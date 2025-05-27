from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection
from django.http import JsonResponse
from datetime import datetime
import re

def dictfetchall(cursor):
    """Return all rows from a cursor as a dict"""
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]

def show_atraksi_management(request):
    """View for displaying atraksi management page"""
    try:
        with connection.cursor() as cursor:
            # First determine if sizopi schema exists
            cursor.execute("""
                SELECT schema_name FROM information_schema.schemata 
                WHERE schema_name = 'sizopi'
            """)
            
            if cursor.rowcount == 0:
                # If schema doesn't exist, create it
                cursor.execute("CREATE SCHEMA IF NOT EXISTS sizopi")
            
            # Check if tables exist, and create if needed
            cursor.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'sizopi' AND table_name = 'fasilitas'
            """)
            
            if cursor.rowcount == 0:
                # Create necessary tables if they don't exist
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS sizopi.fasilitas (
                        nama VARCHAR(50) PRIMARY KEY,
                        jadwal TIMESTAMP NOT NULL,
                        kapasitas_max INT NOT NULL
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS sizopi.atraksi (
                        nama_atraksi VARCHAR(50) PRIMARY KEY,
                        lokasi VARCHAR(100) NOT NULL,
                        FOREIGN KEY (nama_atraksi) REFERENCES sizopi.fasilitas(nama) ON DELETE CASCADE ON UPDATE CASCADE
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS sizopi.hewan (
                        id UUID PRIMARY KEY,
                        nama VARCHAR(100) NOT NULL,
                        jenis VARCHAR(50) NOT NULL,
                        usia INT NOT NULL
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS sizopi.pelatih_hewan (
                        username_lh VARCHAR(50) PRIMARY KEY,
                        spesialisasi VARCHAR(100) NOT NULL
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS sizopi.pengguna (
                        username VARCHAR(50) PRIMARY KEY,
                        nama_depan VARCHAR(50) NOT NULL,
                        nama_belakang VARCHAR(50) NOT NULL
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS sizopi.jadwal_penugasan (
                        username_lh VARCHAR(50),
                        tgl_penugasan TIMESTAMP,
                        nama_atraksi VARCHAR(50),
                        PRIMARY KEY (username_lh, tgl_penugasan),
                        FOREIGN KEY (username_lh) REFERENCES sizopi.pelatih_hewan(username_lh) ON DELETE CASCADE ON UPDATE CASCADE,
                        FOREIGN KEY (nama_atraksi) REFERENCES sizopi.atraksi(nama_atraksi) ON DELETE CASCADE ON UPDATE CASCADE
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS sizopi.berpartisipasi (
                        nama_fasilitas VARCHAR(50),
                        id_hewan UUID,
                        PRIMARY KEY (nama_fasilitas, id_hewan),
                        FOREIGN KEY (nama_fasilitas) REFERENCES sizopi.fasilitas(nama) ON DELETE CASCADE ON UPDATE CASCADE,
                        FOREIGN KEY (id_hewan) REFERENCES sizopi.hewan(id) ON DELETE CASCADE ON UPDATE CASCADE
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS sizopi.wahana (
                        nama_wahana VARCHAR(50) PRIMARY KEY,
                        jenis VARCHAR(50) NOT NULL,
                        FOREIGN KEY (nama_wahana) REFERENCES sizopi.fasilitas(nama) ON DELETE CASCADE ON UPDATE CASCADE
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS sizopi.peraturan_wahana (
                        id SERIAL PRIMARY KEY,
                        nama_wahana VARCHAR(50),
                        peraturan TEXT NOT NULL,
                        FOREIGN KEY (nama_wahana) REFERENCES sizopi.wahana(nama_wahana) ON DELETE CASCADE ON UPDATE CASCADE
                    )
                """)
            
            # Get all attractions with related information
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
            attraction = dictfetchall(cursor)[0] if cursor.rowcount > 0 else None
            
            if not attraction:
                return JsonResponse({'error': 'Atraksi tidak ditemukan'}, status=404)
            
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
        return JsonResponse({'error': str(e)}, status=500)

