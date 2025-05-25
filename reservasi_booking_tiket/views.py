from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.db import connection
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from datetime import datetime
from utils.decorators import role_required

def dictfetchall(cursor):
    """Return all rows from a cursor as a dict"""
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]


def show_admin_booking(request):
    """
    Menampilkan semua booking untuk admin
    """
    try:
        print("DEBUG: Mencoba menjalankan query admin booking")
        
        with connection.cursor() as cursor:
            # Debugging untuk melihat tabel dan kolom yang ada
            cursor.execute("""
                SELECT column_name, table_name 
                FROM information_schema.columns 
                WHERE table_schema = 'sizopi' AND table_name = 'pengunjung'
            """)
            columns = cursor.fetchall()
            print(f"DEBUG: Kolom di tabel PENGUNJUNG: {columns}")
            
            # Query untuk mendapatkan semua reservasi dengan informasi apakah atraksi atau wahana
            cursor.execute("""
                SELECT 
                    r.username_p, 
                    r.nama_fasilitas, 
                    r.tanggal_kunjungan, 
                    r.jumlah_tiket, 
                    r.status,
                    CASE 
                        WHEN a.nama_atraksi IS NOT NULL THEN 'atraksi'
                        WHEN w.nama_wahana IS NOT NULL THEN 'wahana'
                        ELSE 'unknown'
                    END as jenis,
                    a.lokasi,
                    w.peraturan
                FROM 
                    sizopi.RESERVASI r
                LEFT JOIN 
                    sizopi.ATRAKSI a ON r.nama_fasilitas = a.nama_atraksi
                LEFT JOIN 
                    sizopi.WAHANA w ON r.nama_fasilitas = w.nama_wahana
                ORDER BY 
                    r.tanggal_kunjungan DESC
            """)
            
            reservasi_all = dictfetchall(cursor)
            
            # Pisahkan hasil menjadi atraksi dan wahana untuk kompatibilitas template
            reservasi_atraksi = []
            reservasi_wahana = []
            
            for r in reservasi_all:
                if r['jenis'] == 'atraksi':
                    # Tambahkan nama_atraksi untuk kompatibilitas template
                    r['nama_atraksi'] = r['nama_fasilitas']
                    reservasi_atraksi.append(r)
                elif r['jenis'] == 'wahana':
                    # Tambahkan nama_wahana untuk kompatibilitas template
                    r['nama_wahana'] = r['nama_fasilitas']
                    reservasi_wahana.append(r)
            
            print(f"DEBUG: Jumlah reservasi atraksi: {len(reservasi_atraksi)}")
            print(f"DEBUG: Jumlah reservasi wahana: {len(reservasi_wahana)}")
            
        context = {
            'reservasi_atraksi': reservasi_atraksi,
            'reservasi_wahana': reservasi_wahana,
            'title': 'Admin Dashboard - Reservasi',
            'role': 'admin'
        }
        
        return render(request, 'admin_booking.html', context)
    
    except Exception as e:
        import traceback
        print(f"DEBUG - Error: {str(e)}")
        print(f"DEBUG - Traceback: {traceback.format_exc()}")
        messages.error(request, f"Terjadi kesalahan: {str(e)}")
        return render(request, 'admin_booking.html', {
            'reservasi_atraksi': [],
            'reservasi_wahana': [],
            'title': 'Admin Dashboard - Reservasi', 
            'role': 'admin'
        })


