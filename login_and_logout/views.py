from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection

def login_view(request):
    if request.user.is_authenticated:
        return redirect('show_main')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT cek_kredensial(%s, %s)", [username, password])
            valid = cursor.fetchone()[0]

        if valid:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT CASE
                        WHEN EXISTS(SELECT 1 FROM sizopi.pengunjung WHERE username_p = %s) THEN 'pengunjung'
                        WHEN EXISTS(SELECT 1 FROM sizopi.dokter_hewan WHERE username_dh = %s) THEN 'dokter'
                        WHEN EXISTS(SELECT 1 FROM sizopi.staf_admin WHERE username_sa = %s) THEN 'staff'
                        WHEN EXISTS(SELECT 1 FROM sizopi.penjaga_hewan WHERE username_jh = %s) THEN 'pjh'
                        WHEN EXISTS(SELECT 1 FROM sizopi.pelatih_hewan WHERE username_lh = %s) THEN 'plp'
                        ELSE 'unknown'
                    END
                """, [username]*5)
                role = cursor.fetchone()[0]

            # Simpan ke session (opsional)
            request.session['username'] = username
            request.session['role'] = role

            # Redirect ke dashboard yang sesuai
            if role == 'pengunjung':
                return redirect('pengunjung_dashboard')
            elif role == 'dokter':
                return redirect('dokter_hewan_dashboard')
            elif role == 'staff':
                return redirect('show_staff_dashboard')
            elif role == 'pjh':
                return redirect('penjaga_hewan_dashboard')
            elif role == 'plp':
                return redirect('pelatih_pertunjukan_dashboard')
            else:
                messages.error(request, "Role tidak dikenali.")
                return redirect('login')
        else:
            messages.error(request, "Username atau password salah, silakan coba lagi.")
            return redirect('login')

    return render(request, 'login.html')

def logout_view(request):
    request.session.flush()  
    messages.info(request, 'Anda telah logout.')
    return redirect('login')
