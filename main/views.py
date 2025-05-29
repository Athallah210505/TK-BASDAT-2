from django.shortcuts import render
from django.db import connection
from utils.decorators import role_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection
from datetime import date
from datetime import date, datetime

# Create your views here.
def show_main(request):
    return render(request, 'main.html')


@role_required('staff')
def show_staff_dashboard(request):
    if 'username' not in request.session:
        messages.error(request, "Silakan login terlebih dahulu.")
        return redirect('login')
    
    username = request.session['username']
    today = date.today()
    
    # Harga tiket per unit
    HARGA_TIKET = 20000

    try:
        with connection.cursor() as cursor:
            # Ambil data staff
            cursor.execute("""
                SELECT p.username, p.email, p.nama_depan, p.nama_tengah, p.nama_belakang, 
                       p.no_telepon
                FROM sizopi.pengguna p
                JOIN sizopi.staf_admin sa ON p.username = sa.username_sa
                WHERE p.username = %s
            """, [username])
            user_data = cursor.fetchone()
            if not user_data:
                messages.error(request, "Data staff tidak ditemukan.")
                return redirect('login')

            # Total tiket terjual (semua data)
            cursor.execute("""
                SELECT COUNT(*) as total_tiket
                FROM sizopi.reservasi
                WHERE status != 'Dibatalkan'
            """)
            tiket_total = cursor.fetchone()[0] or 0

            # Total pengunjung (sama dengan tiket terjual)
            pengunjung_total = tiket_total

            # Pendapatan total
            pendapatan_total = tiket_total * HARGA_TIKET

            # Rata-rata pendapatan per hari
            # Hitung jumlah hari unik dalam data reservasi
            cursor.execute("""
                SELECT COUNT(DISTINCT tanggal_kunjungan) as jumlah_hari
                FROM sizopi.reservasi
                WHERE status != 'Dibatalkan'
            """)
            jumlah_hari = cursor.fetchone()[0] or 1  # minimal 1 untuk menghindari pembagian dengan 0
            rata_rata_pendapatan = (pendapatan_total / jumlah_hari)

            # Penjualan tiket berdasarkan jenis fasilitas (semua data)
            cursor.execute("""
                SELECT nama_fasilitas, COUNT(*) as jumlah
                FROM sizopi.reservasi
                WHERE status != 'Dibatalkan'
                GROUP BY nama_fasilitas
                ORDER BY jumlah DESC
                LIMIT 5
            """)
            penjualan_tiket_raw = cursor.fetchall()
            
            # Tambahkan pendapatan untuk setiap jenis tiket
            penjualan_tiket = []
            for item in penjualan_tiket_raw:
                penjualan_tiket.append((
                    item[0],                 # nama_fasilitas
                    item[1],                 # jumlah tiket
                    item[1] * HARGA_TIKET    # pendapatan
                ))

            # Atraksi terpopuler (semua data)
            cursor.execute("""
                SELECT r.nama_fasilitas, COUNT(*) as total_tiket
                FROM sizopi.reservasi r
                WHERE r.status != 'Dibatalkan'
                GROUP BY r.nama_fasilitas
                ORDER BY total_tiket DESC
                LIMIT 5
            """)
            atraksi_populer = cursor.fetchall()

            # Hitung persentase untuk atraksi populer
            total_tiket_atraksi = sum([a[1] for a in atraksi_populer])
            atraksi_dengan_persentase = []
            for nama, jumlah in atraksi_populer:
                persentase = (jumlah / total_tiket_atraksi * 100) if total_tiket_atraksi > 0 else 0
                atraksi_dengan_persentase.append({
                    'nama': nama,
                    'jumlah': jumlah,
                    'persentase': round(persentase, 1)
                })

            # Format nama lengkap
            nama_lengkap = user_data[2] or ""
            if user_data[3]:
                nama_lengkap += f" {user_data[3]}"
            if user_data[4]:
                nama_lengkap += f" {user_data[4]}"

            context = {
                'username': user_data[0],
                'email': user_data[1],
                'nama_lengkap': nama_lengkap,
                'no_telepon': user_data[5],
                'tiket_hari_ini': tiket_total,  # Gunakan total tiket
                'pengunjung_hari_ini': pengunjung_total,
                'pendapatan_hari_ini': pendapatan_total,
                'rata_rata_pendapatan': rata_rata_pendapatan,
                'penjualan_tiket': penjualan_tiket,
                'atraksi_populer': atraksi_dengan_persentase,
                'harga_tiket': HARGA_TIKET,
            }

    except Exception as e:
        messages.error(request, f"Terjadi kesalahan: {str(e)}")
        return redirect('login')
    
    return render(request, 'staff_dashboard.html', context)



