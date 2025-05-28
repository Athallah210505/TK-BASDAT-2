from django.shortcuts import render
from utils.decorators import role_required
from django.db import connection

# Create your views here.
def show_main(request):
    return render(request, 'main.html')

@role_required('staff')
def show_staff_dashboard(request):
    return render(request, 'staff_dashboard.html')

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


@role_required('pengunjung')
def pengunjung_dashboard(request):
    return render(request, 'pengunjung_dashboard.html')

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
    return render(request, 'pelatih_pertunjukan_dashboard.html')

@role_required('pengunjung_adopter')
def pengunjung_adopter_dashboard(request):
    return render(request, 'pengunjung_adopter_dashboard.html')

