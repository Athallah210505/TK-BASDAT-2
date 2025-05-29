from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection
from django.views.decorators.http import require_http_methods
import hashlib
from django.urls import reverse
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.hashers import check_password, make_password
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


@role_required('dokter')
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
                # Ambil password lama dari tabel PENGGUNA
                cursor.execute("SELECT password FROM sizopi.pengguna WHERE username = %s", [username])
                row = cursor.fetchone()

                if not row or password_lama != row[0]:
                    messages.error(request, "Password lama salah.")
                    return redirect(reverse('pengaturan_profil_dh'))

                # Update password baru (tanpa hash, sesuai dengan struktur kamu sekarang)
                cursor.execute("""
                    UPDATE sizopi.pengguna SET password = %s WHERE username = %s
                """, [password_baru, username])

            messages.success(request, "Password berhasil diubah.")
        except Exception as e:
            messages.error(request, f"Gagal mengubah password: {str(e)}")

        return redirect(reverse('pengaturan_profil_dh'))
    
# Common profile functions
def get_common_context(request):
    """Get common context for all profile views"""
    if 'username' not in request.session:
        messages.error(request, 'Silakan login terlebih dahulu.')
        return redirect('login')
    
    username = request.session['username']
    role = request.session['role']
    
    return {
        'username': username,
        'role': role,
        'is_visitor': role in ['pengunjung', 'pengunjung_adopter'],
        'is_vet': role == 'dokter',
        'is_staff': role == 'staff',
        'is_penjaga': role == 'penjaga_hewan',
        'is_pelatih': role == 'pelatih_pertunjukan',
    }

