from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection
from django.http import JsonResponse
from datetime import datetime
import re
from utils.decorators import role_required

def dictfetchall(cursor):
    """Return all rows from a cursor as a dict"""
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]
@role_required('staff')
def show_atraksi_management(request):
    """View for displaying atraksi management page"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT schema_name FROM information_schema.schemata 
                WHERE schema_name = 'sizopi'
            """)
            cursor.execute("""
                SELECT a.nama_atraksi as id, a.nama_atraksi as nama, a.lokasi, 
                       f.kapasitas_max as kapasitas, TO_CHAR(f.jadwal, 'HH24:MI') as jadwal,
                       string_agg(DISTINCT h.nama, ', ') as hewan_terlibat,
                       string_agg(DISTINCT (p.nama_depan || ' ' || p.nama_belakang), ', ') as pelatih
                FROM sizopi.atraksi a
                JOIN sizopi.fasilitas f ON a.nama_atraksi = f.nama
                LEFT JOIN sizopi.berpartisipasi b ON f.nama = b.nama_fasilitas
                LEFT JOIN sizopi.hewan h ON b.id_hewan = h.id
                LEFT JOIN sizopi.jadwal_penugasan jp ON a.nama_atraksi = jp.nama_atraksi
                LEFT JOIN sizopi.pelatih_hewan ph ON jp.username_lh = ph.username_lh
                LEFT JOIN sizopi.pengguna p ON ph.username_lh = p.username
                GROUP BY a.nama_atraksi, a.lokasi, f.kapasitas_max, f.jadwal
                ORDER BY a.nama_atraksi
            """)
            attractions = dictfetchall(cursor)
            
            # Get all trainers for the form
            cursor.execute("""
                SELECT ph.username_lh as id, p.nama_depan || ' ' || p.nama_belakang as nama
                FROM sizopi.pelatih_hewan ph
                JOIN sizopi.pengguna p ON ph.username_lh = p.username
                ORDER BY nama
            """)
            trainers = dictfetchall(cursor)
            
            # Get all animals for the form
            cursor.execute("SELECT id, nama FROM sizopi.hewan ORDER BY nama")
            animals = dictfetchall(cursor)
        
        context = {
            'attractions': attractions,
            'trainers': trainers,
            'animals': animals
        }
        
        return render(request, 'atraksi_management.html', context)
    
    except Exception as e:
        messages.error(request, f"Terjadi kesalahan: {str(e)}")
        return render(request, 'atraksi_management.html', {'error': str(e)})

@role_required('staff')
def add_atraksi(request):
    """View for adding a new attraction"""
    if request.method == 'POST':
        nama = request.POST.get('nama')
        lokasi = request.POST.get('lokasi')
        kapasitas = request.POST.get('kapasitas')
        jadwal = request.POST.get('jadwal')  # Format: HH:MM
        pelatih_ids = request.POST.getlist('pelatih')
        hewan_ids = request.POST.getlist('hewan')
        
        try:
            with connection.cursor() as cursor:
                # Convert time string to timestamp with current date
                current_date = datetime.now().strftime('%Y-%m-%d')
                jadwal_timestamp = f'{current_date} {jadwal}:00'
                
                # First insert into fasilitas
                cursor.execute("""
                    INSERT INTO sizopi.fasilitas (nama, jadwal, kapasitas_max)
                    VALUES (%s, %s, %s)
                """, [nama, jadwal_timestamp, kapasitas])
                
                # Then insert into atraksi
                cursor.execute("""
                    INSERT INTO sizopi.atraksi (nama_atraksi, lokasi)
                    VALUES (%s, %s)
                """, [nama, lokasi])
                
                # Insert into jadwal_penugasan for each trainer
                for username_lh in pelatih_ids:
                    cursor.execute("""
                        INSERT INTO sizopi.jadwal_penugasan (username_lh, tgl_penugasan, nama_atraksi)
                        VALUES (%s, %s, %s)
                    """, [username_lh, jadwal_timestamp, nama])
                
                # Insert into berpartisipasi for each animal
                for id_hewan in hewan_ids:
                    cursor.execute("""
                        INSERT INTO sizopi.berpartisipasi (nama_fasilitas, id_hewan)
                        VALUES (%s, %s)
                    """, [nama, id_hewan])
                
            messages.success(request, "Atraksi berhasil ditambahkan!")
            return redirect('show_atraksi_management')
        
        except Exception as e:
            messages.error(request, f"Gagal menambahkan atraksi: {str(e)}")
            return redirect('show_atraksi_management')