@role_required('dokter')
def dokter_hewan_dashboard(request):
    username = request.user.username

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                p.username, 
                CONCAT_WS(' ', p.nama_depan, p.nama_tengah, p.nama_belakang) AS nama_lengkap,
                p.email,
                p.no_telepon,
                d.no_STR,
                (
                    SELECT s.nama_spesialisasi
                    FROM sizopi.spesialisasi s
                    WHERE s.username_SH = d.username_DH
                    LIMIT 1
                ) AS spesialisasi,
                (
                    SELECT COUNT(DISTINCT cm.id_hewan)
                    FROM sizopi.catatan_medis cm
                    WHERE cm.username_dh = d.username_DH
                ) AS jumlah_hewan_ditangani
            FROM sizopi.pengguna p
            JOIN sizopi.dokter_hewan d ON p.username = d.username_DH
            WHERE p.username = %s
        """, [username])
        row = cursor.fetchone()

    dokter = {
        'username': row[0],
        'nama': row[1],
        'email': row[2],
        'no_telepon': row[3],
        'no_str': row[4],
        'spesialisasi': row[5] or 'Belum ada',
        'jumlah_hewan_ditangani': row[6]
    } if row else {}

    return render(request, 'dokter_hewan_dashboard.html', {'dokter': dokter})


@role_required(('pengunjung', 'pengunjung_adopter'))
def pengunjung_dashboard(request):
    if 'username' not in request.session:
        messages.error(request, "Silakan login terlebih dahulu.")
        return redirect('login')
    
    username = request.session['username']
    today = date.today()

    try:
        with connection.cursor() as cursor:
            # Ambil data pengguna
            cursor.execute("""
                SELECT p.username, p.email, p.nama_depan, p.nama_tengah, p.nama_belakang, 
                       p.no_telepon, pg.alamat, pg.tgl_lahir
                FROM sizopi.pengguna p
                LEFT JOIN sizopi.pengunjung pg ON p.username = pg.username_p
                WHERE p.username = %s
            """, [username])
            user_data = cursor.fetchone()
            if not user_data:
                messages.error(request, "Data pengguna tidak ditemukan.")
                return redirect('login')

            # Ambil semua reservasi user
            cursor.execute("""
                SELECT nama_fasilitas, tanggal_kunjungan, jumlah_tiket, status
                FROM sizopi.reservasi
                WHERE username_p = %s
                ORDER BY tanggal_kunjungan DESC
            """, [username])
            all_reservasi = cursor.fetchall()

            # Riwayat kunjungan: semua reservasi yang statusnya bukan Dibatalkan dan tanggal <= hari ini
            riwayat_kunjungan = [
                r for r in all_reservasi if r[1] < today and r[3] != 'Dibatalkan'
]

            # Tiket mendatang: semua reservasi yang statusnya bukan Dibatalkan dan tanggal > hari ini
            tiket_mendatang = [
                r for r in all_reservasi if r[1] >= today and r[3] != 'Dibatalkan'
            ]

            # Nama lengkap
            nama_lengkap = user_data[2] or ""
            if user_data[3]:
                nama_lengkap += f" {user_data[3]}"
            if user_data[4]:
                nama_lengkap += f" {user_data[4]}"

            context = {
                'username': user_data[0],
                'email': user_data[1],
                'nama_lengkap': nama_lengkap,
                'no_telepon': user_data[5],
                'alamat': user_data[6],
                'tgl_lahir': user_data[7],
                'total_reservasi': len(riwayat_kunjungan),
                'total_tiket_mendatang': len(tiket_mendatang),
                'riwayat_kunjungan': riwayat_kunjungan,
                'tiket_mendatang': tiket_mendatang,
            }
    except Exception as e:
        messages.error(request, f"Terjadi kesalahan: {str(e)}")
        return redirect('login')
    
    return render(request, 'pengunjung_dashboard.html', context)


@role_required('penjaga_hewan')
def penjaga_hewan_dashboard(request):
    username = request.user.username

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                p.username,
                CONCAT_WS(' ', p.nama_depan, p.nama_tengah, p.nama_belakang) AS nama_lengkap,
                p.email,
                p.no_telepon,
                j.id_staf,
                (
                    SELECT COUNT(DISTINCT m.id_hewan) 
                    FROM sizopi.memberi m
                    JOIN sizopi.pakan p ON m.id_hewan = p.id_hewan
                    WHERE m.username_jh = j.username_jh
                      AND LOWER(p.status) = 'sudah diberikan'
                ) AS jumlah_pakan_diberikan
            FROM sizopi.pengguna p
            JOIN sizopi.penjaga_hewan j ON p.username = j.username_jh
            WHERE p.username = %s
        """, [username])
        row = cursor.fetchone()

    penjaga = {
        'username': row[0],
        'nama_lengkap': row[1],
        'email': row[2],
        'no_telepon': row[3],
        'id_staf': row[4],
        'jumlah_pakan_diberikan': row[5],
    } if row else {}

    return render(request, 'penjaga_hewan_dashboard.html', {'penjaga': penjaga})


