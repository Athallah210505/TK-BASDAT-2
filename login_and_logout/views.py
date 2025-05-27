from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection
from django.db.utils import DatabaseError
from psycopg2 import Error as Psycopg2Error

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT sizopi.cek_kredensial(%s::text, %s::text)", [username, password])

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

            redirect_map = {
                'pengunjung': 'pengunjung_dashboard',
                'dokter': 'dokter_hewan_dashboard',
                'staff': 'show_staff_dashboard',
                'penjaga_hewan': 'penjaga_hewan_dashboard',
                'pelatih_pertunjukan': 'pelatih_pertunjukan_dashboard',
                'pengunjung_adopter': 'pengunjung_adopter_dashboard',
            }

            if role in redirect_map:
                return redirect(redirect_map[role])
            else:
                messages.error(request, "Role tidak dikenali.")
                return redirect('login')

        except DatabaseError as e:
            error_message = str(e).splitlines()[0].replace('ERROR:', '').strip()
            messages.error(request, error_message)
            return redirect('login')

    return render(request, 'login.html')

def logout_view(request):
    request.session.flush()  
    messages.info(request, 'Anda telah logout.')
    return redirect('login')