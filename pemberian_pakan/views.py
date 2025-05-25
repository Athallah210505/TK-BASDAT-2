from django.shortcuts import render, redirect
from django.db import connection
from django.contrib import messages
from utils.decorators import role_required
from datetime import datetime
import uuid
from django.http import JsonResponse

def dictfetchall(cursor):
    """Return all rows from a cursor as a dict"""
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]

@role_required('penjaga_hewan')
def show_pemberian_pakan(request, id_hewan=None):
    """
    View to show an animal's feeding schedule and details.
    If id_hewan is provided, it will show details for that animal.
    """
    with connection.cursor() as cursor:
        if id_hewan:
            cursor.execute("""
                SELECT h.id, h.nama, h.spesies, h.asal_hewan, h.tanggal_lahir, 
                       h.status_kesehatan, h.nama_habitat, h.url_foto
                FROM SIZOPI.HEWAN h
                WHERE h.id = %s
            """, [id_hewan])
            animal = dictfetchall(cursor)
            
            if not animal:
                messages.error(request, "Hewan tidak ditemukan.")
                return redirect('show_pemberian_pakan')
            
            animal = animal[0]
            
            cursor.execute("""
                SELECT p.id_hewan, p.jadwal, p.jenis, p.jumlah, p.status
                FROM SIZOPI.PAKAN p
                WHERE p.id_hewan = %s
                ORDER BY p.jadwal
            """, [id_hewan])
            
            feedings = dictfetchall(cursor)
            
            for feeding in feedings:
                if isinstance(feeding['jadwal'], str):
                    feeding['jadwal'] = datetime.strptime(feeding['jadwal'], '%Y-%m-%d %H:%M:%S')
                feeding['tanggal'] = feeding['jadwal'].strftime('%d %b %Y')
                feeding['waktu'] = feeding['jadwal'].strftime('%H:%M WIB')
                feeding['jadwal_str'] = feeding['jadwal'].strftime('%Y-%m-%d %H:%M:%S')
            
            upcoming_feedings = [f for f in feedings if f['status'].lower().strip() in ['menunggu pemberian', 'menunggu pemberian']]
            completed_feedings = [f for f in feedings if f['status'].lower().strip() in ['selesai diberikan', 'sudah diberikan']]

            
            return render(request, 'show_pemberian_pakan.html', {
                'animal': animal,
                'upcoming_feedings': upcoming_feedings,
                'completed_feedings': completed_feedings
            })
        else:
            cursor.execute("""
                SELECT h.id, h.nama, h.spesies, h.url_foto, h.status_kesehatan
                FROM SIZOPI.HEWAN h
                ORDER BY h.nama
            """)
            animals = dictfetchall(cursor)
            
            return render(request, 'list_hewan.html', {'animals': animals})

@role_required('penjaga_hewan')
def add_feeding_schedule(request, id_hewan):
    """Add a new feeding schedule for an animal"""
    if request.method == 'POST':
        try:
            jenis_pakan = request.POST.get('new_food_type')
            jumlah_pakan = request.POST.get('new_food_amount')
            jadwal_str = request.POST.get('new_feeding_schedule')
            
            jadwal = datetime.strptime(jadwal_str, '%Y-%m-%dT%H:%M')
            
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO SIZOPI.PAKAN (id_hewan, jadwal, jenis, jumlah, status)
                    VALUES (%s, %s, %s, %s, 'Menunggu Pemberian')
                """, [id_hewan, jadwal, jenis_pakan, jumlah_pakan])
                
            messages.success(request, "Jadwal pemberian pakan berhasil ditambahkan")
        except Exception as e:
            messages.error(request, f"Gagal menambahkan jadwal: {str(e)}")
            
        return redirect('show_pemberian_pakan', id_hewan=id_hewan)
    
    return redirect('show_pemberian_pakan', id_hewan=id_hewan)

@role_required('penjaga_hewan')
@role_required('penjaga_hewan')
def update_feeding_schedule(request, id_hewan, jadwal):
    """Update pakan dari form modal"""
    if request.method == 'POST':
        try:
            jenis = request.POST.get('food_type')
            jumlah = request.POST.get('food_amount')
            jadwal_baru_str = request.POST.get('feeding_date')
            jadwal_baru = datetime.strptime(jadwal_baru_str, '%Y-%m-%dT%H:%M')

            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE SIZOPI.PAKAN
                    SET jenis = %s, jumlah = %s, jadwal = %s
                    WHERE id_hewan = %s AND jadwal = %s
                """, [jenis, jumlah, jadwal_baru, id_hewan, jadwal])
            
            messages.success(request, "Jadwal berhasil diperbarui.")
        except Exception as e:
            messages.error(request, f"Gagal memperbarui jadwal: {str(e)}")
        
        return redirect('show_pemberian_pakan', id_hewan=id_hewan)
    else:
        messages.error(request, "Metode tidak diizinkan.")
        return redirect('show_pemberian_pakan', id_hewan=id_hewan)