def admin_edit_booking(request):
    """
    Mengedit booking dari admin
    """
    if request.method == 'POST':
        try:
            # Get form data
            jenis_reservasi = request.POST.get('jenis_reservasi')
            username = request.POST.get('username')
            nama_fasilitas = request.POST.get('nama_fasilitas')
            tanggal_asli_str = request.POST.get('tanggal_asli')
            tanggal_baru_str = request.POST.get('tanggal_kunjungan')
            jumlah_tiket = int(request.POST.get('jumlah_tiket', 1))
            status = request.POST.get('status', 'Terjadwal')
            
            # Convert dates
            tanggal_asli = datetime.strptime(tanggal_asli_str, '%Y-%m-%d').date()
            tanggal_baru = datetime.strptime(tanggal_baru_str, '%Y-%m-%d').date()
            
            with connection.cursor() as cursor:
                # Update reservasi di tabel RESERVASI baru
                cursor.execute("""
                    UPDATE sizopi.RESERVASI
                    SET tanggal_kunjungan = %s,
                        jumlah_tiket = %s,
                        status = %s
                    WHERE username_p = %s
                    AND nama_fasilitas = %s
                    AND tanggal_kunjungan = %s
                """, [tanggal_baru, jumlah_tiket, status, username, nama_fasilitas, tanggal_asli])
                
                if cursor.rowcount > 0:
                    messages.success(request, f"Reservasi {jenis_reservasi} berhasil diperbarui!")
                else:
                    messages.error(request, f"Gagal memperbarui reservasi {jenis_reservasi}")
            
            return redirect('show_admin_booking')
        
        except Exception as e:
            messages.error(request, f"Terjadi kesalahan: {str(e)}")
            return redirect('show_admin_booking')
    
    # Redirect jika bukan POST request
    return redirect('show_admin_booking')


def admin_cancel_booking(request):
    """
    Membatalkan booking dari admin
    """
    if request.method == 'POST':
        try:
            username = request.POST.get('username')
            nama_fasilitas = request.POST.get('nama_fasilitas')
            tanggal_str = request.POST.get('tanggal_kunjungan')
            
            tanggal_kunjungan = datetime.strptime(tanggal_str, '%Y-%m-%d').date()
            
            with connection.cursor() as cursor:
                # Batalkan reservasi di tabel RESERVASI baru
                cursor.execute("""
                    UPDATE sizopi.RESERVASI
                    SET status = 'Dibatalkan'
                    WHERE username_p = %s
                    AND nama_fasilitas = %s
                    AND tanggal_kunjungan = %s
                """, [username, nama_fasilitas, tanggal_kunjungan])
                
                if cursor.rowcount > 0:
                    messages.success(request, f"Reservasi untuk {username} berhasil dibatalkan!")
                else:
                    messages.error(request, "Gagal membatalkan reservasi")
            
            return redirect('show_admin_booking')
        
        except Exception as e:
            messages.error(request, f"Terjadi kesalahan: {str(e)}")
            return redirect('show_admin_booking')
    
    # Redirect jika bukan POST request
    return redirect('show_admin_booking')