@role_required('staff')
def get_atraksi_data(request, id):
    """View to get attraction data for editing via AJAX"""
    try:
        with connection.cursor() as cursor:
            # Get attraction details
            cursor.execute("""
                SELECT a.nama_atraksi as id, a.nama_atraksi as nama, a.lokasi, 
                       f.kapasitas_max as kapasitas, TO_CHAR(f.jadwal, 'HH24:MI') as jadwal
                FROM sizopi.atraksi a
                JOIN sizopi.fasilitas f ON a.nama_atraksi = f.nama
                WHERE a.nama_atraksi = %s
            """, [id])
            
            results = dictfetchall(cursor)
            if not results:
                return JsonResponse({'error': 'Atraksi tidak ditemukan'}, status=404)
            
            attraction = results[0]
            
            # Get selected trainers
            cursor.execute("""
                SELECT username_lh as id_pelatih
                FROM sizopi.jadwal_penugasan
                WHERE nama_atraksi = %s
            """, [id])
            selected_trainers = [item['id_pelatih'] for item in dictfetchall(cursor)]
            
            # Get selected animals
            cursor.execute("""
                SELECT id_hewan
                FROM sizopi.berpartisipasi
                WHERE nama_fasilitas = %s
            """, [id])
            selected_animals = [str(item['id_hewan']) for item in dictfetchall(cursor)]
            
            # Get all trainers
            cursor.execute("""
                SELECT ph.username_lh as id, p.nama_depan || ' ' || p.nama_belakang as nama
                FROM sizopi.pelatih_hewan ph
                JOIN sizopi.pengguna p ON ph.username_lh = p.username
                ORDER BY nama
            """)
            trainers = dictfetchall(cursor)
            
            # Get all animals
            cursor.execute("SELECT id, nama FROM sizopi.hewan ORDER BY nama")
            animals = dictfetchall(cursor)
        
        data = {
            'id': attraction['id'],
            'nama': attraction['nama'],
            'lokasi': attraction['lokasi'],
            'kapasitas': attraction['kapasitas'],
            'jadwal': attraction['jadwal'],
            'selected_trainers': selected_trainers,
            'selected_animals': selected_animals,
            'trainers': trainers,
            'animals': animals
        }
        
        return JsonResponse(data)
    
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"ERROR in get_atraksi_data: {error_details}")
        return JsonResponse({'error': str(e), 'details': error_details}, status=500)
    
    
    
