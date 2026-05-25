# 🧪 TESTING CHECKLIST - SMADER IoT Service v2.0

## Pre-Testing Setup

- [ ] Clone/pull latest code dari repository
- [ ] Install requirements: `pip install -r requirements.txt`
- [ ] Pastikan kamera tersambung dan berfungsi
- [ ] Backend server berjalan di `http://localhost:3000/api/signals`
- [ ] Configure `.env` dengan setting yang tepat

```bash
URL_SERVER=http://localhost:3000/api/signals
NOMOR_RUANG=102
COOLDOWN_SECONDS=3
SHOW_UI=True
CAMERA_INDEX=0
MAX_QUEUE_SIZE=5
REQUEST_TIMEOUT=5
```

---

## ✅ TEST 1: UI DISPLAY

### Test 1.1: Panel Atas Tampil
- [ ] Jalankan aplikasi: `python3 final.py`
- [ ] Verifikasi panel atas (60px) tampil dengan:
  - [ ] Teks "Status: IDLE"
  - [ ] Teks "Jari: 0 | Kode: 0"
  - [ ] Background warna gelap
  - [ ] Border abu-abu

### Test 1.2: Panel Bawah Tampil
- [ ] Verifikasi panel bawah (160px) tampil dengan:
  - [ ] Teks "Recent Activity:"
  - [ ] Teks "Queue: 0/5"
  - [ ] Background warna gelap
  - [ ] Border abu-abu

### Test 1.3: Hand Landmarks Rendering
- [ ] Tampilkan tangan ke kamera
- [ ] Verifikasi:
  - [ ] Garis hijau menghubungkan joints
  - [ ] Titik merah di setiap joint
  - [ ] Skeleton hand terbentuk dengan benar

---

## ✅ TEST 2: GESTURE DETECTION & KODE

### Test 2.1: 2 Jari Detection
- [ ] Tampilkan gesture 2 jari (peace sign)
- [ ] Verifikasi di panel atas:
  - [ ] "Jari: 2" muncul
  - [ ] "Kode: 1" muncul

### Test 2.2: 3 Jari Detection
- [ ] Tampilkan gesture 3 jari
- [ ] Verifikasi:
  - [ ] "Jari: 3" dan "Kode: 2"

### Test 2.3: 4 Jari Detection
- [ ] Tampilkan gesture 4 jari
- [ ] Verifikasi:
  - [ ] "Jari: 4" dan "Kode: 3"

### Test 2.4: 5 Jari Detection
- [ ] Tampilkan gesture 5 jari (open hand)
- [ ] Verifikasi:
  - [ ] "Jari: 5" dan "Kode: 4"

---

## ✅ TEST 3: STATUS INDICATOR

### Test 3.1: IDLE Status
- [ ] Awalnya status harus "IDLE" (putih)
- [ ] Background normal gelap

### Test 3.2: SENDING Status
- [ ] Tunjukkan gesture ke kamera
- [ ] Verifikasi status berubah ke "SENDING..." (orange)
- [ ] Status berubah cepat (loading indicator)

### Test 3.3: SUCCESS Status
- [ ] Jika server respond 200, status menjadi "SUCCESS ✓"
- [ ] Warna hijau (0, 255, 0)
- [ ] Tetap tampil selama 3 detik
- [ ] Setelah 3 detik, auto-reset ke "IDLE"

### Test 3.4: ERROR/TIMEOUT Status
- [ ] Matikan server backend
- [ ] Tunjukkan gesture
- [ ] Verifikasi status menjadi "TIMEOUT ✗" atau "ERROR ✗"
- [ ] Warna merah (0, 0, 255)
- [ ] Auto-reset ke IDLE setelah 3 detik

---

## ✅ TEST 4: HISTORY LOGGING

### Test 4.1: History Entry
- [ ] Tunjukkan gesture
- [ ] Verifikasi di panel bawah muncul entry baru:
  - [ ] `[HH:MM:SS] Kode:X Jari:Y | STATUS`
  - [ ] Timestamp format benar

