import uuid
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse, Http404
from django.urls import reverse
from django.db import connection, DatabaseError
from utils.decorators import role_required

HEALTH_STATUS_CHOICES = [
    ('Sehat', 'Sehat'),
    ('Sakit', 'Sakit'),
    ('Dalam Pemantauan', 'Dalam Pemantauan'),
    ('Lain-lain', 'Lain-lain'),
]

def get_habitats():
    with connection.cursor() as cur:
        cur.execute("SELECT nama FROM sizopi.habitat ORDER BY nama;")
        return [row[0] for row in cur.fetchall()]
    

@role_required(('dokter', 'penjaga_hewan', 'staff'))
def animal_list(request):
    """
    Tampilkan semua hewan dari schema sizopi.hewan,
    dengan alias kolom yang cocok ke template.
    """
    with connection.cursor() as cur:
        cur.execute("""
            SELECT
              id::text                          AS id,
              nama                              AS name,
              spesies                           AS species,
              asal_hewan                        AS origin,
              to_char(tanggal_lahir, 'YYYY-MM-DD') AS birth_date,
              status_kesehatan                  AS health_status,
              nama_habitat                      AS habitat,
              url_foto                          AS photo_url
            FROM sizopi.hewan
            ORDER BY species, name;
        """)
        cols = [c[0] for c in cur.description]
        rows = cur.fetchall()

    # sekarang keys di dict akan match: name, origin, habitat, dsb.
    animals = [ dict(zip(cols, row)) for row in rows ]
    role = request.session.get('role')
    return render(request, 'animals/animal_list.html', {
        'animals': animals,
        'habitats': get_habitats(),
        'health_choices': HEALTH_STATUS_CHOICES,
        'user_role': role,
    })


@role_required(('dokter', 'penjaga_hewan', 'staff'))
def animal_create(request):
    """
    Tambah hewan baru. Trigger fn_check_duplicate_satwa() akan dijalankan otomatis.
    """
    if request.method == 'GET':
        # Bersihkan pesan sukses yang tertinggal
        storage = messages.get_messages(request)
        for _ in storage:
            pass
    if request.method == 'POST':
        nama       = request.POST.get('name') or None
        species    = request.POST['species']
        origin     = request.POST['origin']
        birth_date = request.POST.get('birth_date') or None
        status     = request.POST['health_status']
        habitat    = request.POST['habitat']
        photo_url  = request.POST.get('photo_url') or ''

        try:
            with connection.cursor() as cur:
                cur.execute("""
                    INSERT INTO sizopi.hewan
                      (id, nama, spesies, asal_hewan, tanggal_lahir,
                       status_kesehatan, nama_habitat, url_foto)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
                """, [ str(uuid.uuid4()), nama, species, origin,
                       birth_date, status, habitat, photo_url ])
            messages.success(request, "Data satwa berhasil ditambahkan.")
            return redirect('animals:animal_list')

        except DatabaseError as e:
            # Ambil pesan asli dari Postgres:
            err_msg = getattr(e, 'pgerror', str(e))
            clean_msg = err_msg.split('\n')[0]
            messages.error(request, clean_msg)
            return redirect('animals:animal_create')

    role = request.session.get('role')
    return render(request, 'animals/animal_form.html', {
        'animal': None,
        'habitats': get_habitats(), 
        'health_choices': HEALTH_STATUS_CHOICES,
        'user_role': role,
    })

@role_required(('dokter', 'penjaga_hewan', 'staff'))
def animal_update(request, pk):
    """
    AJAX endpoint untuk update record hewan.
    Trigger fn_log_riwayat_satwa() akan mencatat perubahan.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=405)

    # Cek apakah hewan ada
    with connection.cursor() as cur:
        cur.execute("SELECT 1 FROM sizopi.hewan WHERE id = %s;", [pk])
        if not cur.fetchone():
            return JsonResponse({'error': 'Data satwa tidak ditemukan.'}, status=404)

    nama       = request.POST.get('name') or None
    species    = request.POST['species']
    origin     = request.POST['origin']
    birth_date = request.POST.get('birth_date') or None
    status     = request.POST['health_status']
    habitat    = request.POST['habitat']
    photo_url  = request.POST.get('photo_url') or ''


    try:
        with connection.cursor() as cur:
            cur.execute("""
                UPDATE sizopi.hewan
                   SET nama             = %s,
                       spesies          = %s,
                       asal_hewan       = %s,
                       tanggal_lahir    = %s,
                       status_kesehatan = %s,
                       nama_habitat     = %s,
                       url_foto         = %s
                 WHERE id = %s;
            """, [nama, species, origin, birth_date, status, habitat, photo_url, pk])
            # Ambil pesan NOTICE terakhir dari trigger
            notice_msg = ""
            if hasattr(cur.connection, "notices") and cur.connection.notices:
                notice_msg = cur.connection.notices[-1].strip()
                # Hapus prefix "NOTICE:  " jika ada
                if notice_msg.startswith("NOTICE:"):
                    notice_msg = notice_msg[8:].strip()
                # Bersihkan notices agar tidak menumpuk
                cur.connection.notices.clear()
        return JsonResponse({
            'id': pk,
            'name': nama or '',
            'species': species,
            'origin': origin,
            'birth_date': birth_date or '',
            'health_status': status,
            'habitat': habitat,
            'photo_url': photo_url,
            'notice': notice_msg, 
        })
    except DatabaseError as e:
        err_msg = getattr(e, 'pgerror', str(e))
        clean_msg = err_msg.split('\n')[0]
        return JsonResponse({'error': clean_msg}, status=400)

@role_required(('dokter', 'penjaga_hewan', 'staff'))
def animal_delete(request, pk):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=405)

    # Cek apakah hewan ada
    with connection.cursor() as cur:
        cur.execute("SELECT 1 FROM sizopi.hewan WHERE id = %s;", [pk])
        if not cur.fetchone():
            return JsonResponse({'error': 'Data satwa tidak ditemukan.'}, status=404)

    try:
        with connection.cursor() as cur:
            cur.execute("DELETE FROM sizopi.hewan WHERE id = %s;", [pk])
        return JsonResponse({'success': True})

    except DatabaseError as e:
        err_msg = getattr(e, 'pgerror', str(e))
        clean_msg = err_msg.split('\n')[0]
        messages.error(request, clean_msg)
        return JsonResponse({'error': clean_msg}, status=400)