@role_required('staff')
def edit_atraksi(request, id):
    """View for editing an attraction"""
    if request.method == 'POST':
        lokasi = request.POST.get('lokasi')
        kapasitas = request.POST.get('kapasitas')
        jadwal = request.POST.get('jadwal')  
        pelatih_ids = request.POST.getlist('pelatih')
        hewan_ids = request.POST.getlist('hewan')
        
        try:
            with connection.cursor() as cursor:
                # Get current date from existing record
                cursor.execute("""
                    SELECT TO_CHAR(jadwal, 'YYYY-MM-DD') as date
                    FROM sizopi.fasilitas
                    WHERE nama = %s
                """, [id])
                result = cursor.fetchone()
                date_str = result[0] if result else datetime.now().strftime('%Y-%m-%d')
                
                # Convert time string to timestamp with preserved date
                jadwal_timestamp = f'{date_str} {jadwal}:00'
                
                # Langkah 1: Temukan pelatih yang sudah bertugas >90 hari
                cursor.execute("""
                    SELECT jp.username_lh, 
                           p.nama_depan || ' ' || p.nama_belakang AS nama_pelatih,
                           EXTRACT(DAY FROM (CURRENT_DATE - MIN(jp.tgl_penugasan))) AS durasi_hari
                    FROM sizopi.jadwal_penugasan jp
                    JOIN sizopi.pelatih_hewan ph ON jp.username_lh = ph.username_lh
                    JOIN sizopi.pengguna p ON ph.username_lh = p.username
                    WHERE jp.nama_atraksi = %s
                    GROUP BY jp.username_lh, p.nama_depan, p.nama_belakang, jp.tgl_penugasan
                    HAVING EXTRACT(DAY FROM (CURRENT_DATE - MIN(jp.tgl_penugasan))) >= 90
                """, [id])
                
                long_serving_trainers = dictfetchall(cursor)
                rotated_trainer_ids = [t['username_lh'] for t in long_serving_trainers]
                
                # Langkah 2: HAPUS pelatih tersebut dari list pelatih yang dipilih
                pelatih_ids = [pid for pid in pelatih_ids if pid not in rotated_trainer_ids]
                
                # Langkah 3: Update atraksi untuk memicu trigger
                cursor.execute("""
                    UPDATE sizopi.atraksi
                    SET lokasi = %s
                    WHERE nama_atraksi = %s
                """, [lokasi, id])
                
                # Langkah 4: Update fasilitas
                cursor.execute("""
                    UPDATE sizopi.fasilitas
                    SET kapasitas_max = %s, jadwal = %s
                    WHERE nama = %s
                """, [kapasitas, jadwal_timestamp, id])
                
                # Langkah 5: Periksa pelatih yang ditambahkan oleh trigger
                cursor.execute("""
                    SELECT jp.username_lh, p.nama_depan || ' ' || p.nama_belakang AS nama_pelatih
                    FROM sizopi.jadwal_penugasan jp
                    JOIN sizopi.pelatih_hewan ph ON jp.username_lh = ph.username_lh
                    JOIN sizopi.pengguna p ON ph.username_lh = p.username
                    WHERE jp.nama_atraksi = %s
                """, [id])
                
                current_trainers = dictfetchall(cursor)
                current_trainer_ids = [t['username_lh'] for t in current_trainers]
                
                # Langkah 6: Temukan pelatih yang ditambahkan oleh trigger (tidak ada di seleksi sebelumnya)
                new_trainer_ids = []
                for trainer_id in current_trainer_ids:
                    if trainer_id not in pelatih_ids and trainer_id not in rotated_trainer_ids:
                        new_trainer_ids.append(trainer_id)
                        pelatih_ids.append(trainer_id)  # Tambahkan ke list yang akan dipertahankan
                
                # Langkah 7: Tampilkan pesan untuk pelatih yang dirotasi
                for trainer in long_serving_trainers:
                    username_lh = trainer['username_lh']
                    nama_pelatih = trainer['nama_pelatih']
                    messages.success(request, f"Pelatih \"{nama_pelatih}\" telah bertugas lebih dari 3 bulan di atraksi \"{id}\" dan akan diganti.")
                    
                # Langkah 8: Tampilkan pesan untuk pelatih pengganti
                for trainer_id in new_trainer_ids:
                    # Cari nama pelatih
                    for trainer in current_trainers:
                        if trainer['username_lh'] == trainer_id:
                            messages.info(request, f"Pelatih \"{trainer['nama_pelatih']}\" telah ditugaskan sebagai pengganti.")
                            break
                
                # Langkah 9: Hapus pelatih yang tidak dipilih user dan bukan pengganti dari trigger
                if pelatih_ids:
                    cursor.execute("""
                        DELETE FROM sizopi.jadwal_penugasan
                        WHERE nama_atraksi = %s AND username_lh NOT IN %s
                    """, [id, tuple(pelatih_ids) if len(pelatih_ids) > 1 else f"('{pelatih_ids[0]}')"])
                else:
                    cursor.execute("""
                        DELETE FROM sizopi.jadwal_penugasan
                        WHERE nama_atraksi = %s
                    """, [id])
                
                # Langkah 10: Tambahkan pelatih baru yang dipilih user jika belum ada
                for username_lh in pelatih_ids:
                    cursor.execute("""
                        SELECT 1 FROM sizopi.jadwal_penugasan
                        WHERE username_lh = %s AND nama_atraksi = %s
                    """, [username_lh, id])
                    
                    if cursor.fetchone() is None:
                        cursor.execute("""
                            INSERT INTO sizopi.jadwal_penugasan (username_lh, tgl_penugasan, nama_atraksi)
                            VALUES (%s, %s, %s)
                        """, [username_lh, datetime.now(), id])
                
                # Langkah 11: Update hewan yang berpartisipasi
                cursor.execute("""
                    DELETE FROM sizopi.berpartisipasi
                    WHERE nama_fasilitas = %s
                """, [id])
                
                for id_hewan in hewan_ids:
                    cursor.execute("""
                        INSERT INTO sizopi.berpartisipasi (nama_fasilitas, id_hewan)
                        VALUES (%s, %s)
                    """, [id, id_hewan])
            
            # Tampilkan pesan sukses jika tidak ada pelatih yang dirotasi
            if not long_serving_trainers:
                messages.success(request, "Atraksi berhasil diperbarui!")
            return redirect('show_atraksi_management')
        
        except Exception as e:
            messages.error(request, f"Gagal memperbarui atraksi: {str(e)}")
            return redirect('show_atraksi_management')
        
        
