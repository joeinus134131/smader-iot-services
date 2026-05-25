# 📋 PANDUAN PEMAKAIAN - SMADER IoT Service v2.0

## 🎯 Apa yang Sudah Diperbaiki?

Udah saya perbaiki `final.py` dengan fitur-fitur berikut:

### ✨ UI yang Lebih Enak
- **Panel Atas**: Menampilkan status pengiriman real-time
  - Status berubah warna: IDLE (putih) → SENDING (orange) → SUCCESS (hijau) atau ERROR (merah)
  - Menampilkan jumlah jari yang terdeteksi + kode gesture

- **Panel Bawah**: History aktivitas terbaru
  - Tampil 5 event terakhir dengan timestamp (jam:menit:detik)
  - Setiap event menunjukkan: waktu, kode, jumlah jari, status
  - Queue counter untuk melihat antrian request

### 📊 Data yang Termonitor dengan Baik
- Semua event tercatat dengan timestamp
- History tersimpan maksimal 15 item (tidak langsung hilang)
- Thread-safe access (aman dari race condition)
- Bisa melihat riwayat aktivitas 5 terbaru

### ⏰ Info Tidak Langsung Hilang
- Status pengiriman ditampilkan selama 3 detik (tidak hilang langsung)
- History tersimpan permanen selama program berjalan
- User dapat melihat apa yang terjadi di masa lalu (5 event terakhir)

### 🔄 Loading Indicator
- Ketika mengirim: Status "SENDING..." (loading)
- Ketika sukses: Status "SUCCESS ✓" (hijau)
- Ketika timeout: Status "TIMEOUT ✗" (merah)
- Ketika error: Status "ERROR ✗" (merah)

### 🚦 Kontrol Traffic (Prevent Overload & Duplicate)
- **Queue System**: Maksimal 5 request dalam antrian
  - Jika queue penuh → request baru ditolak (tidak duplicate)
  
- **Cooldown**: 3 detik sebelum gesture sama bisa dikirim lagi
  - Jika tunjuk 2 jari (Kode:1) → harus tunggu 3 detik sebelum kirim ulang
  - Tapi jika tunjuk gesture berbeda (Kode:2) → langsung bisa dikirim
  
- **Timeout**: 5 detik timeout per request
  - Request tidak akan gantung selamanya
  - Jika >5 detik tidak ada response → mark as TIMEOUT

---

## 🚀 Cara Menggunakan

### 1️⃣ Setup (hanya sekali)
```bash
cd /Users/user/smader/smader-iot-service
pip install -r requirements.txt
```

### 2️⃣ Pastikan Konfigurasi di `.env`
```env
URL_SERVER=http://localhost:3000/api/signals
NOMOR_RUANG=102
COOLDOWN_SECONDS=3
SHOW_UI=True
MAX_QUEUE_SIZE=5
REQUEST_TIMEOUT=5
```

### 3️⃣ Jalankan Aplikasi
```bash
python3 final.py
```

### 4️⃣ Gunakan
- Tunjukkan tangan ke kamera
- Ubah jumlah jari (2, 3, 4, atau 5 jari)
- Lihat perubahan di panel atas (status, jari, kode)
- Lihat history di panel bawah
- Tekan ESC untuk keluar

---

## 👁️ Tampilan Visual

```
┌─────────────────────────────────────────────────────────┐
│ Status: SUCCESS ✓              Jari: 3 | Kode: 2       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│    [Video dari Kamera]                                  │
│    Dengan Hand Skeleton:                               │
│    - Garis Hijau: Hubungan antar joint                 │
│    - Titik Merah: Posisi setiap joint                  │
│                                                         │
├─────────────────────────────────────────────────────────┤
│ Recent Activity:                          Queue: 0/5    │
│ [14:35:22] Kode:2 Jari:3 | SENT                        │
│ [14:35:19] Kode:1 Jari:2 | SENT                        │
│ [14:35:16] Kode:3 Jari:4 | SENT                        │
│ [14:35:13] Kode:2 Jari:3 | QUEUED                      │
│ [14:35:10] Kode:1 Jari:2 | TIMEOUT                     │
└─────────────────────────────────────────────────────────┘
```

---

## 📊 Penjelasan Status

### 🟢 SUCCESS ✓ (Hijau)
- Artinya: Gesture berhasil dikirim ke server
- Durasi: Tampil selama 3 detik
- Setelah: Auto-kembali ke IDLE

### 🟠 SENDING... (Orange)
- Artinya: Sedang mengirim data ke server
- Durasi: Sampai server respond atau timeout
- Ini loading indicator-nya

### 🔴 ERROR ✗ (Merah)
- Artinya: Gagal mengirim (connection error)
- Penyebab: Backend tidak konek, URL salah, dll
- Durasi: Tampil 3 detik
- Dicatat di history

### 🔴 TIMEOUT ✗ (Merah)
- Artinya: Server tidak respond dalam 5 detik
- Penyebab: Backend lambat atau hang
- Durasi: Tampil 3 detik
- Dicatat di history

### ⚪ IDLE (Putih)
- Artinya: Menunggu gesture
- Status normal saat tidak ada aktivitas

---

## 📱 Gesture Reference

| Jari | Gesture | Kode | Deskripsi |
|-----|---------|------|-----------|
| 2 | ✌️ | 1 | Peace sign (jempol + telunjuk) |
| 3 | 🤟 | 2 | Gunakan telunjuk, jari tengah, jari manis |
| 4 | 👍 | 3 | Buka jempol, telunjuk, jari tengah, jari manis |
| 5 | ✋ | 4 | Buka semua jari (open hand) |