@role_required('pengunjung')
def show_user_booking(request):
    """
    Menampilkan booking untuk pengguna yang sedang login
    """
    username = request.session.get('username', '')
    
    print(f"DEBUG - Username dari session: {username}")
    
    try:
        with connection.cursor() as cursor:
            # Query untuk mendapatkan semua reservasi pengguna
            cursor.execute("""
                SELECT 
                    r.username_p, 
                    r.nama_fasilitas, 
                    r.tanggal_kunjungan, 
                    r.jumlah_tiket, 
                    r.status,
                    CASE 
                        WHEN a.nama_atraksi IS NOT NULL THEN 'atraksi'
                        WHEN w.nama_wahana IS NOT NULL THEN 'wahana'
                        ELSE 'unknown'
                    END as jenis,
                    a.lokasi,
                    w.peraturan
                FROM 
                    sizopi.RESERVASI r
                LEFT JOIN 
                    sizopi.ATRAKSI a ON r.nama_fasilitas = a.nama_atraksi
                LEFT JOIN 
                    sizopi.WAHANA w ON r.nama_fasilitas = w.nama_wahana
                WHERE 
                    r.username_p = %s
                ORDER BY 
                    r.tanggal_kunjungan DESC
            """, [username])
            
            reservasi_all = dictfetchall(cursor)
            print(f"DEBUG - Ditemukan {len(reservasi_all)} reservasi untuk {username}")
            
            # Pisahkan hasil menjadi atraksi dan wahana
            reservasi_atraksi = []
            reservasi_wahana = []
            
            for r in reservasi_all:
                if r['jenis'] == 'atraksi':
                    # Tambahkan nama_atraksi untuk kompatibilitas template
                    r['nama_atraksi'] = r['nama_fasilitas']
                    reservasi_atraksi.append(r)
                elif r['jenis'] == 'wahana':
                    # Tambahkan nama_wahana untuk kompatibilitas template
                    r['nama_wahana'] = r['nama_fasilitas']
                    reservasi_wahana.append(r)
            
            print(f"DEBUG - Jumlah reservasi atraksi: {len(reservasi_atraksi)}")
            print(f"DEBUG - Jumlah reservasi wahana: {len(reservasi_wahana)}")
            
        context = {
            'reservasi_atraksi': reservasi_atraksi,
            'reservasi_wahana': reservasi_wahana,
            'title': 'Reservasi Saya',
            'role': 'user',
            'username': username
        }
        
        return render(request, 'user_booking.html', context)
    
    except Exception as e:
        import traceback
        print(f"ERROR: {str(e)}")
        print(traceback.format_exc())
        
        messages.error(request, f"Terjadi kesalahan: {str(e)}")
        return render(request, 'user_booking.html', {
            'reservasi_atraksi': [],
            'reservasi_wahana': [],
            'title': 'Reservasi Saya', 
            'role': 'user',
            'username': username
        })