@role_required('staff')
def delete_atraksi(request, id):
    """View for deleting an attraction"""
    if request.method == 'POST':
        try:
            with connection.cursor() as cursor:
              
                cursor.execute("""
                    DELETE FROM sizopi.fasilitas
                    WHERE nama = %s
                """, [id])
            
            messages.success(request, "Atraksi berhasil dihapus!")
        except Exception as e:
            messages.error(request, f"Gagal menghapus atraksi: {str(e)}")
    
    return redirect('show_atraksi_management')


@role_required('staff')
def show_wahana_management(request):
    """Show the wahana management page with list of wahanas"""
    try:
        with connection.cursor() as cursor:
            
            cursor.execute("""
                SELECT w.nama_wahana, w.peraturan, f.kapasitas_max as kapasitas, 
                       TO_CHAR(f.jadwal, 'HH24:MI') as jadwal
                FROM sizopi.wahana w
                JOIN sizopi.fasilitas f ON w.nama_wahana = f.nama
            """)
            wahana_list = dictfetchall(cursor)
            
           
            for wahana in wahana_list:
                if wahana.get('peraturan'):
                   
                    if '\n' in wahana['peraturan']:
                        
                        wahana['peraturan_list'] = [rule.strip() for rule in wahana['peraturan'].split('\n') if rule.strip()]
                    else:
                       
                        wahana['peraturan_list'] = [wahana['peraturan']]
            
        context = {
            'wahana_list': wahana_list,
            'error': None
        }
        return render(request, 'wahana_management.html', context)
    except Exception as e:
        context = {
            'wahana_list': [],
            'error': f"Terjadi kesalahan database: {str(e)}"
        }
        return render(request, 'wahana_management.html', context)


@role_required('staff')
def add_wahana(request):
    """Add a new wahana to the database"""
    if request.method == 'POST':
        try:
            nama_wahana = request.POST.get('nama_wahana')
            kapasitas = request.POST.get('kapasitas', 20)
            jadwal = request.POST.get('jadwal', '10:00')
            
            peraturan_list = []
            for key in sorted([k for k in request.POST.keys() if k.startswith('peraturan_')]):
                peraturan_value = request.POST.get(key).strip()
                if peraturan_value:  
                    peraturan_list.append(peraturan_value)
            
            peraturan_text = '\n'.join(peraturan_list)
            
            with connection.cursor() as cursor:
                current_date = datetime.now().strftime('%Y-%m-%d')
                jadwal_timestamp = f'{current_date} {jadwal}:00'
                
                cursor.execute("""
                    INSERT INTO sizopi.fasilitas (nama, jadwal, kapasitas_max)
                    VALUES (%s, %s, %s)
                """, [nama_wahana, jadwal_timestamp, kapasitas])
                
                cursor.execute("""
                    INSERT INTO sizopi.wahana (nama_wahana, peraturan)
                    VALUES (%s, %s)
                """, [nama_wahana, peraturan_text])
                
            messages.success(request, f"Wahana '{nama_wahana}' berhasil ditambahkan!")
        except Exception as e:
            messages.error(request, f"Gagal menambahkan wahana: {str(e)}")
            
    return redirect('show_wahana_management')