### Test 4.2: History Accumulation
- [ ] Tunjukkan gesture 5 kali berbeda
- [ ] Verifikasi panel bawah menampilkan 5 entry terakhir
- [ ] Entry tertua masih terlihat (tidak hilang)

### Test 4.3: History Max Limit
- [ ] Tunjukkan gesture 20+ kali
- [ ] Verifikasi:
  - [ ] Hanya 15 entry tersimpan (max_history)
  - [ ] Entry terlama dihapus otomatis
  - [ ] Panel tetap menampilkan 5 terbaru

### Test 4.4: Status dalam History
- [ ] Verifikasi berbagai status tercatat:
  - [ ] "QUEUED" - request masuk queue
  - [ ] "SENT" - berhasil dikirim
  - [ ] "FAILED (XXX)" - gagal dengan status code
  - [ ] "TIMEOUT" - timeout
  - [ ] "ERROR" - error koneksi
  - [ ] "QUEUE FULL" - queue penuh

---

## ✅ TEST 5: QUEUE MANAGEMENT

### Test 5.1: Queue Counter
- [ ] Lihat teks "Queue: X/5" di panel bawah
- [ ] Awalnya "Queue: 0/5"
- [ ] Saat ada request pending, nilai naik (0→1→2...)

### Test 5.2: Queue Not Full
- [ ] Tunjukkan gesture dengan cepat 3 kali
- [ ] Verifikasi:
  - [ ] Semua berhasil masuk queue
  - [ ] Queue: 0-3 terlihat
  - [ ] "Queue: X/5" warna hijau

### Test 5.3: Queue Full Protection
- [ ] Matikan server backend
- [ ] Tunjukkan gesture dengan sangat cepat 10+ kali
- [ ] Verifikasi:
  - [ ] Queue tidak melebihi 5 (tidak melampaui MAX_QUEUE_SIZE)
  - [ ] "Queue: 5/5" warna merah (warning)
  - [ ] Gesture ke-6+ ditolak (tidak langsung kirim)

### Test 5.4: Queue Processing
- [ ] Nyalakan kembali server
- [ ] Verifikasi queue secara otomatis berkurang (0→1→0)
- [ ] Request diproses satu per satu

---

## ✅ TEST 6: COOLDOWN & RATE LIMITING

### Test 6.1: Same Gesture Cooldown
- [ ] Tunjukkan gesture 2 jari (Kode: 1)
- [ ] Tunggu 1 detik
- [ ] Tunjukkan gesture 2 jari lagi
- [ ] Verifikasi:
  - [ ] Request pertama: SENT ✓
  - [ ] Request kedua (dalam 3 detik): ditolak (tidak ada entry baru di history)

### Test 6.2: Different Gesture
- [ ] Tunjukkan gesture 2 jari (Kode: 1)
- [ ] Langsung tunjukkan gesture 3 jari (Kode: 2)
- [ ] Verifikasi:
  - [ ] Kedua request dikirim (berbeda kode)
  - [ ] Tidak menunggu cooldown

### Test 6.3: Cooldown Timer
- [ ] Tunjukkan gesture 2 jari
- [ ] Tunggu 3+ detik
- [ ] Tunjukkan gesture 2 jari lagi
- [ ] Verifikasi:
  - [ ] Kedua request dikirim (cooldown sudah habis)

---

## ✅ TEST 7: TIMEOUT HANDLING

### Test 7.1: Normal Timeout (Backend Slow)
- [ ] Modifikasi backend untuk response lambat (>5 detik)
- [ ] Tunjukkan gesture
- [ ] Verifikasi:
  - [ ] Status: "SENDING..." muncul
  - [ ] Setelah 5 detik: "TIMEOUT ✗"
  - [ ] History: "TIMEOUT" tercatat

### Test 7.2: Backend Down
- [ ] Matikan backend server
- [ ] Tunjukkan gesture
- [ ] Verifikasi:
  - [ ] Status: "SENDING..." → "ERROR ✗"
  - [ ] History: "ERROR" atau "TIMEOUT"

### Test 7.3: Connection Refused
- [ ] Set URL ke port yang tidak aktif (e.g., 9999)
- [ ] Tunjukkan gesture
- [ ] Verifikasi:
  - [ ] Status: "ERROR ✗"
  - [ ] Terminal: "[ERROR-NET] Gagal mengirim data"

