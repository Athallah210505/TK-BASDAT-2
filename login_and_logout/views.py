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
            cursor.execute("SELECT sizopi.cek_kredensial(%s::text, %s::text)", [username, password])
            valid = cursor.fetchone()[0]

        if valid:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT CASE
                        WHEN EXISTS(SELECT 1 FROM sizopi.adopter WHERE username_adopter = %s) THEN 'pengunjung_adopter'
                        WHEN EXISTS(SELECT 1 FROM sizopi.pengunjung WHERE username_p = %s) THEN 'pengunjung'
                        WHEN EXISTS(SELECT 1 FROM sizopi.dokter_hewan WHERE username_dh = %s) THEN 'dokter'
                        WHEN EXISTS(SELECT 1 FROM sizopi.staf_admin WHERE username_sa = %s) THEN 'staff'
                        WHEN EXISTS(SELECT 1 FROM sizopi.penjaga_hewan WHERE username_jh = %s) THEN 'penjaga_hewan'
                        WHEN EXISTS(SELECT 1 FROM sizopi.pelatih_hewan WHERE username_lh = %s) THEN 'pelatih_pertunjukan'
                        ELSE 'unknown'
                    END
                """, [username]*6)
                role = cursor.fetchone()[0]

            request.session['username'] = username
            request.session['role'] = role

            if role == 'pengunjung':
                return redirect('pengunjung_dashboard')
            elif role == 'dokter':
                return redirect('dokter_hewan_dashboard')
            elif role == 'staff':
                return redirect('show_staff_dashboard')
            elif role == 'penjaga_hewan':
                return redirect('penjaga_hewan_dashboard')
            elif role == 'pelatih_pertunjukan':
                return redirect('pelatih_pertunjukan_dashboard')
            elif role == 'pengunjung_adopter':
                return redirect('pengunjung_adopter_dashboard')
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
