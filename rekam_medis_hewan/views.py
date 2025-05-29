from django.shortcuts import render, redirect
from django.db import DatabaseError, connection
from django.contrib import messages
from django.urls import reverse
from utils.decorators import role_required
from psycopg2 import errors
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

@role_required('dokter')
def show_rekam_medis(request):
    hewan_id = request.GET.get('id')
    if not hewan_id:
        messages.error(request, "ID Hewan tidak ditemukan.")
        return redirect('home')

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, nama, spesies, asal_hewan, tanggal_lahir, url_foto
            from sizopi.hewan
            WHERE id = %s
        """, [hewan_id])
        hewan_row = cursor.fetchone()

        if not hewan_row:
            messages.error(request, "Data hewan tidak ditemukan.")
            return redirect('home')

        hewan = {
            'id_hewan': hewan_row[0],
            'nama_hewan': hewan_row[1],
            'spesies': hewan_row[2],
            'asal_hewan': hewan_row[3],
            'tanggal_lahir': hewan_row[4],
            'url_foto': hewan_row[5]
        }

        cursor.execute("""
            SELECT cm.id_hewan, cm.tanggal_pemeriksaan, d.username_DH AS username_dh,
                   cm.status_kesehatan, cm.diagnosis, cm.pengobatan,
                   COALESCE(cm.catatan_tindak_lanjut, '')
            FROM sizopi.catatan_medis cm
            JOIN sizopi.dokter_hewan d ON cm.username_dh = d.username_DH
            WHERE cm.id_hewan = %s
            ORDER BY cm.tanggal_pemeriksaan DESC
        """, [hewan_id])

        rekam_medis = [
            {
                'id_hewan': row[0],
                'tanggal_pemeriksaan': row[1],
                'username_dh': row[2],
                'status_kesehatan': row[3],
                'diagnosis': row[4],
                'pengobatan': row[5],
                'catatan_tindak_lanjut': row[6],
            }
            for row in cursor.fetchall()
        ]

    return render(request, 'show_rekam_medis.html', {
        'hewan_id': hewan_id,
        'hewan': hewan,
        'rekam_medis': rekam_medis,
    })

@role_required('dokter')
def form_rekam_medis(request):
    id_hewan = request.GET.get('id')
    username_dh = request.user.username

    if request.method == 'POST':
        tanggal_pemeriksaan = request.POST.get('tanggal_pemeriksaan')
        status_kesehatan = request.POST.get('status_kesehatan')
        diagnosis = request.POST.get('diagnosis') or None
        pengobatan = request.POST.get('pengobatan') or None

        try:
            with connection.cursor() as cursor:
                connection.ensure_connection()
                raw_conn = connection.connection
                raw_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

                cursor.execute("""
                    INSERT INTO sizopi.catatan_medis (
                        id_hewan, username_dh, tanggal_pemeriksaan, 
                        diagnosis, pengobatan, status_kesehatan, catatan_tindak_lanjut
                    ) VALUES (%s, %s, %s, %s, %s, %s, NULL)
                """, [id_hewan, username_dh, tanggal_pemeriksaan,
                      diagnosis, pengobatan, status_kesehatan])

                # Ambil pesan dari trigger
                cursor.execute("SHOW app.message;")
                result = cursor.fetchone()

                if result and result[0]:
                    success_message = result[0]
                    messages.success(request, success_message)
                else:
                    messages.success(request, "Rekam medis berhasil ditambahkan.")

                # Tambahan jika status sakit
                if status_kesehatan == 'Sakit':
                    cursor.execute("""
                        SELECT nama FROM sizopi.hewan WHERE id = %s
                    """, [id_hewan])
                    nama_row = cursor.fetchone()
                    if nama_row:
                        nama_hewan = nama_row[0]
                        trigger_message = f'SUKSES: Jadwal pemeriksaan hewan "{nama_hewan}" telah diperbarui karena status kesehatan "Sakit".'
                        messages.success(request, trigger_message)

        except DatabaseError as e:
            messages.error(request, f'Gagal menambahkan catatan medis: {str(e)}')

        return redirect(reverse('show_rekam_medis') + f'?id={id_hewan}')

    elif request.method == 'GET':
        if not id_hewan:
            messages.error(request, "ID Hewan tidak ditemukan.")
            return redirect('list_rekam_medis_hewan')

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT nama, spesies, asal_hewan, tanggal_lahir, url_foto
                FROM sizopi.hewan
                WHERE id = %s
            """, [id_hewan])
            row = cursor.fetchone()

        if not row:
            messages.error(request, "Data hewan tidak ditemukan.")
            return redirect('list_rekam_medis_hewan')

        hewan = {
            'id_hewan': id_hewan,
            'nama': row[0],
            'spesies': row[1],
            'asal_hewan': row[2],
            'tanggal_lahir': row[3],
            'url_foto': row[4],
        }

        return render(request, 'form_rekam_medis.html', {
            'id_hewan': id_hewan,
            'hewan': hewan,
            'username_dh': username_dh,
        })


@role_required('dokter')
def edit_rekam_medis(request):
    if request.method == 'POST':
        try:
            record_id = request.POST.get('record_id')
            diagnosis = request.POST.get('diagnosa')
            pengobatan = request.POST.get('pengobatan')
            tindak_lanjut = request.POST.get('tindak_lanjut')

            id_hewan, tanggal_pemeriksaan = record_id.split('|')

            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE SIZOPI.CATATAN_MEDIS
                    SET diagnosis = %s,
                        pengobatan = %s,
                        catatan_tindak_lanjut = %s
                    WHERE id_hewan = %s AND tanggal_pemeriksaan = %s
                """, [diagnosis, pengobatan, tindak_lanjut, id_hewan, tanggal_pemeriksaan])

            messages.success(request, 'Rekam medis berhasil diperbarui.')
        except Exception as e:
            messages.error(request, f'Gagal memperbarui rekam medis: {e}')

    return redirect(request.META.get('HTTP_REFERER', '/rekam-medis/'))

@role_required('dokter')
def delete_rekam_medis(request):
    if request.method == 'POST':
        try:
            record_id = request.POST.get('record_id')
            id_hewan, tanggal_pemeriksaan = record_id.split('|')

            with connection.cursor() as cursor:
                cursor.execute("""
                    DELETE FROM sizopi.catatan_medis
                    WHERE id_hewan = %s AND tanggal_pemeriksaan = %s
                """, [id_hewan, tanggal_pemeriksaan])

            messages.success(request, 'Rekam medis berhasil dihapus.')
        except Exception as e:
            messages.error(request, f'Gagal menghapus rekam medis: {e}')

    return redirect(request.META.get('HTTP_REFERER', '/rekam-medis/'))

@role_required('dokter')
def list_rekam_medis_hewan(request):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, nama, spesies, asal_hewan, url_foto
            FROM sizopi.hewan
            ORDER BY nama
        """)
        rows = cursor.fetchall()

    hewan_list = [
        {
            'id': row[0],
            'nama': row[1],
            'spesies': row[2],
            'asal_hewan': row[3],
            'url_foto': row[4]
        } for row in rows
    ]

    return render(request, 'list_rekam_medis_hewan.html', {
        'hewan_list': hewan_list
    })