def edit_atraksi(request, id):
    """View for editing an attraction"""
    if request.method == 'POST':
        lokasi = request.POST.get('lokasi')
        kapasitas = request.POST.get('kapasitas')
        jadwal = request.POST.get('jadwal')  # Format: HH:MM
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
                
                # Update atraksi table
                cursor.execute("""
                    UPDATE sizopi.atraksi
                    SET lokasi = %s
                    WHERE nama_atraksi = %s
                """, [lokasi, id])
                
                # Update fasilitas table
                cursor.execute("""
                    UPDATE sizopi.fasilitas
                    SET kapasitas_max = %s, jadwal = %s
                    WHERE nama = %s
                """, [kapasitas, jadwal_timestamp, id])
                
                # Delete existing jadwal_penugasan entries
                cursor.execute("""
                    DELETE FROM sizopi.jadwal_penugasan
                    WHERE nama_atraksi = %s
                """, [id])
                
                # Insert updated jadwal_penugasan entries
                for username_lh in pelatih_ids:
                    cursor.execute("""
                        INSERT INTO sizopi.jadwal_penugasan (username_lh, tgl_penugasan, nama_atraksi)
                        VALUES (%s, %s, %s)
                    """, [username_lh, jadwal_timestamp, id])
                
                # Delete existing berpartisipasi entries
                cursor.execute("""
                    DELETE FROM sizopi.berpartisipasi
                    WHERE nama_fasilitas = %s
                """, [id])
                
                # Insert updated berpartisipasi entries
                for id_hewan in hewan_ids:
                    cursor.execute("""
                        INSERT INTO sizopi.berpartisipasi (nama_fasilitas, id_hewan)
                        VALUES (%s, %s)
                    """, [id, id_hewan])
            
            messages.success(request, "Atraksi berhasil diperbarui!")
            return redirect('show_atraksi_management')
        
        except Exception as e:
            messages.error(request, f"Gagal memperbarui atraksi: {str(e)}")
            return redirect('show_atraksi_management')

def delete_atraksi(request, id):
    """View for deleting an attraction"""
    if request.method == 'POST':
        try:
            with connection.cursor() as cursor:
                # Due to ON DELETE CASCADE, we only need to delete from fasilitas
                cursor.execute("""
                    DELETE FROM sizopi.fasilitas
                    WHERE nama = %s
                """, [id])
            
            messages.success(request, "Atraksi berhasil dihapus!")
        except Exception as e:
            messages.error(request, f"Gagal menghapus atraksi: {str(e)}")
    
    return redirect('show_atraksi_management')

# Wahana Management Views
def show_wahana_management(request):
    """Show the wahana management page with list of wahanas"""
    try:
        with connection.cursor() as cursor:
            # Get wahana data with capacity and schedule from fasilitas
            cursor.execute("""
                SELECT w.nama_wahana, w.peraturan, f.kapasitas_max as kapasitas, 
                       TO_CHAR(f.jadwal, 'HH24:MI') as jadwal
                FROM sizopi.wahana w
                JOIN sizopi.fasilitas f ON w.nama_wahana = f.nama
            """)
            wahana_list = dictfetchall(cursor)
            
            # Format peraturan for display
            for wahana in wahana_list:
                if wahana.get('peraturan'):
                    # Parse peraturan into list items
                    if '\n' in wahana['peraturan']:
                        # Split by newlines
                        wahana['peraturan_list'] = [rule.strip() for rule in wahana['peraturan'].split('\n') if rule.strip()]
                    else:
                        # Single rule
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

