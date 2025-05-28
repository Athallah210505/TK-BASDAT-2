from django.shortcuts import render
from utils.decorators import role_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection
from datetime import date


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
    return render(request, 'dokter_hewan_dashboard.html')

@role_required('pengunjung')
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
    return render(request, 'penjaga_hewan_dashboard.html')

@role_required('pelatih_pertunjukan')
def pelatih_pertunjukan_dashboard(request):
    return render(request, 'pelatih_pertunjukan_dashboard.html')

@role_required('pengunjung_adopter')
def pengunjung_adopter_dashboard(request):
    return render(request, 'pengunjung_adopter_dashboard.html')