# @login_required
@role_required('pengunjung')
def show_user_add_booking(request):
    """
    Menampilkan form untuk menambahkan booking baru
    """
    today = datetime.now().date()
    
    # Ambil username dari session (sesuai dengan cara login Anda)
    username = request.session.get('username', '')
    
    if request.method == 'POST':
        try:
            # Gunakan username dari session bukan dari request.user
            jenis_reservasi = request.POST.get('jenis_reservasi')
            nama_fasilitas = request.POST.get('nama_fasilitas')
            tanggal_str = request.POST.get('tanggal_kunjungan')
            jumlah_tiket = int(request.POST.get('jumlah_tiket', 1))
            
            # Debug - print all POST data
            print("Debug - POST data:")
            for key, value in request.POST.items():
                print(f"{key}: {value}")
            
            tanggal_kunjungan = datetime.strptime(tanggal_str, '%Y-%m-%d').date()
            
            with connection.cursor() as cursor:
                # Cek ketersediaan untuk fasilitas
                cursor.execute("""
                    SELECT f.kapasitas_max,
                           COALESCE((SELECT SUM(r.jumlah_tiket)
                                    FROM sizopi.RESERVASI r
                                    WHERE r.nama_fasilitas = %s
                                    AND r.tanggal_kunjungan = %s
                                    AND r.status = 'Terjadwal'), 0) as tiket_terpakai
                    FROM sizopi.FASILITAS f
                    WHERE f.nama = %s
                """, [nama_fasilitas, tanggal_kunjungan, nama_fasilitas])
                
                result = cursor.fetchone()
                
                if result:
                    kapasitas_max, tiket_terpakai = result
                    kapasitas_tersisa = kapasitas_max - tiket_terpakai
                    
                    if jumlah_tiket > kapasitas_tersisa:
                        messages.error(request, f"Jumlah tiket melebihi kapasitas tersisa. Kapasitas tersisa: {kapasitas_tersisa}")
                        return redirect('show_user_add_booking')
                    
                    # Simpan reservasi ke tabel RESERVASI baru
                    cursor.execute("""
                        INSERT INTO sizopi.RESERVASI (username_p, nama_fasilitas, tanggal_kunjungan, jumlah_tiket, status)
                        VALUES (%s, %s, %s, %s, %s)
                    """, [username, nama_fasilitas, tanggal_kunjungan, jumlah_tiket, 'Terjadwal'])
                    
                    messages.success(request, f"Reservasi {jenis_reservasi} berhasil dibuat!")
                else:
                    messages.error(request, "Fasilitas tidak ditemukan atau tidak terdaftar")
                    return redirect('show_user_add_booking')
            
            return redirect('show_user_booking')
        
        except Exception as e:
            import traceback
            print(f"ERROR: {str(e)}")
            print(traceback.format_exc())
            messages.error(request, f"Terjadi kesalahan: {str(e)}")
            return redirect('show_user_add_booking')
    
    # GET request - tampilkan form
    try:
        with connection.cursor() as cursor:
            # Debug session untuk memahami apa yang tersedia
            print(f"DEBUG - Session data: {dict(request.session)}")
            print(f"DEBUG - Username dari session: {username}")
            
            # Ambil daftar atraksi
            cursor.execute("""
                SELECT a.nama_atraksi, a.lokasi, f.kapasitas_max
                FROM sizopi.ATRAKSI a
                JOIN sizopi.FASILITAS f ON a.nama_atraksi = f.nama
                ORDER BY a.nama_atraksi
            """)
            
            atraksi_list = dictfetchall(cursor)
            
            # Debug - print lokasi untuk setiap atraksi
            print("DEBUG - Atraksi data:")
            for atraksi in atraksi_list:
                print(f"Atraksi: {atraksi['nama_atraksi']}, Lokasi: {atraksi['lokasi'] or 'None'}")
            
            # Ambil daftar wahana
            cursor.execute("""
                SELECT w.nama_wahana, w.peraturan, f.kapasitas_max
                FROM sizopi.WAHANA w
                JOIN sizopi.FASILITAS f ON w.nama_wahana = f.nama
                ORDER BY w.nama_wahana
            """)
            
            wahana_list = dictfetchall(cursor)
            
            # Debug - print peraturan untuk setiap wahana
            print("DEBUG - Wahana data:")
            for wahana in wahana_list:
                print(f"Wahana: {wahana['nama_wahana']}, Peraturan: {wahana['peraturan'] or 'None'}")
            
            # Cek apakah username ada di tabel PENGUNJUNG
            cursor.execute("SELECT username_p FROM sizopi.PENGUNJUNG WHERE username_p = %s", [username])
            pengunjung = cursor.fetchone()
            
            if pengunjung:
                print(f"DEBUG - Username {username} ditemukan di PENGUNJUNG")
                user_data = {'username': username}
            else:
                print(f"DEBUG - Username {username} TIDAK ditemukan di PENGUNJUNG")
                user_data = {'username': username or 'Pengunjung'}
            
            print(f"DEBUG - Final user data: {user_data}")
            
        context = {
            'atraksi_list': atraksi_list,
            'wahana_list': wahana_list,
            'today': today.strftime('%Y-%m-%d'),
            'title': 'Tambah Reservasi',
            'user': user_data,
            'session_username': username  # Tambahkan username session ke context
        }
        
        return render(request, 'user_add_booking.html', context)
    
    except Exception as e:
        import traceback
        print(f"ERROR: {str(e)}")
        print(traceback.format_exc())
        messages.error(request, f"Terjadi kesalahan: {str(e)}")
        return render(request, 'user_add_booking.html', {
            'atraksi_list': [],
            'wahana_list': [],
            'today': today.strftime('%Y-%m-%d'),
            'title': 'Tambah Reservasi',
            'user': {'username': username or 'Pengunjung'},
            'session_username': username
        })
        
        