def get_user_data(cursor, username, role):
    """Get user data based on role"""
    user_data = {}
    
    if role == 'pengunjung' or role == 'pengunjung_adopter':
        cursor.execute("""
            SELECT username_p, email_p, no_telp, nama_depan, nama_tengah, nama_belakang, 
                   tanggal_lahir, alamat
            FROM sizopi.pengunjung 
            WHERE username_p = %s
        """, [username])
        result = cursor.fetchone()
        
        if result:
            user_data = {
                'username': result[0],
                'email': result[1],
                'phone': result[2],
                'first_name': result[3],
                'middle_name': result[4],
                'last_name': result[5],
                'birth_date': result[6],
                'address': result[7]
            }
    
    elif role == 'dokter':
        try:
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema = 'sizopi' 
                AND table_name = 'dokter_hewan'
            """)
            columns = [row[0] for row in cursor.fetchall()]
            
            base_query = "SELECT username_dh"
            fields = ['username']
            
            if 'email' in columns:
                base_query += ", email"
                fields.append('email')
            elif 'email_dh' in columns:
                base_query += ", email_dh"
                fields.append('email')
            else:
                base_query += ", NULL as email"
                fields.append('email')
            
            if 'no_telp' in columns:
                base_query += ", no_telp"
                fields.append('phone')
            else:
                base_query += ", NULL as no_telp"
                fields.append('phone')
            
            if 'nama_depan' in columns:
                base_query += ", nama_depan"
                fields.append('first_name')
            else:
                base_query += ", NULL as nama_depan"
                fields.append('first_name')
            
            if 'nama_tengah' in columns:
                base_query += ", nama_tengah"
                fields.append('middle_name')
            else:
                base_query += ", NULL as nama_tengah"
                fields.append('middle_name')
            
            if 'nama_belakang' in columns:
                base_query += ", nama_belakang"
                fields.append('last_name')
            else:
                base_query += ", NULL as nama_belakang"
                fields.append('last_name')
            
            if 'no_sertifikasi_profesional' in columns:
                base_query += ", no_sertifikasi_profesional"
                fields.append('certification_number')
            else:
                base_query += ", NULL as no_sertifikasi_profesional"
                fields.append('certification_number')
            
            base_query += " FROM sizopi.dokter_hewan WHERE username_dh = %s"
            
            cursor.execute(base_query, [username])
            result = cursor.fetchone()
            
            if result:
                user_data = {}
                for i, field in enumerate(fields):
                    user_data[field] = result[i]
                
                try:
                    cursor.execute("""
                        SELECT spesialisasi FROM sizopi.spesialisasi_dokter_hewan 
                        WHERE username_dh = %s
                    """, [username])
                    specializations = [row[0] for row in cursor.fetchall()]
                    user_data['specializations'] = specializations
                except:
                    user_data['specializations'] = []
                    
        except Exception as e:
            cursor.execute("""
                SELECT username_dh FROM sizopi.dokter_hewan WHERE username_dh = %s
            """, [username])
            result = cursor.fetchone()
            if result:
                user_data = {
                    'username': result[0],
                    'email': '',
                    'phone': '',
                    'first_name': '',
                    'middle_name': '',
                    'last_name': '',
                    'certification_number': '',
                    'specializations': []
                }
    
    elif role == 'staff':
        cursor.execute("""
            SELECT username_sa, p.email_sa, no_telp, nama_depan, nama_tengah, nama_belakang
            FROM sizopi.staf_admin, sizopi.pengguna p
            WHERE username_sa = %s
        """, [username])
        result = cursor.fetchone()
        
        if result:
            user_data = {
                'username': result[0],
                'email': result[1],
                'phone': result[2],
                'first_name': result[3],
                'middle_name': result[4],
                'last_name': result[5],
                'staff_id': f"STAFF-{username.upper()}"
            }
    
    elif role == 'penjaga_hewan':
        cursor.execute("""
            SELECT username_jh, email_jh, no_telp, nama_depan, nama_tengah, nama_belakang
            FROM sizopi.penjaga_hewan 
            WHERE username_jh = %s
        """, [username])
        result = cursor.fetchone()
        
        if result:
            user_data = {
                'username': result[0],
                'email': result[1],
                'phone': result[2],
                'first_name': result[3],
                'middle_name': result[4],
                'last_name': result[5]
            }
    
    elif role == 'pelatih_pertunjukan':
        cursor.execute("""
            SELECT username_lh, email_lh, no_telp, nama_depan, nama_tengah, nama_belakang
            FROM sizopi.pelatih_hewan 
            WHERE username_lh = %s
        """, [username])
        result = cursor.fetchone()
        
        if result:
            user_data = {
                'username': result[0],
                'email': result[1],
                'phone': result[2],
                'first_name': result[3],
                'middle_name': result[4],
                'last_name': result[5]
            }
    
    return user_data

# Profile views
def profile_settings(request):
    """Main profile settings page that redirects to specific profile"""
    common_context = get_common_context(request)
    if isinstance(common_context, dict):
        role = common_context['role']
        if role in ['pengunjung', 'pengunjung_adopter']:
            return redirect('visitor_profile')
        elif role == 'dokter':
            return redirect('vet_profile')
        elif role == 'staff':
            return redirect('staff_profile')
        elif role in ['penjaga_hewan', 'pelatih_pertunjukan']:
            return redirect('visitor_profile')  # or appropriate redirect
    return common_context

def visitor_profile(request):
    """Visitor profile view"""
    common_context = get_common_context(request)
    if not isinstance(common_context, dict):
        return common_context
    
    with connection.cursor() as cursor:
        user_data = get_user_data(cursor, common_context['username'], common_context['role'])
    
    context = {
        **common_context,
        'user_data': user_data
    }
    return render(request, 'visitor_profile.html', context)

def vet_profile(request):
    """Veterinarian profile view"""
    common_context = get_common_context(request)
    if not isinstance(common_context, dict):
        return common_context
    
    with connection.cursor() as cursor:
        user_data = get_user_data(cursor, common_context['username'], common_context['role'])
    
    context = {
        **common_context,
        'user_data': user_data
    }
    return render(request, 'vet_profile.html', context)

def staff_profile(request):
    """Staff profile view"""
    common_context = get_common_context(request)
    if not isinstance(common_context, dict):
        return common_context
    
    with connection.cursor() as cursor:
        user_data = get_user_data(cursor, common_context['username'], common_context['role'])
    
    context = {
        **common_context,
        'user_data': user_data
    }
    return render(request, 'staff_profile.html', context)

# Update profile views
def update_visitor_profile(request):
    """Update visitor profile"""
    return update_profile(request, ['pengunjung', 'pengunjung_adopter'])

def update_vet_profile(request):
    """Update vet profile"""
    return update_profile(request, ['dokter'])

def update_staff_profile(request):
    """Update staff profile"""
    return update_profile(request, ['staff'])

def update_profile(request, allowed_roles):
    """Common update profile function"""
    common_context = get_common_context(request)
    if not isinstance(common_context, dict):
        return common_context
    
    if common_context['role'] not in allowed_roles:
        messages.error(request, 'Anda tidak memiliki akses ke halaman ini.')
        return redirect('profile_settings')
    
    username = common_context['username']
    role = common_context['role']
    
    try:
        with connection.cursor() as cursor:
            if role in ['pengunjung', 'pengunjung_adopter']:
                cursor.execute("""
                    UPDATE sizopi.pengunjung 
                    SET email_p = %s, no_telp = %s, nama_depan = %s, 
                        nama_tengah = %s, nama_belakang = %s, tanggal_lahir = %s, alamat = %s
                    WHERE username_p = %s
                """, [
                    request.POST.get('email'),
                    request.POST.get('phone'),
                    request.POST.get('first_name'),
                    request.POST.get('middle_name') or None,
                    request.POST.get('last_name'),
                    request.POST.get('birth_date') or None,
                    request.POST.get('address'),
                    username
                ])
            
            elif role == 'dokter':
                try:
                    cursor.execute("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_schema = 'sizopi' 
                        AND table_name = 'dokter_hewan'
                    """)
                    columns = [row[0] for row in cursor.fetchall()]
                    
                    update_fields = []
                    update_values = []
                    
                    if 'email' in columns or 'email_dh' in columns:
                        email_col = 'email' if 'email' in columns else 'email_dh'
                        update_fields.append(f"{email_col} = %s")
                        update_values.append(request.POST.get('email'))
                    
                    if 'no_telp' in columns:
                        update_fields.append("no_telp = %s")
                        update_values.append(request.POST.get('phone'))
                    
                    if 'nama_depan' in columns:
                        update_fields.append("nama_depan = %s")
                        update_values.append(request.POST.get('first_name'))
                    
                    if 'nama_tengah' in columns:
                        update_fields.append("nama_tengah = %s")
                        update_values.append(request.POST.get('middle_name') or None)
                    
                    if 'nama_belakang' in columns:
                        update_fields.append("nama_belakang = %s")
                        update_values.append(request.POST.get('last_name'))
                    
                    if update_fields:
                        update_values.append(username)
                        update_query = f"""
                            UPDATE sizopi.dokter_hewan 
                            SET {', '.join(update_fields)}
                            WHERE username_dh = %s
                        """
                        cursor.execute(update_query, update_values)
                    
                    specializations = request.POST.getlist('specialization')
                    if specializations:
                        try:
                            cursor.execute("""
                                DELETE FROM sizopi.spesialisasi_dokter_hewan 
                                WHERE username_dh = %s
                            """, [username])
                            
                            for spec in specializations:
                                if spec == 'other' and request.POST.get('other_specialization'):
                                    spec_value = request.POST.get('other_specialization')
                                else:
                                    spec_value = spec
                                
                                cursor.execute("""
                                    INSERT INTO sizopi.spesialisasi_dokter_hewan (username_dh, spesialisasi)
                                    VALUES (%s, %s)
                                """, [username, spec_value])
                        except:
                            pass
                            
                except Exception as e:
                    pass
            
            elif role == 'staff':
                cursor.execute("""
                    UPDATE sizopi.staf_admin 
                    SET email_sa = %s, no_telp = %s, nama_depan = %s, 
                        nama_tengah = %s, nama_belakang = %s
                    WHERE username_sa = %s
                """, [
                    request.POST.get('email'),
                    request.POST.get('phone'),
                    request.POST.get('first_name'),
                    request.POST.get('middle_name') or None,
                    request.POST.get('last_name'),
                    username
                ])
        
        messages.success(request, 'Profil berhasil diperbarui!')
        
    except Exception as e:
        messages.error(request, f'Terjadi kesalahan saat memperbarui profil: {str(e)}')
    
    if role in ['pengunjung', 'pengunjung_adopter']:
        return redirect('visitor_profile')
    elif role == 'dokter':
        return redirect('vet_profile')
    elif role == 'staff':
        return redirect('staff_profile')

