from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import connection, DatabaseError
from django.http import JsonResponse
from utils.decorators import role_required

@role_required(('penjaga_hewan', 'staff'))
def habitat_list(request):
    with connection.cursor() as cur:
        cur.execute("""
            SELECT nama, luas_area, kapasitas, status
            FROM sizopi.habitat
            ORDER BY nama;
        """)
        habitats = [
            {
                'nama': row[0],
                'luas_area': row[1],
                'kapasitas': row[2],
                'status': row[3],
            }
            for row in cur.fetchall()
        ]
    role = request.session.get('role')
    return render(request, 'habitats/habitat_list.html', {
        'habitats': habitats,
        'user_role': role,
    })

@role_required(('penjaga_hewan', 'staff'))
def habitat_create(request):
    if request.method == 'POST':
        nama = request.POST['name']
        luas_area = request.POST['area']
        kapasitas = request.POST['capacity']
        status = request.POST['environment_status']
        try:
            with connection.cursor() as cur:
                cur.execute("""
                    INSERT INTO sizopi.habitat (nama, luas_area, kapasitas, status)
                    VALUES (%s, %s, %s, %s)
                """, [nama, luas_area, kapasitas, status])
            messages.success(request, "Habitat berhasil ditambahkan.")
            return redirect('habitat:habitat_list')
        except DatabaseError as e:
            err_msg = getattr(e, 'pgerror', str(e))
            clean_msg = err_msg.split('\n')[0]
            messages.error(request, clean_msg)
            return redirect('habitat:habitat_create')
    role = request.session.get('role')
    return render(request, 'habitats/habitat_create.html', {
        'habitat': None,
        'user_role': role,
    })

@role_required(('penjaga_hewan', 'staff'))
def habitat_edit(request, nama):
    with connection.cursor() as cur:
        cur.execute("SELECT nama, luas_area, kapasitas, status FROM sizopi.habitat WHERE nama = %s", [nama])
        row = cur.fetchone()
        if not row:
            messages.error(request, "Habitat tidak ditemukan.")
            return redirect('habitat:habitat_list')
        habitat = {
            'name': row[0],
            'area': row[1],
            'capacity': row[2],
            'environment_status': row[3],
        }
    if request.method == 'POST':
        new_nama = request.POST['name']
        luas_area = request.POST['area']
        kapasitas = request.POST['capacity']
        status = request.POST['environment_status']
        try:
            with connection.cursor() as cur:
                cur.execute("""
                    UPDATE sizopi.habitat
                    SET nama = %s, luas_area = %s, kapasitas = %s, status = %s
                    WHERE nama = %s
                """, [new_nama, luas_area, kapasitas, status, nama])
            messages.success(request, "Habitat berhasil diperbarui.")
            return redirect('habitat:habitat_list')
        except DatabaseError as e:
            err_msg = getattr(e, 'pgerror', str(e))
            clean_msg = err_msg.split('\n')[0]
            messages.error(request, clean_msg)
            return redirect('habitat:habitat_edit', nama=nama)
    role = request.session.get('role')
    return render(request, 'habitats/habitat_create.html', {
        'habitat': habitat,
        'user_role': role,
    })

@role_required(('penjaga_hewan', 'staff'))
def habitat_delete(request, nama):
    if request.method == 'POST':
        try:
            with connection.cursor() as cur:
                cur.execute("DELETE FROM sizopi.habitat WHERE nama = %s", [nama])
            return JsonResponse({'success': True, 'message': 'Habitat berhasil dihapus.'})
        except DatabaseError as e:
            err_msg = getattr(e, 'pgerror', str(e))
            clean_msg = err_msg.split('\n')[0]
            return JsonResponse({'success': False, 'error': clean_msg}, status=400)
    return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)

@role_required(('penjaga_hewan', 'staff'))
def habitat_detail(request, nama):
    with connection.cursor() as cur:
        cur.execute("SELECT nama, luas_area, kapasitas, status FROM sizopi.habitat WHERE nama = %s", [nama])
        row = cur.fetchone()
        if not row:
            messages.error(request, "Habitat tidak ditemukan.")
            return redirect('habitat:habitat_list')
        habitat = {
            'nama': row[0],
            'luas_area': row[1],
            'kapasitas': row[2],
            'status': row[3],
        }
        # Ambil daftar hewan di habitat ini
        cur.execute("""
            SELECT nama, spesies, asal_hewan, tanggal_lahir, status_kesehatan
            FROM sizopi.hewan
            WHERE nama_habitat = %s
            ORDER BY spesies, nama
        """, [nama])
        animals = [
            {
                'name': r[0],
                'species': r[1],
                'origin': r[2],
                'birth_date': r[3],
                'health_status': r[4],
            }
            for r in cur.fetchall()
        ]
    role = request.session.get('role')
    return render(request, 'habitats/habitat_detail.html', {
        'habitat': habitat,
        'animals': animals,
        'user_role': role,
    })