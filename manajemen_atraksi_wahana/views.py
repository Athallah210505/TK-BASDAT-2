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
                jadwal_timestamp = f'{date_str} {jadwal}:00'
                
                # STEP 1: Ambil semua pelatih yang sedang ditugaskan SEBELUM rotasi
                cursor.execute("""
                    SELECT jp.username_lh, 
                           p.nama_depan || ' ' || p.nama_belakang AS nama_pelatih,
                           EXTRACT(DAY FROM (CURRENT_DATE - jp.tgl_penugasan)) AS durasi_hari
                    FROM sizopi.jadwal_penugasan jp
                    JOIN sizopi.pelatih_hewan ph ON jp.username_lh = ph.username_lh
                    JOIN sizopi.pengguna p ON ph.username_lh = p.username
                    WHERE jp.nama_atraksi = %s
                """, [id])
                
                all_current_trainers = dictfetchall(cursor)
                
                # Identifikasi pelatih yang sudah >90 hari
                long_serving_trainers = [t for t in all_current_trainers if t.get('durasi_hari', 0) >= 90]
                rotated_trainer_ids = [t['username_lh'] for t in long_serving_trainers]
                
                print(f"Semua pelatih saat ini: {[t['username_lh'] for t in all_current_trainers]}")
                print(f"Pelatih yang akan dirotasi: {rotated_trainer_ids}")
                print(f"Pelatih yang dipilih user: {pelatih_ids}")
                
                # STEP 2: HAPUS pelatih >90 hari dari daftar yang dipilih user
                original_pelatih_ids = [p_id for p_id in pelatih_ids if p_id not in rotated_trainer_ids]
                
                print(f"Pelatih yang dipilih setelah filter rotasi: {original_pelatih_ids}")
                
                # STEP 3: Update atraksi untuk memicu trigger
                cursor.execute("""
                    UPDATE sizopi.atraksi
                    SET lokasi = %s
                    WHERE nama_atraksi = %s
                """, [lokasi, id])
                
                # STEP 4: Update fasilitas
                cursor.execute("""
                    UPDATE sizopi.fasilitas
                    SET kapasitas_max = %s, jadwal = %s
                    WHERE nama = %s
                """, [kapasitas, jadwal_timestamp, id])
                
                # STEP 5: Berikan waktu untuk trigger diproses
                from time import sleep
                sleep(0.3)  # 300ms delay
                
                # STEP 6: Ambil data pelatih setelah trigger berjalan
                cursor.execute("""
                    SELECT jp.username_lh, 
                           p.nama_depan || ' ' || p.nama_belakang AS nama_pelatih,
                           jp.tgl_penugasan
                    FROM sizopi.jadwal_penugasan jp
                    JOIN sizopi.pelatih_hewan ph ON jp.username_lh = ph.username_lh
                    JOIN sizopi.pengguna p ON ph.username_lh = p.username
                    WHERE jp.nama_atraksi = %s
                """, [id])
                
                current_trainers_after_trigger = dictfetchall(cursor)
                current_trainer_ids_after = [t['username_lh'] for t in current_trainers_after_trigger]
                
                print(f"Pelatih setelah trigger: {current_trainer_ids_after}")
                
                # STEP 7: Identifikasi pelatih baru yang ditambahkan oleh trigger
                trigger_added_trainers = []
                for trainer in current_trainers_after_trigger:
                    username_lh = trainer['username_lh']
                    # Pelatih yang ditambahkan trigger = ada sekarang tapi tidak ada di daftar awal
                    if (username_lh not in [t['username_lh'] for t in all_current_trainers] and
                        username_lh not in original_pelatih_ids):
                        trigger_added_trainers.append(username_lh)
                
                print(f"Pelatih baru dari trigger: {trigger_added_trainers}")
                
                # STEP 8: Buat daftar final pelatih yang harus ada
                final_trainer_ids = list(original_pelatih_ids) + trigger_added_trainers
                
                print(f"Daftar final pelatih yang harus ada: {final_trainer_ids}")
                
                # STEP 9: HAPUS SEMUA pelatih yang tidak ada di daftar final
                # Ini adalah perbaikan utama - hapus semua yang tidak diperlukan sekaligus
                if final_trainer_ids:
                    # Buat placeholder untuk IN clause
                    placeholders = ','.join(['%s'] * len(final_trainer_ids))
                    cursor.execute(f"""
                        DELETE FROM sizopi.jadwal_penugasan
                        WHERE nama_atraksi = %s 
                        AND username_lh NOT IN ({placeholders})
                    """, [id] + final_trainer_ids)
                    
                    deleted_count = cursor.rowcount
                    print(f"Jumlah pelatih yang dihapus: {deleted_count}")
                else:
                    # Jika tidak ada pelatih yang harus dipertahankan, hapus semua
                    cursor.execute("""
                        DELETE FROM sizopi.jadwal_penugasan
                        WHERE nama_atraksi = %s
                    """, [id])
                    deleted_count = cursor.rowcount
                    print(f"Semua pelatih dihapus: {deleted_count}")
                
                # STEP 10: Tambahkan pelatih yang dipilih user jika belum ada
                for username_lh in final_trainer_ids:
                    cursor.execute("""
                        SELECT 1 FROM sizopi.jadwal_penugasan
                        WHERE username_lh = %s AND nama_atraksi = %s
                    """, [username_lh, id])
                    
                    if cursor.fetchone() is None:
                        cursor.execute("""
                            INSERT INTO sizopi.jadwal_penugasan (username_lh, tgl_penugasan, nama_atraksi)
                            VALUES (%s, %s, %s)
                        """, [username_lh, datetime.now(), id])
                        print(f"Menambahkan pelatih: {username_lh}")
                
                # STEP 11: Update hewan yang berpartisipasi
                cursor.execute("""
                    DELETE FROM sizopi.berpartisipasi
                    WHERE nama_fasilitas = %s
                """, [id])
                
                for id_hewan in hewan_ids:
                    cursor.execute("""
                        INSERT INTO sizopi.berpartisipasi (nama_fasilitas, id_hewan)
                        VALUES (%s, %s)
                    """, [id, id_hewan])
                
                # STEP 12: Tampilkan pesan untuk pelatih yang dirotasi
                for trainer in long_serving_trainers:
                    messages.warning(request, f"Pelatih \"{trainer['nama_pelatih']}\" telah bertugas lebih dari 3 bulan di atraksi \"{id}\" dan akan diganti.")
                
                # STEP 13: Tampilkan pesan untuk pelatih pengganti
                for trainer_id in trigger_added_trainers:
                    for trainer in current_trainers_after_trigger:
                        if trainer['username_lh'] == trainer_id:
                            messages.success(request, f"Pelatih \"{trainer['nama_pelatih']}\" telah ditugaskan sebagai pengganti.")
                            break
                
                # STEP 14: Verifikasi hasil akhir
                cursor.execute("""
                    SELECT jp.username_lh, p.nama_depan || ' ' || p.nama_belakang AS nama_pelatih
                    FROM sizopi.jadwal_penugasan jp
                    JOIN sizopi.pelatih_hewan ph ON jp.username_lh = ph.username_lh
                    JOIN sizopi.pengguna p ON ph.username_lh = p.username
                    WHERE jp.nama_atraksi = %s
                """, [id])
                
                final_trainers = dictfetchall(cursor)
                print(f"Pelatih final setelah update: {[t['username_lh'] for t in final_trainers]}")
            
            # Tampilkan pesan sukses
            if not long_serving_trainers:
                messages.success(request, "Atraksi berhasil diperbarui!")
            else:
                messages.success(request, "Atraksi berhasil diperbarui dengan rotasi pelatih.")
            return redirect('show_atraksi_management')
        
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            messages.error(request, f"Gagal memperbarui atraksi: {str(e)}")
            return redirect('show_atraksi_management')
        
        

