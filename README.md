# 🧾 Aplikasi Antrian Online Multi-Loket Berbasis Flask

Aplikasi ini merupakan sistem antrian online berbasis web yang dirancang untuk mengelola proses pengambilan nomor oleh pengunjung, pemanggilan antrian oleh petugas, serta pemantauan dan manajemen oleh admin. Dibangun menggunakan **Python Flask** dan **SQLite**, sistem ini mendukung **multi-loket** dan **multi-role user** secara real-time dan sinkron.

---

## 🚀 Fitur Utama

- ✅ Pengambilan nomor antrian online oleh pengunjung
- 🔎 Cek status antrian berdasarkan nomor HP
- 📺 Display antrian real-time
- 👨‍💼 Dashboard petugas untuk memanggil dan menyelesaikan antrian
- 🛠️ Dashboard admin untuk manajemen petugas, loket, dan histori
- 📊 Filter & export histori antrian ke Excel
- 🔐 Login multi-role (admin & petugas)

---

## 🏗️ Teknologi yang Digunakan

- Python 3
- Flask
- SQLite
- HTML/CSS + Bootstrap
- Jinja2 (template engine)
- OpenPyXL (untuk ekspor Excel)

---

## 📁 Struktur Direktori

```

├── app.py
├── init\_db.py
├── templates/
│   ├── index.html
│   ├── success.html
│   ├── status.html
│   ├── display.html
│   ├── dashboard.html
│   ├── login.html
│   ├── admin\_dashboard.html
│   ├── admin\_histori.html
│   ├── admin\_loket.html
│   ├── tambah\_loket.html
│   ├── edit\_loket.html
│   ├── admin\_petugas.html
│   ├── tambah\_petugas.html
│   └── edit\_petugas.html
├── static/
│   └── (jika ada CSS/JS tambahan)
├── database.db

````

---

## ⚙️ Instalasi & Menjalankan Proyek

1. **Clone repository ini**
   ```bash
   git clone https://github.com/username/nama-repo-antrian.git
   cd nama-repo-antrian
   ````

2. **Install dependency**

   ```bash
   pip install flask openpyxl
   ```

3. **Inisialisasi database**

   ```bash
   python init_db.py
   ```

4. **Jalankan aplikasi**

   ```bash
   python app.py
   ```

5. **Akses via browser**

   ```
   http://localhost:5000
   ```

---

## 👤 Akun Default

* **Petugas Loket A**
  Username: `loket_a`
  Password: `123`

* **Petugas Loket B**
  Username: `loket_b`
  Password: `123`

> **Catatan:** Admin dapat ditambahkan langsung melalui database (`users` table) menggunakan SQLite viewer.

---

## 🧠 Konsep Sistem Terdistribusi

Sistem ini dibangun dengan arsitektur **client-server** yang mendukung prinsip dasar sistem terdistribusi:

* Pengunjung, petugas, dan admin mengakses sistem melalui UI masing-masing dari perangkat berbeda
* Seluruh proses backend dikendalikan oleh satu server Flask yang bertindak sebagai pusat koordinasi
* Status antrian disinkronkan secara real-time antara petugas, pengunjung, dan layar display
* Sistem ini scalable untuk kebutuhan multi-user dan siap dikembangkan ke infrastruktur cloud

---

## 📄 Lisensi

Proyek ini bersifat open-source dan bebas digunakan untuk tujuan pembelajaran, penelitian, atau pengembangan lebih lanjut.

---