---

## ✅ TEST 8: THREAD SAFETY

### Test 8.1: Non-Blocking Network
- [ ] Jalankan aplikasi dengan server yang lambat
- [ ] Tunjukkan gesture
- [ ] Verifikasi:
  - [ ] UI tetap responsif (tidak freeze)
  - [ ] Video tetap smooth (tidak jeda)
  - [ ] Request diproses di background

### Test 8.2: Concurrent Access
- [ ] Tunjukkan gesture dengan cepat
- [ ] Verifikasi:
  - [ ] Tidak ada error "racing condition"
  - [ ] History tercatat dengan benar
  - [ ] Status konsisten

### Test 8.3: Multiple Events
- [ ] Tunjukkan 5 gesture berbeda dalam 1 detik
- [ ] Verifikasi:
  - [ ] Semua tercatat di history
  - [ ] Urutan benar
  - [ ] Tidak ada duplikat/data corruption

---

## ✅ TEST 9: CONFIGURATION

### Test 9.1: URL_SERVER
- [ ] Set URL_SERVER ke server lain
- [ ] Verifikasi request dikirim ke URL yang baru

### Test 9.2: COOLDOWN_SECONDS
- [ ] Set COOLDOWN_SECONDS=1
- [ ] Tunjukkan gesture 2 jari 2x dengan jarak 1.5 detik
- [ ] Verifikasi: request kedua berhasil (cooldown hanya 1 detik)

### Test 9.3: MAX_QUEUE_SIZE
- [ ] Set MAX_QUEUE_SIZE=2
- [ ] Tunjukkan gesture 5x dengan cepat
- [ ] Verifikasi: queue tidak melebihi 2

### Test 9.4: REQUEST_TIMEOUT
- [ ] Set REQUEST_TIMEOUT=1
- [ ] Server buat delay 2+ detik
- [ ] Verifikasi: request timeout lebih cepat

### Test 9.5: SHOW_UI
- [ ] Set SHOW_UI=False (headless mode)
- [ ] Tunjukkan gesture
- [ ] Verifikasi:
  - [ ] Tidak ada window video
  - [ ] Request tetap terkirim
  - [ ] Terminal log menampilkan event

---

## ✅ TEST 10: ERROR RECOVERY

### Test 10.1: Temporary Network Loss
- [ ] Start dengan network normal
- [ ] Tunjukkan gesture (SENT ✓)
- [ ] Simulasi network loss
- [ ] Tunjukkan gesture (ERROR ✗)
- [ ] Restore network
- [ ] Tunjukkan gesture (SENT ✓ lagi)

### Test 10.2: Server Restart
- [ ] Backend server mati
- [ ] Tunjukkan gesture (ERROR)
- [ ] Nyalakan ulang server
- [ ] Tunjukkan gesture (SENT ✓)

### Test 10.3: Long Running
- [ ] Jalankan aplikasi selama 10 menit
- [ ] Tunjukkan gesture secara random
- [ ] Verifikasi:
  - [ ] No memory leak
  - [ ] History tidak overflow
  - [ ] UI tetap responsif

---

## ✅ TEST 11: VISUAL ELEMENTS

### Test 11.1: Color Coding
- [ ] Status Success: Warna hijau (0, 255, 0)
- [ ] Status Sending: Warna orange/kuning
- [ ] Status Error: Warna merah (0, 0, 255)
- [ ] Status Idle: Warna putih (200, 200, 200)
- [ ] Queue OK: Warna hijau
- [ ] Queue Full: Warna merah

### Test 11.2: Text Readability
- [ ] Font size cukup besar untuk dibaca
- [ ] Contrast cukup (teks terang, background gelap)
- [ ] Spacing antar element bagus

### Test 11.3: Layout Consistency
- [ ] Panel atas konsisten di semua frame
- [ ] Panel bawah konsisten di semua frame
- [ ] Hand landmarks tidak bergeser-geser

---

## ✅ TEST 12: PERFORMANCE