@role_required('staff')
def get_wahana_data(request, nama_wahana):
    """Get data for a specific wahana for AJAX requests"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT w.nama_wahana, w.peraturan, f.kapasitas_max as kapasitas, 
                       TO_CHAR(f.jadwal, 'HH24:MI') as jadwal
                FROM sizopi.wahana w
                JOIN sizopi.fasilitas f ON w.nama_wahana = f.nama
                WHERE w.nama_wahana = %s
            """, [nama_wahana])
            
            results = dictfetchall(cursor)
            if not results:
                return JsonResponse({'error': 'Wahana tidak ditemukan'}, status=404)
            
            wahana = results[0]
            
            peraturan_list = []
            if wahana.get('peraturan'):
                clean_peraturan = re.sub(r'^\d+\.\s*', '', wahana['peraturan'], flags=re.MULTILINE)
                
                peraturan_list = [line.strip() for line in clean_peraturan.split('\n') if line.strip()]
                
            wahana['peraturan_list'] = peraturan_list
            
            return JsonResponse(wahana)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@role_required('staff')
def edit_wahana(request, nama_wahana):
    """Edit an existing wahana"""
    if request.method == 'POST':
        try:
            kapasitas = request.POST.get('kapasitas', 20)
            jadwal = request.POST.get('jadwal', '10:00')
            
            # Collect all peraturan entries
            peraturan_list = []
            for key in sorted([k for k in request.POST.keys() if k.startswith('edit_peraturan_')]):
                peraturan_value = request.POST.get(key).strip()
                if peraturan_value:  
                    peraturan_list.append(peraturan_value)
            
            peraturan_text = '\n'.join(peraturan_list)
            
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT TO_CHAR(jadwal, 'YYYY-MM-DD') as date
                    FROM sizopi.fasilitas
                    WHERE nama = %s
                """, [nama_wahana])
                result = cursor.fetchone()
                date_str = result[0] if result else datetime.now().strftime('%Y-%m-%d')
                
                jadwal_timestamp = f'{date_str} {jadwal}:00'
                
                cursor.execute("""
                    UPDATE sizopi.fasilitas
                    SET kapasitas_max = %s, jadwal = %s
                    WHERE nama = %s
                """, [kapasitas, jadwal_timestamp, nama_wahana])
                
                cursor.execute("""
                    UPDATE sizopi.wahana
                    SET peraturan = %s
                    WHERE nama_wahana = %s
                """, [peraturan_text, nama_wahana])
                
            messages.success(request, f"Wahana '{nama_wahana}' berhasil diperbarui!")
        except Exception as e:
            messages.error(request, f"Gagal memperbarui wahana: {str(e)}")
            
    return redirect('show_wahana_management')

@role_required('staff')
def delete_wahana(request, nama_wahana):
    """Delete a wahana"""
    if request.method == 'POST':
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    DELETE FROM sizopi.wahana
                    WHERE nama_wahana = %s
                """, [nama_wahana])
                
                cursor.execute("""
                    DELETE FROM sizopi.fasilitas
                    WHERE nama = %s
                """, [nama_wahana])
                
            messages.success(request, f"Wahana '{nama_wahana}' berhasil dihapus!")
        except Exception as e:
            messages.error(request, f"Gagal menghapus wahana: {str(e)}")
            
    return redirect('show_wahana_management')