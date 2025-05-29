from datetime import date
import psycopg2
from django.contrib import messages
from django.shortcuts import redirect, render
from utils.decorators import role_required
from django.db import connection, DatabaseError
from psycopg2 import errors
from django.db import transaction

@role_required('dokter')
def show_jadwal_pemeriksaan(request):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT DISTINCT ON (h.nama)
                   h.id, h.nama, h.url_foto,
                   COALESCE(j.freq_pemeriksaan_rutin, 3) AS frekuensi
            FROM sizopi.hewan h
            LEFT JOIN sizopi.jadwal_pemeriksaan_kesehatan j
              ON h.id = j.id_hewan
            ORDER BY h.nama, j.tgl_pemeriksaan_selanjutnya ASC
        """)
        rows = cursor.fetchall()

    jadwal_list = [
        {
            'id': row[0],
            'nama': row[1],
            'url_foto': row[2],
            'frekuensi': row[3]
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
        frekuensi_rutin = freq_row[0] if freq_row else 3

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
                freq_value = request.session.pop(f"pending_freq_{id_hewan}", None)
                if not freq_value:
                    cursor.execute("""
                        SELECT MAX(freq_pemeriksaan_rutin)
                        FROM sizopi.jadwal_pemeriksaan_kesehatan
                        WHERE id_hewan = %s
                    """, [id_hewan])
                    freq_row = cursor.fetchone()
                    freq_value = freq_row[0] if freq_row and freq_row[0] is not None else 3
                
                cursor.execute("""
                    SELECT nama FROM sizopi.hewan WHERE id = %s
                """, [id_hewan])
                nama_row = cursor.fetchone()
                hewan_nama = nama_row[0] if nama_row else "Tidak diketahui"

                cursor.execute("""
                    INSERT INTO sizopi.jadwal_pemeriksaan_kesehatan (
                        id_hewan, tgl_pemeriksaan_selanjutnya, freq_pemeriksaan_rutin
                    ) VALUES (%s, %s, %s)
                """, [id_hewan, tanggal_baru, freq_value])

                cursor.execute("SHOW app.message;")
                result = cursor.fetchone()
                if result and result[0]:
                    message = result[0]
                    if "SUKSES:" in message:
                        messages.success(request, message)
                    else:
                        messages.info(request, message)
                else:
                    messages.success(request, f'SUKSES: Jadwal rutin hewan "{hewan_nama}" telah ditambahkan sesuai frekuensi.')

        except Exception as e:
            messages.error(request, f"Terjadi kesalahan saat menambahkan jadwal: {e}")

        return redirect(f"/jadwal_pemeriksaan/jadwal_satu_hewan?id={id_hewan}")
    
@role_required('dokter')
def edit_frekuensi_pemeriksaan(request):
    if request.method == 'POST':
        id_hewan = request.POST.get('id_hewan')
        frekuensi_baru = request.POST.get('frekuensi_baru')

        if not id_hewan or not frekuensi_baru:
            messages.error(request, "ID hewan dan frekuensi baru wajib diisi.")
            return redirect(f"/jadwal_pemeriksaan/jadwal_satu_hewan?id={id_hewan}")

        try:
            frekuensi_baru = int(frekuensi_baru)

            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE sizopi.jadwal_pemeriksaan_kesehatan
                    SET freq_pemeriksaan_rutin = %s
                    WHERE id_hewan = %s
                """, [frekuensi_baru, id_hewan])

                if cursor.rowcount == 0:
                    request.session[f"pending_freq_{id_hewan}"] = frekuensi_baru
                    messages.success(request, f"Frekuensi disimpan sementara: {frekuensi_baru} bulan. Akan diterapkan saat menambah jadwal.")
                else:
                    messages.success(request, f"Frekuensi berhasil diperbarui menjadi {frekuensi_baru} bulan.")

        except ValueError:
            messages.error(request, "Frekuensi baru harus berupa angka bulat.")
        except Exception as e:
            messages.error(request, f"Gagal memperbarui frekuensi: {str(e)}")

        return redirect(f"/jadwal_pemeriksaan/jadwal_satu_hewan?id={id_hewan}")