@role_required('pelatih_pertunjukan')
def pelatih_pertunjukan_dashboard(request):
    username = request.session.get('username')
    today = date.today()
    now = datetime.now()

    # 1. Data profil pelatih
    with connection.cursor() as cur:
        cur.execute("""
            SELECT p.id_staf, u.username, u.email, u.no_telepon,
                   u.nama_depan, u.nama_tengah, u.nama_belakang
            FROM sizopi.pelatih_hewan p
            JOIN sizopi.pengguna u ON p.username_lh = u.username
            WHERE p.username_lh = %s
        """, [username])
        row = cur.fetchone()
        if not row:
            return render(request, 'pelatih_pertunjukan_dashboard.html', {'error': 'Data tidak ditemukan'})
        id_staf, username, email, no_telepon, nama_depan, nama_tengah, nama_belakang = row
        nama_lengkap = " ".join([n for n in [nama_depan, nama_tengah, nama_belakang] if n])

    # 2. Jadwal pertunjukan hari ini
    with connection.cursor() as cur:
        cur.execute("""
            SELECT j.tgl_penugasan, a.nama_atraksi, a.lokasi
            FROM sizopi.jadwal_penugasan j
            JOIN sizopi.atraksi a ON j.nama_atraksi = a.nama_atraksi
            WHERE j.username_lh = %s AND j.tgl_penugasan::date = %s
            ORDER BY j.tgl_penugasan
        """, [username, today])
        jadwal_hari_ini = [
            {
                'waktu': row[0].strftime('%H:%M'),
                'nama_atraksi': row[1],
                'lokasi': row[2],
                'durasi': '-',  # Tambahkan durasi jika ada di tabel
                'status': 'Siap'
            }
            for row in cur.fetchall()
        ]
        atraksi_hari_ini = [row[1] for row in cur.fetchall()]

    # 3. Daftar hewan yang dilatih (hewan yang ikut atraksi hari ini)
    daftar_hewan = []
    if jadwal_hari_ini:
        with connection.cursor() as cur:
            cur.execute("""
                SELECT DISTINCT h.id, h.nama, h.spesies
                FROM sizopi.berpartisipasi bp
                JOIN sizopi.hewan h ON bp.id_hewan = h.id
                WHERE bp.nama_fasilitas IN (
                    SELECT a.nama_atraksi
                    FROM sizopi.atraksi a
                    WHERE a.nama_atraksi IN %s
                )
            """, [tuple([jadwal['nama_atraksi'] for jadwal in jadwal_hari_ini])])
            daftar_hewan = [
                {'id': row[0], 'nama': row[1], 'spesies': row[2]}
                for row in cur.fetchall()
            ]

    # 4. Status latihan terakhir
    status_latihan = []
    with connection.cursor() as cur:
        for jadwal in jadwal_hari_ini:
            # Ambil waktu jadwal fasilitas (atraksi)
            cur.execute("""
                SELECT f.jadwal
                FROM sizopi.fasilitas f
                WHERE f.nama = %s
            """, [jadwal['nama_atraksi']])
            fasilitas_row = cur.fetchone()
            if fasilitas_row:
                waktu_jadwal = fasilitas_row[0]
                # Cek instance penugasan
                cur.execute("""
                    SELECT COUNT(*)
                    FROM sizopi.jadwal_penugasan
                    WHERE nama_atraksi = %s AND tgl_penugasan = %s
                """, [jadwal['nama_atraksi'], waktu_jadwal])
                penugasan_count = cur.fetchone()[0]
                if now < waktu_jadwal:
                    status = 'UPCOMING'
                elif now >= waktu_jadwal and penugasan_count == 0:
                    status = 'DUE'
                else:
                    status = 'FINISHED'
            else:
                status = '-'
            status_latihan.append({
                'nama': jadwal['nama_atraksi'],
                'tanggal': waktu_jadwal.strftime('%Y-%m-%d %H:%M') if fasilitas_row else '-',
                'latihan': 'Atraksi',
                'status': status
            })

    context = {
        'id_staf': id_staf,
        'nama_lengkap': nama_lengkap,
        'username': username,
        'email': email,
        'no_telepon': no_telepon,
        'peran': 'Staf Pelatih Pertunjukan',
        'jadwal_hari_ini': jadwal_hari_ini,
        'jumlah_pertunjukan_hari_ini': len(jadwal_hari_ini),
        'daftar_hewan': daftar_hewan,
        'status_latihan': status_latihan,
    }
    return render(request, 'pelatih_pertunjukan_dashboard.html', context)

