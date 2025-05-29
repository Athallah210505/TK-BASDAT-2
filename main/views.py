from django.shortcuts import render
from django.db import connection
from utils.decorators import role_required
from datetime import date, datetime

# Create your views here.
def show_main(request):
    return render(request, 'main.html')

@role_required('staff')
def show_staff_dashboard(request):
    return render(request, 'staff_dashboard.html')

@role_required('dokter')
def dokter_hewan_dashboard(request):
    return render(request, 'dokter_hewan_dashboard.html')

@role_required('pengunjung')
def pengunjung_dashboard(request):
    return render(request, 'pengunjung_dashboard.html')

@role_required('penjaga_hewan')
def penjaga_hewan_dashboard(request):
    return render(request, 'penjaga_hewan_dashboard.html')

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
    return render(request, 'pengunjung_adopter_dashboard.html')