@role_required('penjaga_hewan')
def delete_feeding_schedule(request, id_hewan, jadwal):
    """Delete a feeding schedule"""
    if request.method == 'POST':
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    DELETE FROM SIZOPI.PAKAN
                    WHERE id_hewan = %s AND jadwal = %s
                """, [id_hewan, jadwal])
                
            messages.success(request, "Jadwal pemberian pakan berhasil dihapus")
        except Exception as e:
            messages.error(request, f"Gagal menghapus jadwal: {str(e)}")
    else:
        messages.error(request, "Metode tidak diizinkan")
        
    return redirect('show_pemberian_pakan', id_hewan=id_hewan)

@role_required('penjaga_hewan')
def mark_feeding_complete(request, id_hewan, jadwal):
    try:
        username_jh = request.user.username

        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE SIZOPI.PAKAN
                SET status = 'Sudah diberikan'
                WHERE id_hewan = %s AND jadwal = %s
            """, [id_hewan, jadwal])

            cursor.execute("""
                SELECT 1 FROM SIZOPI.MEMBERI
                WHERE id_hewan = %s AND jadwal = %s
            """, [id_hewan, jadwal])

            exists = cursor.fetchone()

            if exists:
                cursor.execute("""
                    UPDATE SIZOPI.MEMBERI
                    SET username_jh = %s
                    WHERE id_hewan = %s AND jadwal = %s
                """, [username_jh, id_hewan, jadwal])
            else:
                cursor.execute("""
                    INSERT INTO SIZOPI.MEMBERI (id_hewan, jadwal, username_jh)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (id_hewan, jadwal) DO UPDATE 
                    SET username_jh = EXCLUDED.username_jh
                """, [id_hewan, jadwal, username_jh])

        messages.success(request, "Pemberian pakan berhasil dicatat")
    except Exception as e:
        messages.error(request, f"Gagal mencatat pemberian pakan: {str(e)}")

    return redirect('show_pemberian_pakan', id_hewan=id_hewan)


@role_required('penjaga_hewan')
def riwayat_pemberian_pakan(request):
    username_jh = request.user.get_username()
    print(f"[DEBUG] username penjaga: {username_jh}")

    if not username_jh:
        messages.error(request, "Gagal mendapatkan username. Silakan login ulang.")
        return redirect('logout')  

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT h.id, h.nama, h.spesies, h.asal_hewan, h.tanggal_lahir, 
                   h.status_kesehatan, h.nama_habitat, p.jenis as pakan,
                   p.jumlah, p.jadwal, p.status, h.url_foto
            FROM SIZOPI.HEWAN h
            JOIN SIZOPI.PAKAN p ON h.id = p.id_hewan
            JOIN SIZOPI.MEMBERI m 
              ON p.id_hewan = m.id_hewan
             AND p.jadwal BETWEEN m.jadwal - INTERVAL '59 seconds' AND m.jadwal + INTERVAL '59 seconds'
            WHERE m.username_jh = %s
              AND LOWER(p.status) = 'sudah diberikan'
            ORDER BY p.jadwal DESC
        """, [username_jh])
        
        feedings = dictfetchall(cursor)

        for feeding in feedings:
            if isinstance(feeding['jadwal'], str):
                feeding['jadwal'] = datetime.strptime(feeding['jadwal'], '%Y-%m-%d %H:%M:%S')
            if isinstance(feeding['tanggal_lahir'], str):
                feeding['tanggal_lahir'] = datetime.strptime(feeding['tanggal_lahir'], '%Y-%m-%d')
                
            feeding['tanggal_lahir_formatted'] = feeding['tanggal_lahir'].strftime('%d/%m/%Y')
            feeding['jadwal_tanggal'] = feeding['jadwal'].strftime('%d %b %Y')
            feeding['jadwal_waktu'] = feeding['jadwal'].strftime('%H:%M')
            feeding['jadwal_str'] = feeding['jadwal'].strftime('%Y-%m-%d %H:%M:%S')
        
    return render(request, 'riwayat_pemberian_pakan.html', {'feedings': feedings})
