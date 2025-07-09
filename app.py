from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'rahasia123beb'

# -----------------------------
# Fungsi koneksi ke database
# -----------------------------
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# -----------------------------
# Halaman Utama (Pengunjung Ambil Antrian)
# -----------------------------
@app.route('/', methods=['GET', 'POST'])
def index():
    conn = get_db_connection()

    if request.method == 'POST':
        nama = request.form['nama']
        no_hp = request.form['no_hp']
        loket_id = request.form['loket_id']

        # Ambil kuota dari tabel loket
        loket = conn.execute("SELECT * FROM loket WHERE id = ?", (loket_id,)).fetchone()
        if not loket:
            flash('Loket tidak ditemukan.')
            conn.close()
            return redirect(url_for('index'))

        kuota_maks = loket['kuota_harian']

        jumlah_hari_ini = conn.execute("""
            SELECT COUNT(*) FROM antrian 
            WHERE loket_id = ? 
            AND DATE(waktu_masuk) = DATE('now', 'localtime')
        """, (loket_id,)).fetchone()[0]

        if jumlah_hari_ini >= kuota_maks:
            flash(f"⚠️ Kuota untuk {loket['nama']} hari ini sudah penuh.")
            conn.close()
            return redirect(url_for('index'))

        # Ambil nomor terakhir HANYA untuk hari ini
        last_nomor = conn.execute("""
            SELECT MAX(nomor) FROM antrian 
            WHERE loket_id = ? AND DATE(waktu_masuk) = DATE('now', 'localtime')
        """, (loket_id,)).fetchone()[0]

        nomor_baru = (last_nomor or 0) + 1
        waktu_masuk = datetime.utcnow() + timedelta(hours=7)

        conn.execute("""
            INSERT INTO antrian (nama, no_hp, nomor, loket_id, waktu_masuk)
            VALUES (?, ?, ?, ?, ?)
        """, (nama, no_hp, nomor_baru, loket_id, waktu_masuk.strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
        conn.close()

        return render_template('success.html', nama=nama, nomor=nomor_baru, loket_id=loket_id, no_hp=no_hp)

    # GET: Tampilkan semua loket dan sisa kuota
    loket_rows = conn.execute("SELECT * FROM loket").fetchall()
    loket_list = []

    for row in loket_rows:
        jumlah_terpakai = conn.execute("""
            SELECT COUNT(*) FROM antrian 
            WHERE loket_id = ? 
            AND DATE(waktu_masuk) = DATE('now', 'localtime')
        """, (row['id'],)).fetchone()[0]
        sisa_kuota = max(row['kuota_harian'] - jumlah_terpakai, 0)

        loket_list.append({
            'id': row['id'],
            'nama': row['nama'],
            'kode': row['kode'],
            'sisa_kuota': sisa_kuota
        })

    conn.close()
    return render_template('index.html', loket_list=loket_list)

# -----------------------------
# Cek Status Antrian Pengunjung
# -----------------------------
@app.route('/status')
def status():
    no_hp = request.args.get('hp')
    conn = get_db_connection()

    antrian = conn.execute("""
        SELECT a.*, l.nama AS nama_loket, l.kode AS kode_loket
        FROM antrian a
        JOIN loket l ON a.loket_id = l.id
        WHERE a.no_hp = ?
        ORDER BY a.waktu_masuk DESC
        LIMIT 1
    """, (no_hp,)).fetchone()

    display = None
    sisa = 0

    if antrian:
        display = conn.execute("""
            SELECT MAX(nomor) AS nomor FROM antrian
            WHERE loket_id = ? AND status = 'dipanggil'
        """, (antrian['loket_id'],)).fetchone()

        sisa = conn.execute("""
            SELECT COUNT(*) AS total FROM antrian
            WHERE loket_id = ? AND status = 'menunggu' AND nomor < ?
        """, (antrian['loket_id'], antrian['nomor'])).fetchone()['total']

    conn.close()
    return render_template("status.html", antrian=antrian, display=display, sisa=sisa)

# -----------------------------
# Display Umum
# -----------------------------
@app.route('/display')
def display():
    conn = get_db_connection()
    loket_list = conn.execute("""
        SELECT l.id, l.nama, l.kode,
        (SELECT nomor FROM antrian 
         WHERE status = 'dipanggil' AND loket_id = l.id 
         ORDER BY waktu_masuk DESC LIMIT 1) AS nomor
        FROM loket l
    """).fetchall()
    conn.close()
    return render_template('display.html', loket_list=loket_list)

# -----------------------------
# Login
# -----------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute("""
            SELECT * FROM users WHERE username = ? AND password = ?
        """, (username, password)).fetchone()
        conn.close()

        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            session['loket_id'] = user['loket_id']

            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('dashboard'))
        else:
            flash('Username atau password salah')

    return render_template('login.html')

# -----------------------------
# Dashboard Admin
# -----------------------------
@app.route('/admin/dashboard')
def admin_dashboard():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))

    conn = get_db_connection()

    loket_data = conn.execute("SELECT * FROM loket").fetchall()
    total_antrian = conn.execute("SELECT COUNT(*) FROM antrian").fetchone()[0]
    total_menunggu = conn.execute("SELECT COUNT(*) FROM antrian WHERE status = 'menunggu'").fetchone()[0]
    total_dipanggil = conn.execute("SELECT COUNT(*) FROM antrian WHERE status = 'dipanggil'").fetchone()[0]
    total_selesai = conn.execute("SELECT COUNT(*) FROM antrian WHERE status = 'selesai'").fetchone()[0]

    conn.close()

    return render_template('admin_dashboard.html',
                           loket_data=loket_data,
                           total_antrian=total_antrian,
                           total_menunggu=total_menunggu,
                           total_dipanggil=total_dipanggil,
                           total_selesai=total_selesai)
    
    
# -----------------------------
# Histori & Monitoring Antrian (Admin)
# -----------------------------
@app.route('/admin/histori', methods=['GET', 'POST'])
def admin_histori():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))

    conn = get_db_connection()

    # Ambil semua loket untuk pilihan filter
    loket_list = conn.execute("SELECT * FROM loket").fetchall()

    query = """
        SELECT a.*, l.nama AS nama_loket, l.kode AS kode_loket
        FROM antrian a
        JOIN loket l ON a.loket_id = l.id
        WHERE 1=1
    """
    params = []

    # Ambil data filter dari form
    selected_loket = request.args.get('loket_id')
    selected_status = request.args.get('status')
    selected_tanggal = request.args.get('tanggal')

    if selected_loket and selected_loket != 'all':
        query += " AND a.loket_id = ?"
        params.append(selected_loket)

    if selected_status and selected_status != 'all':
        query += " AND a.status = ?"
        params.append(selected_status)

    if selected_tanggal:
        query += " AND DATE(a.waktu_masuk) = ?"
        params.append(selected_tanggal)

    query += " ORDER BY a.waktu_masuk DESC"

    antrian_list = conn.execute(query, params).fetchall()
    conn.close()

    return render_template("admin_histori.html",
                           antrian_list=antrian_list,
                           loket_list=loket_list,
                           selected_loket=selected_loket,
                           selected_status=selected_status,
                           selected_tanggal=selected_tanggal)


from openpyxl import Workbook
from flask import send_file
import io

@app.route('/admin/histori/export')
def export_histori_excel():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))

    conn = get_db_connection()

    query = """
        SELECT a.*, l.nama AS nama_loket, l.kode AS kode_loket
        FROM antrian a
        JOIN loket l ON a.loket_id = l.id
        WHERE 1=1
    """
    params = []

    selected_loket = request.args.get('loket_id')
    selected_status = request.args.get('status')
    selected_tanggal = request.args.get('tanggal')

    if selected_loket and selected_loket != 'all':
        query += " AND a.loket_id = ?"
        params.append(selected_loket)

    if selected_status and selected_status != 'all':
        query += " AND a.status = ?"
        params.append(selected_status)

    if selected_tanggal:
        query += " AND DATE(a.waktu_masuk) = ?"
        params.append(selected_tanggal)

    query += " ORDER BY a.waktu_masuk DESC"
    data = conn.execute(query, params).fetchall()
    conn.close()

    # Buat file Excel
    wb = Workbook()
    ws = wb.active
    ws.title = "Histori Antrian"

    # Header
    ws.append(["No", "Nama", "HP", "Loket", "Kode", "Nomor", "Status", "Waktu Masuk"])

    # Data
    for i, row in enumerate(data, start=1):
        ws.append([
            i,
            row['nama'],
            row['no_hp'],
            row['nama_loket'],
            row['kode_loket'],
            row['nomor'],
            row['status'],
            row['waktu_masuk']
        ])

    # Simpan ke stream
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    filename = f"histori_antrian.xlsx"
    return send_file(output, download_name=filename, as_attachment=True, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    

    
# -----------------------------
# Manajemen Petugas (Admin)
# -----------------------------
@app.route('/admin/petugas')
def admin_petugas():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))

    conn = get_db_connection()
    petugas = conn.execute("""
        SELECT u.*, l.nama AS nama_loket FROM users u
        LEFT JOIN loket l ON u.loket_id = l.id
        WHERE u.role = 'petugas'
    """).fetchall()
    conn.close()
    return render_template('admin_petugas.html', petugas=petugas)


@app.route('/admin/petugas/tambah', methods=['GET', 'POST'])
def tambah_petugas():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))

    conn = get_db_connection()
    loket_list = conn.execute("SELECT * FROM loket").fetchall()

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        loket_id = request.form['loket_id']

        conn.execute("""
            INSERT INTO users (username, password, role, loket_id)
            VALUES (?, ?, 'petugas', ?)
        """, (username, password, loket_id))
        conn.commit()
        conn.close()
        return redirect(url_for('admin_petugas'))

    conn.close()
    return render_template('tambah_petugas.html', loket_list=loket_list)


@app.route('/admin/petugas/edit/<int:id>', methods=['GET', 'POST'])
def edit_petugas(id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))

    conn = get_db_connection()
    petugas = conn.execute("SELECT * FROM users WHERE id = ?", (id,)).fetchone()
    loket_list = conn.execute("SELECT * FROM loket").fetchall()

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        loket_id = request.form['loket_id']

        conn.execute("""
            UPDATE users SET username = ?, password = ?, loket_id = ?
            WHERE id = ?
        """, (username, password, loket_id, id))
        conn.commit()
        conn.close()
        return redirect(url_for('admin_petugas'))

    conn.close()
    return render_template('edit_petugas.html', petugas=petugas, loket_list=loket_list)


@app.route('/admin/petugas/hapus/<int:id>', methods=['POST'])
def hapus_petugas(id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))

    conn = get_db_connection()
    conn.execute("DELETE FROM users WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_petugas'))

    

# -----------------------------
# Manajemen Loket (Admin)
# -----------------------------
@app.route('/admin/loket')
def admin_loket():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))

    conn = get_db_connection()
    loket_list = conn.execute("SELECT * FROM loket").fetchall()
    conn.close()
    return render_template('admin_loket.html', loket_list=loket_list)

@app.route('/admin/loket/tambah', methods=['GET', 'POST'])
def tambah_loket():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))

    if request.method == 'POST':
        nama = request.form['nama']
        kode = request.form['kode']
        kuota = int(request.form['kuota'])

        conn = get_db_connection()
        conn.execute("INSERT INTO loket (nama, kode, kuota_harian) VALUES (?, ?, ?)",
                     (nama, kode.upper(), kuota))
        conn.commit()
        conn.close()
        return redirect(url_for('admin_loket'))

    return render_template('tambah_loket.html')

@app.route('/admin/loket/edit/<int:id>', methods=['GET', 'POST'])
def edit_loket(id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))

    conn = get_db_connection()
    loket = conn.execute("SELECT * FROM loket WHERE id = ?", (id,)).fetchone()

    if request.method == 'POST':
        nama = request.form['nama']
        kode = request.form['kode']
        kuota = int(request.form['kuota'])

        conn.execute("UPDATE loket SET nama = ?, kode = ?, kuota_harian = ? WHERE id = ?",
                     (nama, kode.upper(), kuota, id))
        conn.commit()
        conn.close()
        return redirect(url_for('admin_loket'))

    conn.close()
    return render_template('edit_loket.html', loket=loket)

@app.route('/admin/loket/hapus/<int:id>', methods=['POST'])
def hapus_loket(id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))

    conn = get_db_connection()
    conn.execute("DELETE FROM loket WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_loket'))


# -----------------------------
# Dashboard Petugas
# -----------------------------
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session or session.get('role') != 'petugas':
        return redirect(url_for('login'))

    conn = get_db_connection()
    loket_id = session['loket_id']

    antrian = conn.execute("""
        SELECT a.*, l.kode AS kode_loket, l.id AS loket_id
        FROM antrian a
        JOIN loket l ON a.loket_id = l.id
        WHERE a.loket_id = ? AND a.status IN ('menunggu', 'dipanggil')
        ORDER BY a.waktu_masuk ASC
    """, (loket_id,)).fetchall()

    jumlah_dipanggil = conn.execute("""
        SELECT COUNT(*) FROM antrian
        WHERE loket_id = ? AND status = 'dipanggil'
    """, (loket_id,)).fetchone()[0]

    jumlah_menunggu = conn.execute("""
        SELECT COUNT(*) FROM antrian
        WHERE loket_id = ? AND status = 'menunggu'
    """, (loket_id,)).fetchone()[0]

    conn.close()

    return render_template('dashboard.html',
                           antrian=antrian,
                           jumlah_dipanggil=jumlah_dipanggil,
                           jumlah_menunggu=jumlah_menunggu)

# -----------------------------
# Panggil Antrian
# -----------------------------
@app.route('/panggil/<int:antrian_id>', methods=['POST'])
def panggil(antrian_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    conn.execute("UPDATE antrian SET status = 'dipanggil' WHERE id = ?", (antrian_id,))
    conn.commit()
    conn.close()

    return redirect(url_for('dashboard'))

# -----------------------------
# Selesaikan Antrian
# -----------------------------
@app.route('/selesai/<int:antrian_id>', methods=['POST'])
def selesai(antrian_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    conn.execute("UPDATE antrian SET status = 'selesai' WHERE id = ?", (antrian_id,))
    conn.commit()
    conn.close()

    return redirect(url_for('dashboard'))

# -----------------------------
# Logout
# -----------------------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# -----------------------------
# Jalankan aplikasi
# -----------------------------
if __name__ == '__main__':
    app.run(debug=True)