@role_required('staff')
def delete_atraksi(request, id):
    """View for deleting an attraction"""
    if request.method == 'POST':
        try:
            with connection.cursor() as cursor:
                # 1. Hapus dulu data reservasi yang terkait
                cursor.execute("""
                    DELETE FROM sizopi.RESERVASI
                    WHERE nama_fasilitas = %s
                """, [id])
                reservasi_deleted = cursor.rowcount
                print(f"DEBUG - Deleted {reservasi_deleted} related reservations for attraction: {id}")

                # 2. Hapus data jadwal penugasan
                cursor.execute("""
                    DELETE FROM sizopi.jadwal_penugasan
                    WHERE nama_atraksi = %s
                """, [id])
                jadwal_deleted = cursor.rowcount
                print(f"DEBUG - Deleted {jadwal_deleted} related trainer assignments for attraction: {id}")
                
                # 3. Hapus data berpartisipasi (tabel yang menghubungkan fasilitas dengan hewan)
                cursor.execute("""
                    DELETE FROM sizopi.berpartisipasi
                    WHERE nama_fasilitas = %s
                """, [id])
                partisipasi_deleted = cursor.rowcount
                print(f"DEBUG - Deleted {partisipasi_deleted} related animal participations for attraction: {id}")
                
                # 4. Hapus data atraksi
                cursor.execute("""
                    DELETE FROM sizopi.atraksi
                    WHERE nama_atraksi = %s
                """, [id])
                atraksi_deleted = cursor.rowcount
                print(f"DEBUG - Deleted attraction record: {atraksi_deleted}")

                # 5. Terakhir, hapus data fasilitas
                cursor.execute("""
                    DELETE FROM sizopi.fasilitas
                    WHERE nama = %s
                """, [id])
                fasilitas_deleted = cursor.rowcount
                print(f"DEBUG - Deleted facility record: {fasilitas_deleted}")
            
            if reservasi_deleted > 0:
                messages.info(request, f"{reservasi_deleted} reservasi terkait atraksi '{id}' juga dihapus.")
            
            messages.success(request, f"Atraksi '{id}' berhasil dihapus beserta seluruh data terkait!")
            
        except Exception as e:
            import traceback
            print(f"ERROR deleting attraction: {str(e)}")
            print(traceback.format_exc())
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
                # 1. Hapus dulu data reservasi yang terkait
                cursor.execute("""
                    DELETE FROM sizopi.RESERVASI
                    WHERE nama_fasilitas = %s
                """, [nama_wahana])
                reservasi_deleted = cursor.rowcount
                print(f"DEBUG - Deleted {reservasi_deleted} related reservations for wahana: {nama_wahana}")
                
                # 2. Hapus data wahana
                cursor.execute("""
                    DELETE FROM sizopi.wahana
                    WHERE nama_wahana = %s
                """, [nama_wahana])
                wahana_deleted = cursor.rowcount
                print(f"DEBUG - Deleted wahana record: {wahana_deleted}")
                
                # 3. Terakhir, hapus data fasilitas
                cursor.execute("""
                    DELETE FROM sizopi.fasilitas
                    WHERE nama = %s
                """, [nama_wahana])
                fasilitas_deleted = cursor.rowcount
                print(f"DEBUG - Deleted facility record: {fasilitas_deleted}")
                
                if reservasi_deleted > 0:
                    messages.info(request, f"{reservasi_deleted} reservasi terkait wahana '{nama_wahana}' juga dihapus.")
                
                messages.success(request, f"Wahana '{nama_wahana}' berhasil dihapus beserta seluruh data terkait!")
                
        except Exception as e:
            import traceback
            print(f"ERROR deleting wahana: {str(e)}")
            print(traceback.format_exc())
            messages.error(request, f"Gagal menghapus wahana: {str(e)}")
            
    return redirect('show_wahana_management')