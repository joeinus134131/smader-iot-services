# SMADER IoT Service (Smart Patient Movement Detector) 🤖🩺

SMADER IoT Service adalah program berbasis Python yang dirancang untuk dijalankan pada *edge devices* (seperti Raspberry Pi atau Mini PC) di kamar pasien rumah sakit. Program ini menggunakan **Google MediaPipe Tasks API** untuk mendeteksi gestur jari tangan pasien secara *realtime* melalui kamera, dan mengirimkan sinyal bahaya/bantuan ke server pusat (Vercel/Supabase).

---

## 🌟 Fitur Utama
*   **Realtime Hand Tracking**: Mendeteksi jumlah jari yang diangkat oleh pasien menggunakan AI (MediaPipe).
*   **Asynchronous HTTP Request**: Mengirim *trigger* tanpa memblokir/menghentikan antrean *frame* kamera.
*   **Headless Mode (`SHOW_UI=False`)**: Sangat ringan dan tidak memerlukan monitor terhubung, cocok untuk di-*deploy* langsung di *edge device*.
*   **Auto-Reconnect Camera**: Otomatis me-restart deteksi jika koneksi USB kamera sempat terputus.

---

## 🛠️ Persyaratan Sistem (*Prerequisites*)
*   OS: Linux (Raspberry Pi OS / Ubuntu) atau macOS atau Windows.
*   Python 3.9, 3.10, atau 3.11.
*   Webcam/Kamera USB yang terpasang pada alat.

---

## 📦 Instalasi

1. **Clone repositori ini:**
   ```bash
   git clone https://github.com/USERNAME_ANDA/smader-iot-service.git
   cd smader-iot-service
   ```

2. **(Opsional namun disarankan) Buat Virtual Environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install *dependencies* yang dibutuhkan:**
   ```bash
   pip install -r requirements.txt
   ```

---

## ⚙️ Konfigurasi Lingkungan (`.env`)

Salin file contoh konfigurasi dan ubah sesuai kebutuhan alat (misalnya nomor kamar pasien):

```bash
cp .env.example .env
```

Buka file `.env` dan sesuaikan parameter berikut:
*   `URL_SERVER`: URL endpoint Next.js/Vercel (contoh: `http://localhost:3000/api/signals`).
*   `NOMOR_RUANG`: Nomor kamar fisik pasien (contoh: `102`).
*   `SHOW_UI`: Set ke `True` untuk mode *development* (menampilkan visualisasi deteksi jari). Set ke `False` untuk alat *production* yang tidak memiliki layar monitor.
*   `COOLDOWN_SECONDS`: Jeda waktu dalam detik sebelum alat dapat mengirimkan kode yang sama.
*   `CAMERA_INDEX`: Index kamera (biasanya `0` untuk kamera bawaan/USB utama).

---

## 🚀 Menjalankan Aplikasi

Jalankan script utama. Program akan mengunduh model AI `hand_landmarker.task` secara otomatis (hanya pada saat run pertama kali).

```bash
python final.py
```

*Jika Anda mengaktifkan `SHOW_UI=True`, tekan `ESC` pada jendela video untuk keluar.*
*Jika menggunakan mode Headless (`SHOW_UI=False`), tekan `Ctrl+C` pada terminal untuk menghentikan alat.*

---

## 🏗️ Arsitektur Sistem
Informasi lebih lanjut tentang arsitektur dan relasi antara IoT, Web Dashboard, dan Database bisa dibaca pada [architecture_design.md](./architecture_design.md).