@role_required('pengunjung')
def show_user_edit_booking(request):
    """
    Menampilkan form untuk mengedit booking (pembatalan)
    """
    # Ambil username dari session
    username = request.session.get('username', '')
    
    jenis_reservasi = request.GET.get('jenis')
    nama_fasilitas = request.GET.get('nama')
    tanggal_str = request.GET.get('tanggal')
    
    # Debug untuk memastikan parameter diterima dengan benar
    print(f"DEBUG - Edit booking: username={username}, jenis={jenis_reservasi}, fasilitas={nama_fasilitas}, tanggal={tanggal_str}")
    
    if request.method == 'POST':
        try:
            nama_fasilitas = request.POST.get('nama_fasilitas')
            tanggal_str = request.POST.get('tanggal_kunjungan')
            action = request.POST.get('action')
            
            # Debug POST data
            print(f"DEBUG - POST data: nama={nama_fasilitas}, tanggal={tanggal_str}, action={action}")
            
            # Validasi data yang diterima
            if not all([username, nama_fasilitas, tanggal_str]):
                messages.error(request, "Data tidak lengkap. Mohon isi semua field.")
                return redirect('show_user_booking')
            
            tanggal_kunjungan = datetime.strptime(tanggal_str, '%Y-%m-%d').date()
            
            with connection.cursor() as cursor:
                # Cek keberadaan reservasi
                cursor.execute("""
                    SELECT status, jumlah_tiket
                    FROM sizopi.RESERVASI
                    WHERE username_p = %s
                    AND nama_fasilitas = %s
                    AND tanggal_kunjungan = %s
                """, [username, nama_fasilitas, tanggal_kunjungan])
                
                reservasi = cursor.fetchone()
                
                if not reservasi:
                    messages.error(request, "Reservasi tidak ditemukan.")
                    return redirect('show_user_booking')
                
                current_status = reservasi[0]
                jumlah_tiket_asli = reservasi[1]
                
                if action == 'cancel':
                    # Batalkan reservasi jika belum dibatalkan
                    if current_status == 'Dibatalkan':
                        messages.info(request, "Reservasi ini sudah dibatalkan sebelumnya")
                        return redirect('show_user_booking')
                        
                    cursor.execute("""
                        UPDATE sizopi.RESERVASI
                        SET status = 'Dibatalkan'
                        WHERE username_p = %s
                        AND nama_fasilitas = %s
                        AND tanggal_kunjungan = %s
                    """, [username, nama_fasilitas, tanggal_kunjungan])
                    
                    if cursor.rowcount > 0:
                        messages.success(request, "Reservasi berhasil dibatalkan!")
                    else:
                        messages.error(request, "Gagal membatalkan reservasi")
                
                elif action == 'save':
                    # Update reservasi jika statusnya terjadwal
                    if current_status != 'Terjadwal':
                        messages.error(request, "Tidak dapat mengubah reservasi yang sudah dibatalkan.")
                        return redirect('show_user_booking')
                    
                    # Ambil data baru
                    tanggal_baru_str = request.POST.get('tanggal_kunjungan_new')
                    jumlah_tiket_baru = int(request.POST.get('jumlah_tiket', 1))
                    
                    # Validasi input
                    if jumlah_tiket_baru < 1:
                        messages.error(request, "Jumlah tiket harus minimal 1.")
                        # PERBAIKAN: Gunakan path URL lengkap, bukan nama view
                        return redirect(f'/user_edit_booking/?jenis={jenis_reservasi}&nama={nama_fasilitas}&tanggal={tanggal_str}')
                    
                    tanggal_baru = datetime.strptime(tanggal_baru_str, '%Y-%m-%d').date()
                    
                    # Validasi kapasitas jika ada perubahan
                    if tanggal_baru != tanggal_kunjungan or jumlah_tiket_baru != jumlah_tiket_asli:
                        # Ambil kapasitas maksimum fasilitas
                        cursor.execute("""
                            SELECT kapasitas_max
                            FROM sizopi.FASILITAS
                            WHERE nama = %s
                        """, [nama_fasilitas])
                        
                        kapasitas_result = cursor.fetchone()
                        if not kapasitas_result:
                            messages.error(request, "Fasilitas tidak ditemukan.")
                            return redirect('show_user_booking')
                        
                        kapasitas_max = kapasitas_result[0]
                        
                        # Hitung total tiket yang sudah dipesan untuk tanggal baru (kecuali reservasi ini)
                        cursor.execute("""
                            SELECT COALESCE(SUM(jumlah_tiket), 0) as total_tiket_terpakai
                            FROM sizopi.RESERVASI
                            WHERE nama_fasilitas = %s
                            AND tanggal_kunjungan = %s
                            AND status = 'Terjadwal'
                            AND NOT (username_p = %s AND tanggal_kunjungan = %s)
                        """, [nama_fasilitas, tanggal_baru, username, tanggal_kunjungan])
                        
                        tiket_terpakai = cursor.fetchone()[0]
                        kapasitas_tersisa = kapasitas_max - tiket_terpakai
                        
                        print(f"DEBUG - Kapasitas max: {kapasitas_max}, Terpakai: {tiket_terpakai}, Tersisa: {kapasitas_tersisa}, Diminta: {jumlah_tiket_baru}")
                        
                        if jumlah_tiket_baru > kapasitas_tersisa:
                            if tanggal_baru != tanggal_kunjungan:
                                messages.error(request, f"Jumlah tiket melebihi kapasitas tersisa untuk tanggal {tanggal_baru.strftime('%d %B %Y')}. Kapasitas tersisa: {kapasitas_tersisa} tiket.")
                            else:
                                messages.error(request, f"Jumlah tiket melebihi kapasitas tersisa. Kapasitas tersisa: {kapasitas_tersisa} tiket.")
                            
                            # PERBAIKAN: Gunakan path URL lengkap, bukan nama view
                            return redirect(f'/user_edit_booking/?jenis={jenis_reservasi}&nama={nama_fasilitas}&tanggal={tanggal_str}')
                    
                    # Update reservasi jika validasi berhasil
                    cursor.execute("""
                        UPDATE sizopi.RESERVASI
                        SET tanggal_kunjungan = %s,
                            jumlah_tiket = %s
                        WHERE username_p = %s
                        AND nama_fasilitas = %s
                        AND tanggal_kunjungan = %s
                    """, [tanggal_baru, jumlah_tiket_baru, username, nama_fasilitas, tanggal_kunjungan])
                    
                    if cursor.rowcount > 0:
                        if tanggal_baru != tanggal_kunjungan and jumlah_tiket_baru != jumlah_tiket_asli:
                            messages.success(request, f"Reservasi berhasil diperbarui! Tanggal diubah ke {tanggal_baru.strftime('%d %B %Y')} dan jumlah tiket diubah ke {jumlah_tiket_baru}.")
                        elif tanggal_baru != tanggal_kunjungan:
                            messages.success(request, f"Tanggal reservasi berhasil diubah ke {tanggal_baru.strftime('%d %B %Y')}.")
                        elif jumlah_tiket_baru != jumlah_tiket_asli:
                            messages.success(request, f"Jumlah tiket berhasil diubah ke {jumlah_tiket_baru}.")
                        else:
                            messages.success(request, "Reservasi berhasil diperbarui!")
                    else:
                        messages.error(request, "Gagal memperbarui reservasi")
            
            return redirect('show_user_booking')
        
        except ValueError as e:
            messages.error(request, "Format tanggal tidak valid. Mohon gunakan format yang benar.")
            return redirect('show_user_booking')
        except Exception as e:
            import traceback
            print(f"ERROR: {str(e)}")
            print(traceback.format_exc())
            messages.error(request, f"Terjadi kesalahan: {str(e)}")
            return redirect('show_user_booking')
    
    # GET request - tampilkan form
    try:
        with connection.cursor() as cursor:
            if jenis_reservasi and nama_fasilitas and tanggal_str:
                # Query untuk mendapatkan detail reservasi berdasarkan jenis
                if jenis_reservasi == 'atraksi':
                    cursor.execute("""
                        SELECT 
                            r.username_p, 
                            r.nama_fasilitas, 
                            r.tanggal_kunjungan, 
                            r.jumlah_tiket, 
                            r.status, 
                            a.lokasi,
                            f.kapasitas_max
                        FROM sizopi.RESERVASI r
                        JOIN sizopi.ATRAKSI a ON r.nama_fasilitas = a.nama_atraksi
                        JOIN sizopi.FASILITAS f ON r.nama_fasilitas = f.nama
                        WHERE r.username_p = %s
                        AND r.nama_fasilitas = %s
                        AND r.tanggal_kunjungan = %s
                    """, [username, nama_fasilitas, tanggal_str])
                else:  # wahana
                    cursor.execute("""
                        SELECT 
                            r.username_p, 
                            r.nama_fasilitas, 
                            r.tanggal_kunjungan, 
                            r.jumlah_tiket, 
                            r.status, 
                            w.peraturan,
                            f.kapasitas_max
                        FROM sizopi.RESERVASI r
                        JOIN sizopi.WAHANA w ON r.nama_fasilitas = w.nama_wahana
                        JOIN sizopi.FASILITAS f ON r.nama_fasilitas = f.nama
                        WHERE r.username_p = %s
                        AND r.nama_fasilitas = %s
                        AND r.tanggal_kunjungan = %s
                    """, [username, nama_fasilitas, tanggal_str])
                
                reservasi = cursor.fetchone()
                
                if reservasi:
                    # Hitung kapasitas tersisa untuk ditampilkan di template
                    cursor.execute("""
                        SELECT f.kapasitas_max,
                               COALESCE(
                                   (SELECT SUM(r.jumlah_tiket)
                                    FROM sizopi.RESERVASI r
                                    WHERE r.nama_fasilitas = %s
                                    AND r.tanggal_kunjungan = %s
                                    AND r.status = 'Terjadwal'
                                    AND NOT (r.username_p = %s AND r.tanggal_kunjungan = %s)
                                   ), 0
                               ) as tiket_terpakai
                        FROM sizopi.FASILITAS f
                        WHERE f.nama = %s
                    """, [nama_fasilitas, tanggal_str, username, tanggal_str, nama_fasilitas])
                    
                    kapasitas_result = cursor.fetchone()
                    kapasitas_max = kapasitas_result[0]
                    tiket_terpakai = kapasitas_result[1]
                    jumlah_tiket_saat_ini = reservasi[3]
                    
                    # Kapasitas tersisa tidak termasuk tiket pada reservasi ini
                    kapasitas_tersisa = kapasitas_max - tiket_terpakai
                    
                    context = {
                        'jenis_reservasi': jenis_reservasi,
                        'nama_fasilitas': reservasi[1],
                        'tanggal_kunjungan': reservasi[2],
                        'jumlah_tiket': jumlah_tiket_saat_ini,
                        'status': reservasi[4],
                        'kapasitas_max': kapasitas_max,
                        'kapasitas_tersisa': kapasitas_tersisa,  # Tambahkan ini ke context
                        'title': f'Edit Reservasi {jenis_reservasi.capitalize()}',
                        'username': username
                    }
                    
                    # Tambahkan lokasi atau peraturan sesuai jenis
                    if jenis_reservasi == 'atraksi':
                        context['lokasi'] = reservasi[5]
                    else:  # wahana
                        context['peraturan'] = reservasi[5]
                    
                    return render(request, 'user_edit_booking.html', context)
                else:
                    messages.error(request, "Reservasi tidak ditemukan")
                    return redirect('show_user_booking')
            
            else:
                messages.error(request, "Parameter tidak lengkap")
                return redirect('show_user_booking')
    
    except Exception as e:
        import traceback
        print(f"ERROR: {str(e)}")
        print(traceback.format_exc())
        messages.error(request, f"Terjadi kesalahan: {str(e)}")
        return redirect('show_user_booking')


   
