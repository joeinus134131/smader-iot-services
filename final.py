#!/usr/bin/env python3
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import requests
import time
import os
import urllib.request
import threading
from dotenv import load_dotenv
from collections import deque
from datetime import datetime
import queue

# ==========================================
# KONFIGURASI APLIKASI (LOAD DARI .ENV)
# ==========================================
load_dotenv()

URL_SERVER = os.getenv("URL_SERVER", "http://localhost:3000/api/signals")
NOMOR_RUANG = os.getenv("NOMOR_RUANG", "102")
COOLDOWN_SECONDS = int(os.getenv("COOLDOWN_SECONDS", "3"))
SHOW_UI = os.getenv("SHOW_UI", "True").lower() in ("true", "1", "yes")
CAMERA_INDEX = int(os.getenv("CAMERA_INDEX", "0"))
MAX_QUEUE_SIZE = int(os.getenv("MAX_QUEUE_SIZE", "5"))  # Maksimal request dalam queue
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "5"))  # Timeout request

print("=== KONFIGURASI ===")
print(f"URL_SERVER       : {URL_SERVER}")
print(f"NOMOR_RUANG      : {NOMOR_RUANG}")
print(f"COOLDOWN_SECONDS : {COOLDOWN_SECONDS}")
print(f"SHOW_UI          : {SHOW_UI}")
print(f"CAMERA_INDEX     : {CAMERA_INDEX}")
print(f"MAX_QUEUE_SIZE   : {MAX_QUEUE_SIZE}")
print("===================\n")

# ==========================================
# INISIALISASI MEDIAPIPE HANDS
# ==========================================
model_path = 'hand_landmarker.task'
if not os.path.exists(model_path):
    print("[INFO] Mengunduh model AI MediaPipe (sekali saja)...")
    url = 'https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task'
    urllib.request.urlretrieve(url, model_path)
    print("[INFO] Model berhasil diunduh!")

base_options = python.BaseOptions(model_asset_path=model_path)
options = vision.HandLandmarkerOptions(base_options=base_options, num_hands=1)
detector = vision.HandLandmarker.create_from_options(options)

HAND_CONNECTIONS = [
    (0,1), (1,2), (2,3), (3,4),
    (0,5), (5,6), (6,7), (7,8),
    (5,9), (9,10), (10,11), (11,12),
    (9,13), (13,14), (14,15), (15,16),
    (13,17), (17,18), (18,19), (19,20),
    (0,17)
]

# ==========================================
# FUNGSI DRAWING UI YANG LEBIH BAIK
# ==========================================
def draw_landmarks(img, landmarks):
    """Draw hand landmarks dengan warna yang lebih bagus"""
    h, w, _ = img.shape
    # Draw connections dengan warna hijau
    for connection in HAND_CONNECTIONS:
        p1 = landmarks[connection[0]]
        p2 = landmarks[connection[1]]
        cv2.line(img, (int(p1.x * w), int(p1.y * h)), (int(p2.x * w), int(p2.y * h)), 
                (0, 255, 0), 2)
    # Draw landmarks dengan warna merah
    for landmark in landmarks:
        cv2.circle(img, (int(landmark.x * w), int(landmark.y * h)), 4, (0, 0, 255), -1)