### Test 12.1: FPS Monitoring
- [ ] Tunjukkan gesture
- [ ] Verifikasi frame rate tetap smooth (30+ FPS)
- [ ] Tidak ada lag/stuttering

### Test 12.2: CPU Usage
- [ ] Monitor CPU usage saat berjalan
- [ ] Headless mode: < 30% CPU
- [ ] UI mode: < 50% CPU

### Test 12.3: Memory Usage
- [ ] Jalankan 30 menit
- [ ] Monitor memory tidak naik terus (bounded)
- [ ] Stabilisasi di ~100-200 MB

---

## ✅ TEST 13: EDGE CASES

### Test 13.1: No Hand Detected
- [ ] Tunjukkan object lain (bukan tangan)
- [ ] Verifikasi:
  - [ ] "Jari: 0" dan "Kode: 0"
  - [ ] Tidak ada request kirim

### Test 13.2: Partial Hand
- [ ] Tunjukkan tangan yang terpotong layar
- [ ] Verifikasi:
  - [ ] Tidak crash
  - [ ] Handle gracefully

### Test 13.3: Multiple Hands
- [ ] Set num_hands=1 (sudah ada)
- [ ] Tunjukkan 2 tangan
- [ ] Verifikasi:
  - [ ] Hanya 1 hand diproses
  - [ ] Gesture detection bekerja normal

### Test 13.4: Rapid Direction Changes
- [ ] Gerakan tangan sangat cepat bolak-balik
- [ ] Verifikasi:
  - [ ] Tidak ada error
  - [ ] Detection tetap akurat

---

## ✅ TEST 14: INTEGRATION

### Test 14.1: With Real Backend
- [ ] Set URL ke backend production
- [ ] Jalankan aplikasi
- [ ] Verifikasi data benar-benar terkirim dan tersimpan

### Test 14.2: With Frontend Dashboard
- [ ] Buka dashboard frontend
- [ ] Tunjukkan gesture
- [ ] Verifikasi data muncul real-time di dashboard

### Test 14.3: Cross-Platform
- [ ] Test di macOS
- [ ] Test di Linux (jika ada)
- [ ] Test di Windows (jika ada)

---

## 📝 TESTING REPORT TEMPLATE

```
┌─────────────────────────────────────────────────────────┐
│ TESTING REPORT - SMADER IoT Service v2.0               │
├─────────────────────────────────────────────────────────┤
│ Tanggal          : [DATE]                               │
│ Tester           : [NAME]                               │
│ Environment      : [macOS/Linux/Windows]               │
│ Backend Status   : [Running/Stopped]                   │
│ Camera           : [Model/Index]                        │
│                                                         │
│ HASIL TESTING:                                         │
│ ✅ UI Display           : PASS / FAIL                   │
│ ✅ Gesture Detection    : PASS / FAIL                   │
│ ✅ Status Indicator     : PASS / FAIL                   │
│ ✅ History Logging      : PASS / FAIL                   │
│ ✅ Queue Management     : PASS / FAIL                   │
│ ✅ Cooldown Protection  : PASS / FAIL                   │
│ ✅ Timeout Handling     : PASS / FAIL                   │
│ ✅ Thread Safety        : PASS / FAIL                   │
│ ✅ Configuration        : PASS / FAIL                   │
│ ✅ Error Recovery       : PASS / FAIL                   │
│ ✅ Visual Elements      : PASS / FAIL                   │
│ ✅ Performance          : PASS / FAIL                   │
│ ✅ Edge Cases           : PASS / FAIL                   │
│ ✅ Integration          : PASS / FAIL                   │
│                                                         │
│ KESIMPULAN: [READY / NEED FIX / BLOCKED]               │
│ CATATAN    : [Any issues found]                        │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 POST-TESTING CHECKLIST

- [ ] Semua test case PASS
- [ ] No critical bugs
- [ ] Performance acceptable
- [ ] Documentation updated
- [ ] Code reviewed
- [ ] Ready for deployment
- [ ] Backup created
- [ ] Version tagged

---

**Last Updated:** May 25, 2026  
**Test Environment:** macOS  
**Status:** Ready for Execution
