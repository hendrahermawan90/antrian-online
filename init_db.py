import sqlite3

# Buat koneksi
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# --- Buat Tabel Loket ---
cursor.execute('''
CREATE TABLE IF NOT EXISTS loket (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nama TEXT NOT NULL,
    kode TEXT NOT NULL
)
''')

# --- Buat Tabel Antrian ---
cursor.execute('''
CREATE TABLE IF NOT EXISTS antrian (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nama TEXT NOT NULL,
    no_hp TEXT NOT NULL,
    nomor INTEGER NOT NULL,
    loket_id INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'menunggu',
    waktu_masuk DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (loket_id) REFERENCES loket(id)
)
''')

# --- Buat Tabel Users (petugas/admin) ---
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    role TEXT NOT NULL,
    loket_id INTEGER,
    FOREIGN KEY (loket_id) REFERENCES loket(id)
)
''')

# --- Tambah Data Loket (jika kosong) ---
cursor.execute("SELECT COUNT(*) FROM loket")
if cursor.fetchone()[0] == 0:
    cursor.execute("INSERT INTO loket (nama, kode) VALUES ('Loket A', 'A')")
    cursor.execute("INSERT INTO loket (nama, kode) VALUES ('Loket B', 'B')")
    print("Data loket berhasil ditambahkan.")

# --- Tambah Petugas Default (jika belum ada) ---
cursor.execute("SELECT * FROM users WHERE username = 'loket_a'")
if not cursor.fetchone():
    cursor.execute("INSERT INTO users (username, password, role, loket_id) VALUES (?, ?, ?, ?)",
                   ('loket_a', '123', 'petugas', 1))
    cursor.execute("INSERT INTO users (username, password, role, loket_id) VALUES (?, ?, ?, ?)",
                   ('loket_b', '123', 'petugas', 2))
    print("Petugas default ditambahkan.")

# Commit dan tutup koneksi
conn.commit()
conn.close()

print("Database berhasil dibuat.")