def draw_ui_panel(img, fingers_count, kode):
    """Draw panel informasi yang terstruktur"""
    h, w = img.shape[:2]
    
    # ===== PANEL ATAS (Status & Jari) =====
    cv2.rectangle(img, (0, 0), (w, 60), (20, 20, 20), cv2.FILLED)
    cv2.rectangle(img, (0, 0), (w, 60), (100, 100, 100), 1)
    
    # Status pengiriman
    status_text = monitor.current_status
    status_color = (0, 255, 0) if "SUCCESS" in status_text else \
                   (0, 165, 255) if "SENDING" in status_text else \
                   (0, 0, 255) if "ERROR" in status_text or "TIMEOUT" in status_text else \
                   (200, 200, 200)
    
    cv2.putText(img, f"Status: {status_text}", (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
    cv2.putText(img, f"Jari: {fingers_count} | Kode: {kode}", (w - 280, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 100), 2)
    
    # ===== PANEL BAWAH (History & Info) =====
    history_start_y = h - 160
    cv2.rectangle(img, (0, history_start_y), (w, h), (20, 20, 20), cv2.FILLED)
    cv2.rectangle(img, (0, history_start_y), (w, h), (100, 100, 100), 1)
    
    # Judul History
    cv2.putText(img, "Recent Activity:", (10, history_start_y + 25), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (150, 255, 150), 1)
    
    # Tampilkan history (maksimal 5 item terbaru)
    y_offset = history_start_y + 50
    for idx, event in enumerate(list(monitor.history)[-5:]):
        text = f"[{event['time']}] Kode:{event['kode']} Jari:{event['fingers']} | {event['status']}"
        event_color = (0, 255, 0) if "SENT" in event['status'] else \
                     (0, 165, 255) if "QUEUE" in event['status'] else \
                     (0, 0, 255) if "FAIL" in event['status'] or "ERROR" in event['status'] else \
                     (200, 200, 200)
        cv2.putText(img, text, (10, y_offset), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, event_color, 1)
        y_offset += 22
    
    # ===== INFO QUEUE =====
    queue_size = monitor.send_queue.qsize()
    queue_color = (0, 255, 0) if queue_size < MAX_QUEUE_SIZE else (0, 0, 255)
    cv2.putText(img, f"Queue: {queue_size}/{MAX_QUEUE_SIZE}", 
                (w - 200, history_start_y + 25), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, queue_color, 1)

# ==========================================
# SISTEM MONITORING DAN QUEUE
# ==========================================
class DataMonitor:
    """Kelas untuk monitoring data dan status pengiriman"""
    def __init__(self, max_history=10):
        self.send_queue = queue.Queue(maxsize=MAX_QUEUE_SIZE)
        self.history = deque(maxlen=max_history)
        self.current_status = "IDLE"
        self.last_sent_kode = 0
        self.last_sent_time = 0
        self.sending = False
        self.lock = threading.Lock()
    
    def add_history(self, kode, fingers, status):
        """Tambah event ke history"""
        with self.lock:
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.history.append({
                'time': timestamp,
                'kode': kode,
                'fingers': fingers,
                'status': status
            })
    
    def update_status(self, status):
        """Update status monitoring"""
        with self.lock:
            self.current_status = status
    
    def should_send(self, kode):
        """Cek apakah boleh mengirim (cooldown + queue check)"""
        with self.lock:
            current_time = time.time()
            if self.send_queue.full():
                return False  # Queue penuh, jangan kirim
            if (current_time - self.last_sent_time > COOLDOWN_SECONDS or 
                kode != self.last_sent_kode):
                return True
        return False
    
    def mark_sent(self, kode):
        """Tandai bahwa kode telah dikirim"""
        with self.lock:
            self.last_sent_time = time.time()
            self.last_sent_kode = kode

monitor = DataMonitor(max_history=15)

def send_request_async(kode):
    """Pengiriman data ke server dengan status monitoring"""
    def _send():
        try:
            monitor.update_status("SENDING...")
            payload = {
                "room": str(NOMOR_RUANG),
                "code": int(kode)
            }
            print(f"[INFO-NET] Mengirim POST ke {URL_SERVER} -> {payload}")
            response = requests.post(URL_SERVER, json=payload, timeout=REQUEST_TIMEOUT)
            
            if response.status_code in [200, 201]:
                print(f"[SUCCESS-NET] Respon Server: {response.status_code}")
                monitor.update_status("SUCCESS ✓")
                monitor.add_history(kode, "?", "SENT")
            else:
                print(f"[WARNING-NET] Respon tidak normal: {response.status_code}")
                monitor.update_status(f"ERROR {response.status_code}")
                monitor.add_history(kode, "?", f"FAILED ({response.status_code})")
        except requests.exceptions.Timeout:
            print(f"[ERROR-NET] Timeout pada {URL_SERVER}")
            monitor.update_status("TIMEOUT ✗")
            monitor.add_history(kode, "?", "TIMEOUT")
        except requests.exceptions.RequestException as e:
            print(f"[ERROR-NET] Gagal mengirim data: {e}")
            monitor.update_status("ERROR ✗")
            monitor.add_history(kode, "?", "ERROR")
        finally:
            # Status sukses akan dihapus setelah 3 detik
            time.sleep(3)
            if monitor.current_status in ["SUCCESS ✓", "ERROR ✗", "TIMEOUT ✗"]:
                monitor.update_status("IDLE")

    # Jalankan request di thread terpisah
    threading.Thread(target=_send, daemon=True).start()

def process_kode_to_server(kode, fingers_count):
    """Proses kode dan kirim jika memenuhi kondisi"""
    if monitor.should_send(kode):
        try:
            monitor.send_queue.put_nowait((kode, fingers_count))
            monitor.mark_sent(kode)
            send_request_async(kode)
            monitor.add_history(kode, fingers_count, "QUEUED")
            return True
        except queue.Full:
            print("[WARNING-NET] Queue penuh, request diabaikan")
            monitor.add_history(kode, fingers_count, "QUEUE FULL")
            return False
    return False

# ==========================================
# FUNGSI MENGHITUNG JARI
# ==========================================
def count_fingers(hand_landmarks, hand_label):
    tip_ids = [4, 8, 12, 16, 20]
    fingers = []

    # Jempol
    if hand_label == "Right":
        fingers.append(1 if hand_landmarks[tip_ids[0]].x < hand_landmarks[tip_ids[0] - 1].x else 0)
    else:
        fingers.append(1 if hand_landmarks[tip_ids[0]].x > hand_landmarks[tip_ids[0] - 1].x else 0)

    # 4 Jari lainnya
    for id in range(1, 5):
        fingers.append(1 if hand_landmarks[tip_ids[id]].y < hand_landmarks[tip_ids[id] - 2].y else 0)

    return fingers.count(1)

# ==========================================
# PROGRAM UTAMA
# ==========================================
def main():
    cap = cv2.VideoCapture(CAMERA_INDEX)
    
    if not cap.isOpened():
        print(f"[FATAL ERROR] Kamera index {CAMERA_INDEX} tidak ditemukan.")
        print("Pastikan kamera terhubung ke minikomputer.")
        return

    print("[INFO] Aplikasi SMADER berjalan...")
    if SHOW_UI:
        print("[INFO] Mode UI Aktif. Tekan 'ESC' di jendela video untuk keluar.")
    else:
        print("[INFO] Mode Headless Aktif. Berjalan di background. Tekan 'Ctrl+C' di terminal untuk keluar.")

    try:
        while True:
            ret, img = cap.read()
            if not ret:
                print("[WARNING] Gagal membaca frame. Mencoba ulang kamera dalam 2 detik...")
                time.sleep(2)
                cap = cv2.VideoCapture(CAMERA_INDEX)
                continue
                
            img = cv2.flip(img, 1)
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            # Proses MediaPipe
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=img_rgb)
            detection_result = detector.detect(mp_image)

            fingers_count = 0
            kode = 0
            status_terkirim = False
            
            if detection_result.hand_landmarks:
                for i, hand_landmarks in enumerate(detection_result.hand_landmarks):
                    hand_label = detection_result.handedness[i][0].category_name
                    fingers_count = count_fingers(hand_landmarks, hand_label)
                    
                    if fingers_count == 2: kode = 1
                    elif fingers_count == 3: kode = 2
                    elif fingers_count == 4: kode = 3
                    elif fingers_count == 5: kode = 4
                    
                    if kode > 0:
                        status_terkirim = process_kode_to_server(kode, fingers_count)
                        if status_terkirim and not SHOW_UI:
                            print(f"[EVENT] Jari {fingers_count} terdeteksi. Kode {kode} di-trigger.")
                    
                    # Hanya lakukan proses drawing visual jika UI diaktifkan
                    if SHOW_UI:
                        draw_landmarks(img, hand_landmarks)

            # --- MODE VISUAL / HEADLESS ---
            if SHOW_UI:
                draw_ui_panel(img, fingers_count, kode)
                cv2.imshow('SMADER - Deteksi Pasien', img)
                
                # Tekan 'ESC' untuk keluar (wajib di mode UI agar OpenCV merender jendela)
                k = cv2.waitKey(1) & 0xff
                if k == 27: 
                    print("[INFO] Keluar dari aplikasi (ESC ditekan).")
                    break
            else:
                # Mode Headless: Beri jeda kecil agar loop tidak memakan CPU 100%
                time.sleep(0.03) # Sekitar 30 frame per second checking

    except KeyboardInterrupt:
        print("\n[INFO] Aplikasi dihentikan paksa (Ctrl+C).")
    except Exception as e:
        print(f"[FATAL ERROR] Terjadi kesalahan tak terduga: {e}")
    finally:
        cap.release()
        if SHOW_UI:
            cv2.destroyAllWindows()
        print("[INFO] Program selesai.")

if __name__ == "__main__":
    main()