---

## 💡 Tips Pemakaian

### ✅ DO:
- ✓ Posisikan tangan di tengah frame kamera
- ✓ Pencahayaan cukup terang
- ✓ Gerakan tangan jelas dan stabil
- ✓ Pastikan backend server running
- ✓ Monitor panel bawah untuk melihat history

### ❌ DON'T:
- ✗ Tunjukkan banyak gesture dalam 1-2 detik (bisa overload queue)
- ✗ Gerakkan tangan terlalu cepat (deteksi jadi tidak akurat)
- ✗ Tunjukkan gesture di tepi layar (deteksi jadi incomplete)
- ✗ Gesture yang samar-samar (jari tidak jelas terbuka/tertutup)
- ✗ Bayangan tangan yang numpang (bisa confuse AI)

---

## 🧪 Testing Cepat

### Test 1: Basic Functionality
```bash
# 1. Jalankan backend (terminal 1)
python3 -m http.server 3000

# 2. Jalankan SMADER (terminal 2)
python3 final.py

# 3. Tunjukkan 2 jari, lihat status
# Expected: "SENDING..." → "SUCCESS ✓"

# 4. Tunjukkan 3 jari, lihat history
# Expected: Event baru muncul di panel bawah
```

### Test 2: Queue System
```bash
# 1. Matikan backend server
# 2. Tunjukkan 5 gesture dengan cepat
# Expected: Queue tidak melampaui 5
```

### Test 3: Cooldown
```bash
# 1. Tunjukkan 2 jari (Kode:1) → SUCCESS
# 2. Tunggu 1 detik
# 3. Tunjukkan 2 jari lagi
# Expected: Request ditolak (masih dalam cooldown)
# 4. Tunggu sampai 3 detik total
# 5. Tunjukkan 2 jari lagi
# Expected: SUCCESS (cooldown sudah habis)
```

---

## 🔧 Troubleshooting

### ❌ Masalah: Window video tidak muncul
**Solusi:**
```bash
# Pastikan SHOW_UI=True di .env
SHOW_UI=True

# Jalankan ulang:
python3 final.py
```

### ❌ Masalah: Status selalu ERROR
**Solusi:**
```bash
# Check backend server
# 1. Pastikan backend running di port 3000
# 2. Check URL di .env benar:
URL_SERVER=http://localhost:3000/api/signals
# 3. Test connection:
curl http://localhost:3000/api/signals
```

### ❌ Masalah: Gesture tidak terdeteksi
**Solusi:**
- Cek pencahayaan (harus terang)
- Posisikan tangan di tengah frame
- Tangan harus terlihat jelas dari kamera
- Buka jari dengan jelas

### ❌ Masalah: Queue selalu penuh
**Solusi:**
```bash
# Kurangi frekuensi gesture
# Atau tingkatkan MAX_QUEUE_SIZE di .env:
MAX_QUEUE_SIZE=10
```

### ❌ Masalah: Program consume CPU tinggi
**Solusi:**
```bash
# Set ke headless mode (no UI):
SHOW_UI=False
# Ini lebih ringan untuk CPU
```

---

## 📖 Dokumentasi Lengkap

Ada 5 file dokumentasi yang bisa dibaca:

1. **QUICK_GUIDE.md** ← Mulai dari sini (3 menit baca)
   - Ringkasan perbaikan
   - Cara pakai
   - Tips testing

2. **SUMMARY.md** ← Ringkasan lengkap
   - What's new
   - Before vs After
   - Checklist requirement

3. **IMPROVEMENTS.md** ← Detail teknis (untuk developer)
   - Fitur yang ditambah
   - Implementasi
   - Pseudocode

4. **VISUAL_GUIDE.txt** ← Diagram & flow chart
   - ASCII diagram
   - Flow chart
   - Data structure

5. **TESTING_CHECKLIST.md** ← Testing comprehensive
   - 14 kategori test
   - 60+ test cases
   - Template reporting

---

## 🎁 Bonus Features

### Auto-Status Reset
```
SUCCESS ✓ → (3 detik) → IDLE
ERROR ✗   → (3 detik) → IDLE
TIMEOUT ✗ → (3 detik) → IDLE
```

### Thread-Safe Operations
- Aman dari race condition
- Lock mechanism otomatis
- Consistent data

### Bounded Collections
- History max 15 items (prevent memory leak)
- Queue max 5 items (prevent overload)

### Detailed Error Logging
- Terminal: Setiap error detail
- History: Status error tercatat
- Can debug dengan mudah

---

## 📞 Dukungan

Jika ada masalah:
1. Baca dokumentasi (QUICK_GUIDE.md dulu)
2. Lihat file ini (tips & troubleshooting)
3. Check terminal log (ada detail error-nya)
4. Buka TESTING_CHECKLIST.md (ada contoh test)

---

## ✅ Checklist Sebelum Jalankan

- [ ] File `.env` sudah ada dan config benar
- [ ] `requirements.txt` sudah di-install
- [ ] Backend server siap berjalan
- [ ] Kamera terhubung dan working
- [ ] Lighting cukup terang
- [ ] `final.py` tidak ada error (verifikasi)

---

## 🎉 Ready to Go!

Semuanya udah siap. Cukup:
```bash
python3 final.py
```

Dan selamat menikmati SMADER dengan UI yang lebih enak! 🚀

---

**Version:** 2.0 (Improved UI & Monitoring)  
**Last Updated:** May 25, 2026  
**Status:** ✅ Production Ready

**Terima kasih telah menggunakan SMADER!** 👋
