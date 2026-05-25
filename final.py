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

# ==========================================
# KONFIGURASI APLIKASI (LOAD DARI .ENV)
# ==========================================
load_dotenv()

URL_SERVER = os.getenv("URL_SERVER", "http://localhost:3000/api/signals")
NOMOR_RUANG = os.getenv("NOMOR_RUANG", "102")
COOLDOWN_SECONDS = int(os.getenv("COOLDOWN_SECONDS", "3"))
SHOW_UI = os.getenv("SHOW_UI", "True").lower() in ("true", "1", "yes")
CAMERA_INDEX = int(os.getenv("CAMERA_INDEX", "0"))

print("=== KONFIGURASI ===")
print(f"URL_SERVER   : {URL_SERVER}")
print(f"NOMOR_RUANG  : {NOMOR_RUANG}")
print(f"SHOW_UI      : {SHOW_UI}")
print(f"CAMERA_INDEX : {CAMERA_INDEX}")
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

def draw_landmarks(img, landmarks):
    h, w, _ = img.shape
    for connection in HAND_CONNECTIONS:
        p1 = landmarks[connection[0]]
        p2 = landmarks[connection[1]]
        cv2.line(img, (int(p1.x * w), int(p1.y * h)), (int(p2.x * w), int(p2.y * h)), (0, 255, 0), 2)
    for landmark in landmarks:
        cv2.circle(img, (int(landmark.x * w), int(landmark.y * h)), 4, (0, 0, 255), -1)

# ==========================================
# FUNGSI PENGIRIMAN DATA (BACKGROUND THREAD)
# ==========================================
last_sent_time = 0
last_sent_kode = 0

def send_request_async(kode):
    def _send():
        try:
            payload = {
                "ruang": str(NOMOR_RUANG),
                "kode": int(kode)
            }
            print(f"[INFO-NET] Mengirim POST ke {URL_SERVER} -> {payload}")
            # Menggunakan POST sesuai arsitektur (timeout agar tidak gantung)
            response = requests.post(URL_SERVER, json=payload, timeout=5)
            print(f"[SUCCESS-NET] Respon Server: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"[ERROR-NET] Gagal mengirim data: {e}")

    # Jalankan request di thread terpisah agar kamera tidak freeze
    threading.Thread(target=_send, daemon=True).start()

def process_kode_to_server(kode):
    global last_sent_time, last_sent_kode
    current_time = time.time()
    
    # Mencegah pengiriman berulang-ulang tanpa jeda
    if current_time - last_sent_time > COOLDOWN_SECONDS or kode != last_sent_kode:
        last_sent_time = current_time
        last_sent_kode = kode
        send_request_async(kode)
        return True
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
                        status_terkirim = process_kode_to_server(kode)
                        if status_terkirim and not SHOW_UI:
                            print(f"[EVENT] Jari {fingers_count} terdeteksi. Kode {kode} di-trigger.")
                    
                    # Hanya lakukan proses drawing visual jika UI diaktifkan
                    if SHOW_UI:
                        draw_landmarks(img, hand_landmarks)
                        if status_terkirim:
                            cv2.rectangle(img, (0, 0), (img.shape[1], 50), (0, 200, 0), cv2.FILLED)
                            cv2.putText(img, f"KODE {kode} TERKIRIM!", (20, 35), 
                                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

            # --- MODE VISUAL / HEADLESS ---
            if SHOW_UI:
                cv2.putText(img, f"Jari: {fingers_count} | Kode (Kirim): {kode}", (20, 450), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv2.LINE_AA)
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