@role_required('pengunjung')
def user_cancel_booking(request):
    """
    Menghapus (bukan hanya membatalkan) reservasi tiket user
    """
    if request.method == 'POST':
        try:
            # Ambil username dari session
            username = request.session.get('username', '')
            nama_fasilitas = request.POST.get('nama_fasilitas')
            tanggal_str = request.POST.get('tanggal_kunjungan')
            
            # Debug untuk melihat parameter yang diterima
            print(f"DEBUG - Delete booking: username={username}, fasilitas={nama_fasilitas}, tanggal={tanggal_str}")
            
            if not all([username, nama_fasilitas, tanggal_str]):
                messages.error(request, "Data tidak lengkap untuk menghapus reservasi.")
                return redirect('show_user_booking')
            
            tanggal_kunjungan = datetime.strptime(tanggal_str, '%Y-%m-%d').date()
            
            with connection.cursor() as cursor:
                # Cek apakah reservasi ada sebelum dihapus
                cursor.execute("""
                    SELECT status FROM sizopi.RESERVASI
                    WHERE username_p = %s
                    AND nama_fasilitas = %s
                    AND tanggal_kunjungan = %s
                """, [username, nama_fasilitas, tanggal_kunjungan])
                
                reservasi = cursor.fetchone()
                
                if not reservasi:
                    messages.error(request, "Reservasi tidak ditemukan.")
                    return redirect('show_user_booking')
                
                # Hapus permanen reservasi dari tabel RESERVASI
                cursor.execute("""
                    DELETE FROM sizopi.RESERVASI
                    WHERE username_p = %s
                    AND nama_fasilitas = %s
                    AND tanggal_kunjungan = %s
                """, [username, nama_fasilitas, tanggal_kunjungan])
                
                if cursor.rowcount > 0:
                    messages.success(request, "Reservasi berhasil dihapus permanen!")
                else:
                    messages.error(request, "Gagal menghapus reservasi.")
            
            return redirect('show_user_booking')
            
        except Exception as e:
            import traceback
            print(f"ERROR: {str(e)}")
            print(traceback.format_exc())
            messages.error(request, f"Terjadi kesalahan: {str(e)}")
            return redirect('show_user_booking')
    
    # Redirect jika bukan POST request
    return redirect('show_user_booking')


