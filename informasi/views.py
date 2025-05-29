from django.shortcuts import render
from django.db import connection

# Create your views here.

def satwa_list(request):
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
    animals = [ dict(zip(cols, row)) for row in rows ]
    return render(request, 'informasi/satwa_list.html', {
        'animals': animals,
    })