# Password change
def password_change(request):
    """Password change view"""
    common_context = get_common_context(request)
    if not isinstance(common_context, dict):
        return common_context
    
    if request.method == 'POST':
        return change_password(request)
    
    context = {
        **common_context
    }
    return render(request, 'password_change.html', context)

@require_http_methods(["POST"])
def change_password(request):
    """Handle password change"""
    common_context = get_common_context(request)
    if not isinstance(common_context, dict):
        return common_context
    
    username = common_context['username']
    old_password = request.POST.get('old_password')
    new_password = request.POST.get('new_password')
    confirm_password = request.POST.get('confirm_password')
    
    if not all([old_password, new_password, confirm_password]):
        messages.error(request, 'Semua field password harus diisi.')
        return redirect('password_change')
    
    if new_password != confirm_password:
        messages.error(request, 'Password baru dan konfirmasi password tidak cocok.')
        return redirect('password_change')
    
    if len(new_password) < 8:
        messages.error(request, 'Password baru harus minimal 8 karakter.')
        return redirect('password_change')
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT sizopi.cek_kredensial(%s::text, %s::text)", [username, old_password])
            valid = cursor.fetchone()[0]
            
            if not valid:
                messages.error(request, 'Password lama tidak benar.')
                return redirect('password_change')
            
            new_password_hash = hashlib.sha256(new_password.encode()).hexdigest()
            
            cursor.execute("""
                UPDATE sizopi.kredensial 
                SET password = %s 
                WHERE username = %s
            """, [new_password_hash, username])
            
            if cursor.rowcount > 0:
                messages.success(request, 'Password berhasil diubah!')
            else:
                messages.error(request, 'Gagal mengubah password.')
        
    except Exception as e:
        messages.error(request, f'Terjadi kesalahan saat mengubah password: {str(e)}')
    
    return redirect('password_change')