def check_availability(request):
    """
    API untuk memeriksa ketersediaan tiket
    """
    jenis = request.GET.get('jenis')
    nama = request.GET.get('nama')
    tanggal_str = request.GET.get('tanggal')
    
    try:
        tanggal = datetime.strptime(tanggal_str, '%Y-%m-%d').date()
        
        with connection.cursor() as cursor:
            # Query untuk memeriksa ketersediaan fasilitas di tabel RESERVASI baru
            cursor.execute("""
                SELECT f.kapasitas_max,
                       COALESCE((SELECT SUM(r.jumlah_tiket)
                                FROM sizopi.RESERVASI r
                                WHERE r.nama_fasilitas = %s
                                AND r.tanggal_kunjungan = %s
                                AND r.status = 'Terjadwal'), 0) as tiket_terpakai
                FROM sizopi.FASILITAS f
                WHERE f.nama = %s
            """, [nama, tanggal, nama])
            
            result = cursor.fetchone()
            
            if result:
                kapasitas_max, tiket_terpakai = result
                kapasitas_tersisa = kapasitas_max - tiket_terpakai
                
                return JsonResponse({
                    'kapasitas_max': kapasitas_max,
                    'tiket_terpakai': tiket_terpakai,
                    'kapasitas_tersisa': kapasitas_tersisa,
                    'penuh': kapasitas_tersisa <= 0
                })
            else:
                return JsonResponse({'error': 'Fasilitas tidak ditemukan'}, status=404)
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)