def add_wahana(request):
    """Add a new wahana to the database"""
    if request.method == 'POST':
        try:
            nama_wahana = request.POST.get('nama_wahana')
            kapasitas = request.POST.get('kapasitas', 20)
            jadwal = request.POST.get('jadwal', '10:00')
            
            # Collect all peraturan entries
            peraturan_list = []
            for key in sorted([k for k in request.POST.keys() if k.startswith('peraturan_')]):
                peraturan_value = request.POST.get(key).strip()
                if peraturan_value:  # Only add non-empty values
                    peraturan_list.append(peraturan_value)
            
            # Join peraturan with newlines (without numbering)
            peraturan_text = '\n'.join(peraturan_list)
            
            # Start a transaction
            with connection.cursor() as cursor:
                # First insert into fasilitas
                current_date = datetime.now().strftime('%Y-%m-%d')
                jadwal_timestamp = f'{current_date} {jadwal}:00'
                
                cursor.execute("""
                    INSERT INTO sizopi.fasilitas (nama, jadwal, kapasitas_max)
                    VALUES (%s, %s, %s)
                """, [nama_wahana, jadwal_timestamp, kapasitas])
                
                # Then insert into wahana
                cursor.execute("""
                    INSERT INTO sizopi.wahana (nama_wahana, peraturan)
                    VALUES (%s, %s)
                """, [nama_wahana, peraturan_text])
                
            messages.success(request, f"Wahana '{nama_wahana}' berhasil ditambahkan!")
        except Exception as e:
            messages.error(request, f"Gagal menambahkan wahana: {str(e)}")
            
    return redirect('show_wahana_management')

def get_wahana_data(request, nama_wahana):
    """Get data for a specific wahana for AJAX requests"""
    try:
        with connection.cursor() as cursor:
            # Get wahana details with capacity and schedule
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
            
            # Process peraturan into a list
            peraturan_list = []
            if wahana.get('peraturan'):
                # Remove any existing numbering patterns like "1. " at the beginning of lines
                clean_peraturan = re.sub(r'^\d+\.\s*', '', wahana['peraturan'], flags=re.MULTILINE)
                
                # Split by newlines
                peraturan_list = [line.strip() for line in clean_peraturan.split('\n') if line.strip()]
                
            wahana['peraturan_list'] = peraturan_list
            
            return JsonResponse(wahana)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

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
                if peraturan_value:  # Only add non-empty values
                    peraturan_list.append(peraturan_value)
            
            # Join peraturan with newlines (without numbering)
            peraturan_text = '\n'.join(peraturan_list)
            
            with connection.cursor() as cursor:
                # Get current date from existing record
                cursor.execute("""
                    SELECT TO_CHAR(jadwal, 'YYYY-MM-DD') as date
                    FROM sizopi.fasilitas
                    WHERE nama = %s
                """, [nama_wahana])
                result = cursor.fetchone()
                date_str = result[0] if result else datetime.now().strftime('%Y-%m-%d')
                
                # Convert time string to timestamp with preserved date
                jadwal_timestamp = f'{date_str} {jadwal}:00'
                
                # Update fasilitas table with new capacity and schedule
                cursor.execute("""
                    UPDATE sizopi.fasilitas
                    SET kapasitas_max = %s, jadwal = %s
                    WHERE nama = %s
                """, [kapasitas, jadwal_timestamp, nama_wahana])
                
                # Update wahana table with new peraturan
                cursor.execute("""
                    UPDATE sizopi.wahana
                    SET peraturan = %s
                    WHERE nama_wahana = %s
                """, [peraturan_text, nama_wahana])
                
            messages.success(request, f"Wahana '{nama_wahana}' berhasil diperbarui!")
        except Exception as e:
            messages.error(request, f"Gagal memperbarui wahana: {str(e)}")
            
    return redirect('show_wahana_management')
def delete_wahana(request, nama_wahana):
    """Delete a wahana"""
    if request.method == 'POST':
        try:
            with connection.cursor() as cursor:
                # Delete from wahana first (make sure constraints are handled properly)
                cursor.execute("""
                    DELETE FROM sizopi.wahana
                    WHERE nama_wahana = %s
                """, [nama_wahana])
                
                # Then delete from fasilitas
                cursor.execute("""
                    DELETE FROM sizopi.fasilitas
                    WHERE nama = %s
                """, [nama_wahana])
                
            messages.success(request, f"Wahana '{nama_wahana}' berhasil dihapus!")
        except Exception as e:
            messages.error(request, f"Gagal menghapus wahana: {str(e)}")
            
    return redirect('show_wahana_management')