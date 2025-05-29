from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection
from django.views.decorators.http import require_http_methods
import hashlib
from django.urls import reverse
from utils.decorators import role_required

@role_required('dokter')
def pengaturan_profil_dh(request):
    username = request.user.username
    spesialisasi_list = ["Mamalia Besar", "Reptil", "Burung Eksotis", "Primata", "Lainnya"]

    if request.method == 'POST':
        email = request.POST.get('email')
        nama_depan = request.POST.get('nama_depan')
        nama_tengah = request.POST.get('nama_tengah')
        nama_belakang = request.POST.get('nama_belakang')
        no_telepon = request.POST.get('no_telepon')
        spesialisasi_terpilih = request.POST.getlist('spesialisasi')

        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE sizopi.pengguna
                    SET email = %s,
                        nama_depan = %s,
                        nama_tengah = %s,
                        nama_belakang = %s,
                        no_telepon = %s
                    WHERE username = %s
                """, [email, nama_depan, nama_tengah, nama_belakang, no_telepon, username])

                cursor.execute("""
                    DELETE FROM sizopi.spesialisasi WHERE username_sh = %s
                """, [username])

                for sp in spesialisasi_terpilih:
                    cursor.execute("""
                        INSERT INTO sizopi.spesialisasi (username_sh, nama_spesialisasi)
                        VALUES (%s, %s)
                    """, [username, sp])

            messages.success(request, "Profil berhasil diperbarui.")
        except Exception as e:
            messages.error(request, f"Gagal memperbarui profil: {str(e)}")

        return redirect(reverse('pengaturan_profil_dh'))

    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM sizopi.dokter_hewan WHERE username_dh = %s", [username])
        row = cursor.fetchone()
        is_dokter = row and row[0] > 0

        cursor.execute("""
            SELECT p.username, p.email, p.nama_depan, p.nama_tengah,
                   p.nama_belakang, p.no_telepon, d.no_str
            FROM sizopi.pengguna p
            JOIN sizopi.dokter_hewan d ON p.username = d.username_dh
            WHERE p.username = %s
        """, [username])
        profil_row = cursor.fetchone()

        cursor.execute("""
            SELECT nama_spesialisasi 
            FROM sizopi.spesialisasi 
            WHERE username_sh = %s
        """, [username])
        spesialisasi = [row[0] for row in cursor.fetchall()]

    user_data = {
        'username': profil_row[0],
        'email': profil_row[1],
        'nama_depan': profil_row[2],
        'nama_tengah': profil_row[3],
        'nama_belakang': profil_row[4],
        'no_telepon': profil_row[5],
        'no_str': profil_row[6],
        'spesialisasi': spesialisasi
    }

    return render(request, 'pengaturan_profil_dh.html', {
        'user_data': user_data,
        'is_dokter': is_dokter,
        'spesialisasi_list': spesialisasi_list,
    })

def ubah_password(request):
    if request.method == 'POST':
        username = request.user.username
        password_lama = request.POST.get('password_lama')
        password_baru = request.POST.get('password_baru')
        konfirmasi = request.POST.get('konfirmasi_password_baru')

        if password_baru != konfirmasi:
            messages.error(request, "Konfirmasi password tidak cocok.")
            return redirect(reverse('pengaturan_profil_dh'))

        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT password FROM sizopi.pengguna WHERE username = %s", [username])
                row = cursor.fetchone()

                if not row or password_lama != row[0]:
                    messages.error(request, "Password lama salah.")
                    return redirect(reverse('pengaturan_profil_dh'))

                cursor.execute("""
                    UPDATE sizopi.pengguna SET password = %s WHERE username = %s
                """, [password_baru, username])

            messages.success(request, "Password berhasil diubah.")
        except Exception as e:
            messages.error(request, f"Gagal mengubah password: {str(e)}")

        return redirect(reverse('pengaturan_profil_dh'))
    
@role_required('penjaga_hewan')
def pengaturan_profil_penjaga_hewan(request):
    username = request.user.username

    if request.method == 'POST':
        email = request.POST.get('email')
        nama_depan = request.POST.get('nama_depan')
        nama_tengah = request.POST.get('nama_tengah')
        nama_belakang = request.POST.get('nama_belakang')
        no_telepon = request.POST.get('no_telepon')

        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE sizopi.pengguna
                    SET email = %s,
                        nama_depan = %s,
                        nama_tengah = %s,
                        nama_belakang = %s,
                        no_telepon = %s
                    WHERE username = %s
                """, [email, nama_depan, nama_tengah, nama_belakang, no_telepon, username])
            messages.success(request, "Profil berhasil diperbarui.")
        except Exception as e:
            messages.error(request, f"Gagal memperbarui profil: {str(e)}")
        return redirect(reverse('pengaturan_profil_penjaga_hewan'))

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT p.username, p.email, p.nama_depan, p.nama_tengah,
                   p.nama_belakang, p.no_telepon, jh.id_staf
            FROM sizopi.pengguna p
            JOIN sizopi.penjaga_hewan jh ON p.username = jh.username_jh
            WHERE p.username = %s
        """, [username])
        row = cursor.fetchone()

    user_data = {
        'username': row[0],
        'email': row[1],
        'nama_depan': row[2],
        'nama_tengah': row[3],
        'nama_belakang': row[4],
        'no_telepon': row[5],
        'id_staf': row[6],
    }

    return render(request, 'pengaturan_profil_penjaga_hewan.html', {
        'user_data': user_data,
    })


@role_required('penjaga_hewan')
def ubah_password_penjaga_hewan(request):
    if request.method == 'POST':
        username = request.user.username
        password_lama = request.POST.get('password_lama')
        password_baru = request.POST.get('password_baru')
        konfirmasi = request.POST.get('konfirmasi_password_baru')

        if password_baru != konfirmasi:
            messages.error(request, "Konfirmasi password tidak cocok.")
            return redirect(reverse('pengaturan_profil_penjaga_hewan'))

        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT password FROM sizopi.pengguna WHERE username = %s", [username])
                row = cursor.fetchone()

                if not row or password_lama != row[0]:
                    messages.error(request, "Password lama salah.")
                    return redirect(reverse('pengaturan_profil_penjaga_hewan'))

                cursor.execute("""
                    UPDATE sizopi.pengguna SET password = %s WHERE username = %s
                """, [password_baru, username])

            messages.success(request, "Password berhasil diubah.")
        except Exception as e:
            messages.error(request, f"Gagal mengubah password: {str(e)}")

        return redirect(reverse('pengaturan_profil_penjaga_hewan'))

@role_required('staff')
def pengaturan_profil_staff(request):
    username = request.user.username

    if request.method == 'POST':
        email = request.POST.get('email')
        nama_depan = request.POST.get('nama_depan')
        nama_tengah = request.POST.get('nama_tengah')
        nama_belakang = request.POST.get('nama_belakang')
        no_telepon = request.POST.get('no_telepon')

        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE sizopi.pengguna
                    SET email = %s,
                        nama_depan = %s,
                        nama_tengah = %s,
                        nama_belakang = %s,
                        no_telepon = %s
                    WHERE username = %s
                """, [email, nama_depan, nama_tengah, nama_belakang, no_telepon, username])
            messages.success(request, "Profil berhasil diperbarui.")
        except Exception as e:
            messages.error(request, f"Gagal memperbarui profil: {str(e)}")
        return redirect(reverse('pengaturan_profil_staff'))

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT p.username, p.email, p.nama_depan, p.nama_tengah,
                   p.nama_belakang, p.no_telepon, s.id_staf
            FROM sizopi.pengguna p
            JOIN sizopi.staf_admin s ON p.username = s.username_sa
            WHERE p.username = %s
        """, [username])
        row = cursor.fetchone()

    user_data = {
        'username': row[0],
        'email': row[1],
        'nama_depan': row[2],
        'nama_tengah': row[3],
        'nama_belakang': row[4],
        'no_telepon': row[5],
        'id_staf': row[6],
    }

    return render(request, 'pengaturan_profil_staff.html', {
        'user_data': user_data,
        'role': 'staff'
    })


@role_required('staff')
def ubah_password_staff(request):
    if request.method == 'POST':
        username = request.user.username
        password_lama = request.POST.get('password_lama')
        password_baru = request.POST.get('password_baru')
        konfirmasi = request.POST.get('konfirmasi_password_baru')

        if password_baru != konfirmasi:
            messages.error(request, "Konfirmasi password tidak cocok.")
            return redirect(reverse('pengaturan_profil_staff'))

        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT password FROM sizopi.pengguna WHERE username = %s", [username])
                row = cursor.fetchone()

                if not row or password_lama != row[0]:
                    messages.error(request, "Password lama salah.")
                    return redirect(reverse('pengaturan_profil_staff'))

                cursor.execute("""
                    UPDATE sizopi.pengguna SET password = %s WHERE username = %s
                """, [password_baru, username])

            messages.success(request, "Password berhasil diubah.")
        except Exception as e:
            messages.error(request, f"Gagal mengubah password: {str(e)}")

        return redirect(reverse('pengaturan_profil_staff'))
    
    # Jika metode GET, redirect saja ke halaman profil staff
    # karena password akan diubah melalui modal di halaman tersebut
    else:
        return redirect(reverse('pengaturan_profil_staff'))
    
    
    

@role_required('pelatih_pertunjukan')
def pengaturan_profil_pelatih(request):
    username = request.user.username

    if request.method == 'POST':
        email = request.POST.get('email')
        nama_depan = request.POST.get('nama_depan')
        nama_tengah = request.POST.get('nama_tengah')
        nama_belakang = request.POST.get('nama_belakang')
        no_telepon = request.POST.get('no_telepon')

        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE sizopi.pengguna
                    SET email = %s,
                        nama_depan = %s,
                        nama_tengah = %s,
                        nama_belakang = %s,
                        no_telepon = %s
                    WHERE username = %s
                """, [email, nama_depan, nama_tengah, nama_belakang, no_telepon, username])
            messages.success(request, "Profil berhasil diperbarui.")
        except Exception as e:
            messages.error(request, f"Gagal memperbarui profil: {str(e)}")
        return redirect(reverse('pengaturan_profil_pelatih'))

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT p.username, p.email, p.nama_depan, p.nama_tengah,
                   p.nama_belakang, p.no_telepon, ph.id_staf
            FROM sizopi.pengguna p
            JOIN sizopi.pelatih_hewan ph ON p.username = ph.username_lh
            WHERE p.username = %s
        """, [username])
        row = cursor.fetchone()

    user_data = {
        'username': row[0],
        'email': row[1],
        'nama_depan': row[2],
        'nama_tengah': row[3],
        'nama_belakang': row[4],
        'no_telepon': row[5],
        'id_pelatih': row[6],
    }

    return render(request, 'pengaturan_profil_pelatih.html', {
        'user_data': user_data,
        'role': 'pelatih_hewan'
    })


@role_required('pelatih_pertunjukan')
def ubah_password_pelatih(request):
    if request.method == 'POST':
        username = request.user.username
        password_lama = request.POST.get('password_lama')
        password_baru = request.POST.get('password_baru')
        konfirmasi = request.POST.get('konfirmasi_password_baru')

        if password_baru != konfirmasi:
            messages.error(request, "Konfirmasi password tidak cocok.")
            return redirect(reverse('pengaturan_profil_pelatih'))

        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT password FROM sizopi.pengguna WHERE username = %s", [username])
                row = cursor.fetchone()

                if not row or password_lama != row[0]:
                    messages.error(request, "Password lama salah.")
                    return redirect(reverse('pengaturan_profil_pelatih'))

                cursor.execute("""
                    UPDATE sizopi.pengguna SET password = %s WHERE username = %s
                """, [password_baru, username])

            messages.success(request, "Password berhasil diubah.")
        except Exception as e:
            messages.error(request, f"Gagal mengubah password: {str(e)}")

        return redirect(reverse('pengaturan_profil_pelatih'))
    
    else:
        return redirect(reverse('pengaturan_profil_pelatih'))
    

@role_required('pengunjung')
def pengaturan_profil_pengunjung(request):
    username = request.user.username

    if request.method == 'POST':
        email = request.POST.get('email')
        nama_depan = request.POST.get('nama_depan')
        nama_tengah = request.POST.get('nama_tengah')
        nama_belakang = request.POST.get('nama_belakang')
        no_telepon = request.POST.get('no_telepon')
        alamat = request.POST.get('alamat')
        tgl_lahir = request.POST.get('tgl_lahir')

        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE sizopi.pengguna
                    SET email = %s, nama_depan = %s, nama_tengah = %s,
                        nama_belakang = %s, no_telepon = %s
                    WHERE username = %s
                """, [email, nama_depan, nama_tengah, nama_belakang, no_telepon, username])

                cursor.execute("""
                    UPDATE sizopi.pengunjung
                    SET alamat = %s, tgl_lahir = %s
                    WHERE username_p = %s
                """, [alamat, tgl_lahir, username])

            messages.success(request, "Profil berhasil diperbarui.")
        except Exception as e:
            messages.error(request, f"Gagal memperbarui profil: {str(e)}")

        return redirect(reverse('pengaturan_profil_pengunjung'))

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT p.username, p.email, p.nama_depan, p.nama_tengah,
                   p.nama_belakang, p.no_telepon, pg.alamat, pg.tgl_lahir
            FROM sizopi.pengguna p
            JOIN sizopi.pengunjung pg ON p.username = pg.username_p
            WHERE p.username = %s
        """, [username])
        row = cursor.fetchone()

    user_data = {
        'username': row[0],
        'email': row[1],
        'nama_depan': row[2],
        'nama_tengah': row[3],
        'nama_belakang': row[4],
        'no_telepon': row[5],
        'alamat': row[6],
        'tgl_lahir': row[7].strftime('%Y-%m-%d') if row[7] else ''
    }

    return render(request, 'pengaturan_profil_pengunjung.html', {
        'user_data': user_data
    })

@role_required('pengunjung')
def ubah_password_pengunjung(request):
    if request.method == 'POST':
        username = request.user.username
        password_lama = request.POST.get('password_lama')
        password_baru = request.POST.get('password_baru')
        konfirmasi = request.POST.get('konfirmasi_password_baru')

        if password_baru != konfirmasi:
            messages.error(request, "Konfirmasi password tidak cocok.")
            return redirect(reverse('pengaturan_profil_pengunjung'))

        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT password FROM sizopi.pengguna WHERE username = %s", [username])
                row = cursor.fetchone()

                if not row or password_lama != row[0]:
                    messages.error(request, "Password lama salah.")
                    return redirect(reverse('pengaturan_profil_pengunjung'))

                cursor.execute("""
                    UPDATE sizopi.pengguna SET password = %s WHERE username = %s
                """, [password_baru, username])

            messages.success(request, "Password berhasil diubah.")
        except Exception as e:
            messages.error(request, f"Gagal mengubah password: {str(e)}")

        return redirect(reverse('pengaturan_profil_pengunjung'))