@role_required('pengunjung_adopter')
def pengunjung_adopter_dashboard(request):
    if 'username' not in request.session:
        messages.error(request, "Silakan login terlebih dahulu.")
        return redirect('login')
    
    username = request.session['username']
    today = date.today()

    try:
        with connection.cursor() as cursor:
            # Ambil data pengguna
            cursor.execute("""
                SELECT p.username, p.email, p.nama_depan, p.nama_tengah, p.nama_belakang, 
                       p.no_telepon, pg.alamat, pg.tgl_lahir
                FROM sizopi.pengguna p
                LEFT JOIN sizopi.pengunjung pg ON p.username = pg.username_p
                WHERE p.username = %s
            """, [username])
            user_data = cursor.fetchone()
            if not user_data:
                messages.error(request, "Data pengguna tidak ditemukan.")
                return redirect('login')

            # Ambil semua reservasi user
            cursor.execute("""
                SELECT nama_fasilitas, tanggal_kunjungan, jumlah_tiket, status
                FROM sizopi.reservasi
                WHERE username_p = %s
                ORDER BY tanggal_kunjungan DESC
            """, [username])
            all_reservasi = cursor.fetchall()

            # Riwayat kunjungan: semua reservasi yang statusnya bukan Dibatalkan dan tanggal <= hari ini
            riwayat_kunjungan = [
                r for r in all_reservasi if r[1] < today and r[3] != 'Dibatalkan'
]

            # Tiket mendatang: semua reservasi yang statusnya bukan Dibatalkan dan tanggal > hari ini
            tiket_mendatang = [
                r for r in all_reservasi if r[1] >= today and r[3] != 'Dibatalkan'
            ]

            # Nama lengkap
            nama_lengkap = user_data[2] or ""
            if user_data[3]:
                nama_lengkap += f" {user_data[3]}"
            if user_data[4]:
                nama_lengkap += f" {user_data[4]}"

            context = {
                'username': user_data[0],
                'email': user_data[1],
                'nama_lengkap': nama_lengkap,
                'no_telepon': user_data[5],
                'alamat': user_data[6],
                'tgl_lahir': user_data[7],
                'total_reservasi': len(riwayat_kunjungan),
                'total_tiket_mendatang': len(tiket_mendatang),
                'riwayat_kunjungan': riwayat_kunjungan,
                'tiket_mendatang': tiket_mendatang,
            }
    except Exception as e:
        messages.error(request, f"Terjadi kesalahan: {str(e)}")
        return redirect('login')
    
    return render(request, 'pengunjung_adopter_dashboard.html', context)

