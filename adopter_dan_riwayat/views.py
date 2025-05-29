from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db import connection
from django.db.utils import DatabaseError
from django.utils import timezone
import json

def adopter_list(request):
    try:
        with connection.cursor() as cursor:
            # top 5 contributors
            cursor.execute("""
                SELECT a.username_adopter, a.id_adopter, SUM(ad.kontribusi_finansial) as total_kontribusi
                FROM sizopi.adopter a
                JOIN sizopi.adopsi ad ON a.id_adopter = ad.id_adopter
                GROUP BY a.username_adopter, a.id_adopter
                ORDER BY total_kontribusi DESC
                LIMIT 5
            """)
            top_contributors = []
            for row in cursor.fetchall():
                top_contributors.append({
                    'username': row[0],
                    'id': row[1],
                    'total_contribution': row[2]
                })

            # all adopters with their adoption count and total contribution
            cursor.execute("""
                SELECT a.username_adopter, a.id_adopter, 
                       COALESCE(SUM(ad.kontribusi_finansial), 0) as total_kontribusi,
                       COUNT(ad.id_hewan) as jumlah_adopsi
                FROM sizopi.adopter a
                LEFT JOIN sizopi.adopsi ad ON a.id_adopter = ad.id_adopter
                GROUP BY a.username_adopter, a.id_adopter
                ORDER BY total_kontribusi DESC
            """)
            adopters = []
            for row in cursor.fetchall():
                adopters.append({
                    'username': row[0],
                    'id': row[1],
                    'total_contribution': row[2],
                    'adoption_count': row[3]
                })

        return render(request, 'adopter_list.html', {
            'top_contributors': top_contributors,
            'adopters': adopters
        })

    except DatabaseError as e:
        error_message = str(e).splitlines()[0].replace('ERROR:', '').strip()
        return render(request, 'adopter_list.html', {
            'error': error_message
        })

def adopter_detail(request, adopter_id=None):
    if not adopter_id:
        return redirect('adopter_list')
    
    try:
        with connection.cursor() as cursor:
            # adopter info 
            cursor.execute("""
                SELECT a.username_adopter, a.id_adopter, 
                       COALESCE(SUM(ad.kontribusi_finansial), 0) as total_kontribusi
                FROM sizopi.adopter a
                LEFT JOIN sizopi.adopsi ad ON a.id_adopter = ad.id_adopter
                WHERE a.id_adopter = %s
                GROUP BY a.username_adopter, a.id_adopter
            """, [adopter_id])
            adopter_data = cursor.fetchone()
            
            if not adopter_data:
                return redirect('adopter_list')
            
            cursor.execute("""
                SELECT 
                    ad.id_hewan, 
                    COALESCE(h.nama, 'Unknown') as nama_hewan,
                    COALESCE(h.spesies, 'Unknown') as jenis_hewan,
                    ad.tgl_mulai_adopsi,
                    ad.tgl_berhenti_adopsi,
                    ad.kontribusi_finansial,
                    ad.status_pembayaran
                FROM sizopi.adopsi ad
                LEFT JOIN sizopi.hewan h ON ad.id_hewan = h.id
                WHERE ad.id_adopter = %s
                ORDER BY ad.tgl_mulai_adopsi DESC
            """, [adopter_id])
            
            adoptions = []
            active_count = 0
            current_date = timezone.now().date()
            
            for row in cursor.fetchall():
                is_active = row[4] is None or row[4] > current_date
                if is_active:
                    active_count += 1
                
                adoptions.append({
                    'animal_id': row[0],
                    'animal_name': row[1],
                    'animal_type': row[2],
                    'start_date': row[3],
                    'end_date': row[4],
                    'contribution': row[5],
                    'payment_status': row[6],
                    'is_active': is_active
                })

        return render(request, 'adopter_detail.html', {
            'adopter': {
                'username': adopter_data[0],
                'id': adopter_data[1],
                'total_contribution': adopter_data[2] or 0
            },
            'adoptions': adoptions,
            'total_adoptions': len(adoptions),
            'active_adoptions': active_count
        })

    except Exception as e:
        return render(request, 'adopter_detail.html', {
            'error': f"Error: {str(e)}",
            'adopter': {
                'username': '',
                'id': adopter_id,
                'total_contribution': 0
            },
            'adoptions': [],
            'total_adoptions': 0,
            'active_adoptions': 0
        })

@csrf_exempt
@require_http_methods(["DELETE"])
def delete_adoption(request, adoption_id):
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                DELETE FROM sizopi.adopsi
                WHERE id_hewan = %s
                RETURNING id_adopter
            """, [adoption_id])
            
            if cursor.rowcount == 0:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Adoption record not found'
                }, status=404)
            
            adopter_id = cursor.fetchone()[0]
            
            # update total contribution for the adopter
            cursor.execute("""
                UPDATE sizopi.adopter
                SET total_kontribusi = (
                    SELECT COALESCE(SUM(kontribusi_finansial), 0)
                    FROM sizopi.adopsi
                    WHERE id_adopter = %s
                )
                WHERE id_adopter = %s
            """, [adopter_id, adopter_id])
            
        return JsonResponse({
            'status': 'success',
            'message': 'Adoption record deleted successfully'
        })
        
    except DatabaseError as e:
        error_message = str(e).splitlines()[0].replace('ERROR:', '').strip()
        return JsonResponse({
            'status': 'error',
            'message': error_message
        }, status=500)

@csrf_exempt
@require_http_methods(["DELETE"])
def delete_adopter(request, adopter_id):
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                DELETE FROM sizopi.adopsi
                WHERE id_adopter = %s
            """, [adopter_id])
            
            cursor.execute("""
                DELETE FROM sizopi.adopter
                WHERE id_adopter = %s
                RETURNING username_adopter
            """, [adopter_id])
            
            if cursor.rowcount == 0:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Adopter not found'
                }, status=404)
            
        return JsonResponse({
            'status': 'success',
            'message': 'Adopter deleted successfully'
        })
        
    except DatabaseError as e:
        error_message = str(e).splitlines()[0].replace('ERROR:', '').strip()
        return JsonResponse({
            'status': 'error',
            'message': error_message
        }, status=500)