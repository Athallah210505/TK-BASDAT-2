from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection
from psycopg2 import Error as Psycopg2Error
from django.db import DatabaseError
import uuid
import re

def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        first_name = request.POST.get('first_name')
        middle_name = request.POST.get('middle_name')
        last_name = request.POST.get('last_name')
        phone_number = request.POST.get('phone_number')
        role = request.POST.get('role')

        if password1 != password2:
            messages.error(request, "Password tidak cocok!")
            return redirect('register')

        if not re.fullmatch(r'\d{10,15}', phone_number):
            messages.error(request, "Nomor telepon harus 10-15 digit angka.")
            return redirect('register')

        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO sizopi.pengguna (username, email, password, nama_depan, nama_tengah, nama_belakang, no_telepon)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, [username, email, password1, first_name, middle_name, last_name, phone_number])

                if role == 'pengunjung':
                    cursor.execute("""
                        INSERT INTO sizopi.pengunjung (username_P, alamat, tgl_lahir)
                        VALUES (%s, %s, %s)
                    """, [username, request.POST.get('address'), request.POST.get('birth_date')])

                elif role == 'dokter':
                    cursor.execute("""
                        INSERT INTO sizopi.dokter_hewan (username_DH, no_STR)
                        VALUES (%s, %s)
                    """, [username, request.POST.get('certificate_no')])

                    specs = request.POST.getlist('specializations')
                    other = request.POST.get('other_spec')
                    for spec in specs + ([other] if other else []):
                        cursor.execute("""
                            INSERT INTO sizopi.spesialisasi (username_SH, nama_spesialisasi)
                            VALUES (%s, %s)
                        """, [username, spec])

                elif role == 'staff':
                    staff_role = request.POST.get('staff_role')
                    staff_id = str(uuid.uuid4())
                    if staff_role == 'pjh':
                        cursor.execute("INSERT INTO sizopi.penjaga_hewan (username_jh, id_staf) VALUES (%s, %s)", [username, staff_id])
                    elif staff_role == 'adm':
                        cursor.execute("INSERT INTO sizopi.staf_admin (username_sa, id_staf) VALUES (%s, %s)", [username, staff_id])
                    elif staff_role == 'plp':
                        cursor.execute("INSERT INTO sizopi.pelatih_hewan (username_lh, id_staf) VALUES (%s, %s)", [username, staff_id])

            messages.success(request, f"Akun '{username}' berhasil dibuat!")
            return redirect('login')

        except DatabaseError as e:
            error_message = str(e).splitlines()[0].replace('ERROR:', '').strip()
            messages.error(request, error_message)
            return redirect('register')

    return render(request, 'register.html')
