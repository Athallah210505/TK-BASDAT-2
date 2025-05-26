from datetime import date
from django.contrib import messages
from django.shortcuts import redirect, render
from utils.decorators import role_required
from django.db import connection, DatabaseError
from psycopg2 import errors

@role_required('dokter')
def show_jadwal_pemeriksaan(request):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT h.id, h.nama, h.url_foto,
                   COALESCE(j.tgl_pemeriksaan_selanjutnya, NULL) AS tgl_selanjutnya,
                   COALESCE(j.freq_pemeriksaan_rutin, 3) AS frekuensi
            FROM sizopi.hewan h
            LEFT JOIN sizopi.jadwal_pemeriksaan_kesehatan j
              ON h.id = j.id_hewan
            ORDER BY h.nama;
        """)
        rows = cursor.fetchall()

    jadwal_list = [
        {
            'id': row[0],
            'nama': row[1],
            'url_foto': row[2],
            'tgl_selanjutnya': row[3],
            'frekuensi': row[4]
        }
        for row in rows
    ]

    return render(request, 'show_jadwal_pemeriksaan.html', {
        'jadwal_list': jadwal_list
    })

@role_required('dokter')
def show_jadwal_satu_hewan(request):
    hewan_id = request.GET.get('id')
    if not hewan_id:
        return redirect('show_jadwal_pemeriksaan')

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, nama, spesies, asal_hewan, tanggal_lahir, url_foto
            FROM sizopi.hewan
            WHERE id = %s
        """, [hewan_id])
        row = cursor.fetchone()

        if not row:
            return redirect('show_jadwal_pemeriksaan')

        hewan = {
            'id': row[0],
            'nama': row[1],
            'spesies': row[2],
            'asal': row[3],
            'usia': calculate_age(row[4]),
            'url_foto': row[5],
        }

        cursor.execute("""
            SELECT freq_pemeriksaan_rutin
            FROM sizopi.jadwal_pemeriksaan_kesehatan
            WHERE id_hewan = %s
            LIMIT 1
        """, [hewan_id])
        freq_row = cursor.fetchone()
        frekuensi_rutin = freq_row[0] if freq_row else 'Tidak ditentukan'

        cursor.execute("""
            SELECT tgl_pemeriksaan_selanjutnya
            FROM sizopi.jadwal_pemeriksaan_kesehatan
            WHERE id_hewan = %s
            ORDER BY tgl_pemeriksaan_selanjutnya ASC
        """, [hewan_id])
        jadwal_list = [row[0].strftime('%d %B %Y') for row in cursor.fetchall()]

    return render(request, 'show_jadwal_satu_hewan.html', {
        'hewan': hewan,
        'frekuensi_rutin': frekuensi_rutin,
        'jadwal_list': jadwal_list
    })

def calculate_age(birth_date):
    if birth_date is None:
        return "Tidak diketahui"
    today = date.today()
    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    return f"{age} tahun"

@role_required('dokter')
def edit_jadwal_pemeriksaan(request):
    if request.method == 'POST':
        id_hewan = request.POST.get('id_hewan')
        tanggal_lama = request.POST.get('tanggal_lama')
        tanggal_baru = request.POST.get('tanggal_baru')

        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE sizopi.jadwal_pemeriksaan_kesehatan
                    SET tgl_pemeriksaan_selanjutnya = %s
                    WHERE id_hewan = %s AND tgl_pemeriksaan_selanjutnya = %s
                """, [tanggal_baru, id_hewan, tanggal_lama])
            messages.success(request, "Tanggal berhasil diperbarui.")
        except Exception as e:
            messages.error(request, f"Gagal mengubah tanggal: {str(e)}")

        return redirect(f"/jadwal_pemeriksaan/jadwal_satu_hewan?id={id_hewan}")

@role_required('dokter')
def hapus_jadwal_pemeriksaan(request):
    if request.method == 'POST':
        id_hewan = request.POST.get('id_hewan')
        tanggal_hapus = request.POST.get('tanggal_hapus')

        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    DELETE FROM sizopi.jadwal_pemeriksaan_kesehatan
                    WHERE id_hewan = %s AND tgl_pemeriksaan_selanjutnya = %s
                """, [id_hewan, tanggal_hapus])
            messages.success(request, "Jadwal berhasil dihapus.")
        except Exception as e:
            messages.error(request, f"Gagal menghapus jadwal: {str(e)}")

        return redirect(f"/jadwal_pemeriksaan/jadwal_satu_hewan?id={id_hewan}")

@role_required('dokter')
def tambah_jadwal_pemeriksaan(request):
    if request.method == 'POST':
        id_hewan = request.POST.get('id_hewan')
        tanggal_baru = request.POST.get('tanggal_baru')

        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT freq_pemeriksaan_rutin FROM sizopi.jadwal_pemeriksaan_kesehatan
                    WHERE id_hewan = %s LIMIT 1
                """, [id_hewan])
                freq = cursor.fetchone()
                freq_value = freq[0] if freq else 3

                cursor.execute("""
                    INSERT INTO sizopi.jadwal_pemeriksaan_kesehatan (id_hewan, tgl_pemeriksaan_selanjutnya, freq_pemeriksaan_rutin)
                    VALUES (%s, %s, %s)
                """, [id_hewan, tanggal_baru, freq_value])

            messages.success(request, "Jadwal pemeriksaan berhasil ditambahkan.")
        except DatabaseError as e:
            error_message = getattr(e, 'pgerror', str(e))
            if "SUKSES:" in error_message:
                messages.success(request, error_message.strip())
            else:
                messages.error(request, f"Gagal menambahkan jadwal: {error_message}")

        return redirect(f"/jadwal_pemeriksaan/jadwal_satu_hewan?id={id_hewan}")

@role_required('dokter')
def edit_frekuensi_pemeriksaan(request):
    if request.method == 'POST':
        id_hewan = request.POST.get('id_hewan')
        frekuensi_baru = request.POST.get('frekuensi_baru')

        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE sizopi.jadwal_pemeriksaan_kesehatan
                    SET freq_pemeriksaan_rutin = %s
                    WHERE id_hewan = %s
                """, [frekuensi_baru, id_hewan])

            messages.success(request, "Frekuensi berhasil diperbarui.")
        except Exception as e:
            messages.error(request, f"Gagal memperbarui frekuensi: {str(e)}")

        return redirect(f"/jadwal_pemeriksaan/jadwal_satu_hewan?id={id_hewan}")
