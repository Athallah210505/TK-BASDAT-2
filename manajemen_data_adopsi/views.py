from django.shortcuts import render, redirect
from django.db import connection
from django.http import Http404
from datetime import datetime

def adoption_list(request):
    with connection.cursor() as cursor:
        # Get all animals with their adoption status
        cursor.execute("""
            SELECT h.id, h.nama, h.spesies, h.status_kesehatan, 
                   CASE WHEN a.id_hewan IS NOT NULL THEN 'Diadopsi' ELSE 'Belum Diadopsi' END as status_adopsi
            FROM sizopi.hewan h
            LEFT JOIN sizopi.adopsi a ON h.id = a.id_hewan
            WHERE a.tgl_berhenti_adopsi >= CURRENT_DATE OR a.id_hewan IS NULL
        """)
        animals = cursor.fetchall()
        
        # Convert to list of dicts for easier template access
        animal_list = []
        for animal in animals:
            animal_list.append({
                'id_hewan': animal[0],
                'nama_hewan': animal[1],
                'jenis_hewan': animal[2],
                'kondisi': animal[3],
                'status_adopsi': animal[4]
            })
    
    return render(request, 'adoption_list.html', {'animals': animal_list})

def adoption_detail(request, adoption_id):
    with connection.cursor() as cursor:
        # Get adoption details
        cursor.execute("""
            SELECT a.id_adopter, a.id_hewan, a.status_pembayaran, 
                   a.tgl_mulai_adopsi, a.tgl_berhenti_adopsi, a.kontribusi_finansial,
                   h.nama, h.spesies, h.status_kesehatan,
                   ad.username_adopter, ad.total_kontribusi
            FROM sizopi.adopsi a
            JOIN sizopi.hewan h ON a.id_hewan = h.id
            JOIN sizopi.adopter ad ON a.id_adopter = ad.id_adopter
            WHERE a.id_adopter = %s AND a.id_hewan = %s
        """, [adoption_id.split('-')[0], adoption_id.split('-')[1] if '-' in str(adoption_id) else adoption_id])
        adoption = cursor.fetchone()
        
        if not adoption:
            raise Http404("Adopsi tidak ditemukan")
            
        # Format dates
        mulai_adopsi = datetime.strptime(str(adoption[3]), '%Y-%m-%d').strftime('%d %B %Y')
        berhenti_adopsi = datetime.strptime(str(adoption[4]), '%Y-%m-%d').strftime('%d %B %Y')
        
        context = {
            'adoption': {
                'id': f"{adoption[0]}-{adoption[1]}",
                'status_pembayaran': adoption[2],
                'mulai_adopsi': mulai_adopsi,
                'berhenti_adopsi': berhenti_adopsi,
                'kontribusi_finansial': f"Rp {adoption[5]:,}",
                'animal': {
                    'nama': adoption[6],
                    'jenis': adoption[7],
                    'kondisi': adoption[8]
                },
                'adopter': {
                    'username': adoption[9],
                    'total_kontribusi': f"Rp {adoption[10]:,}"
                }
            }
        }
    
    return render(request, 'adoption_detail.html', context)

def register_adopter(request, animal_id=None):
    if request.method == 'POST':
        # Handle form submission
        username = request.POST.get('username')
        adopter_type = request.POST.get('adopter_type')
        start_date = request.POST.get('start_date')
        adoption_period = request.POST.get('adoption_period')
        contribution = request.POST.get('contribution')
        
        try:
            with connection.cursor() as cursor:
                # Get adopter ID first
                cursor.execute("""
                    SELECT id_adopter FROM sizopi.adopter WHERE username_adopter = %s
                """, [username])
                adopter_result = cursor.fetchone()
                if not adopter_result:
                    raise Exception("Adopter tidak ditemukan")
                adopter_id = adopter_result[0]
                
                # Calculate end date
                end_date = datetime.strptime(start_date, '%Y-%m-%d')
                end_date = end_date.replace(month=end_date.month + int(adoption_period))
                
                # Create adoption record
                cursor.execute("""
                    INSERT INTO sizopi.adopsi 
                    (id_adopter, id_hewan, status_pembayaran, tgl_mulai_adopsi, tgl_berhenti_adopsi, kontribusi_finansial)
                    VALUES (%s, %s, 'Tertunda', %s, %s, %s)
                """, [
                    adopter_id,
                    animal_id,
                    start_date,
                    end_date.strftime('%Y-%m-%d'),
                    contribution
                ])
                
                # Update adopter's total contribution
                cursor.execute("""
                    UPDATE sizopi.adopter
                    SET total_kontribusi = total_kontribusi + %s
                    WHERE username_adopter = %s
                """, [contribution, username])
                
            return redirect('adoption_list')
            
        except Exception as e:
            error_message = str(e)
            return render(request, 'adoption_form.html', {'error': error_message, 'animal_id': animal_id})
    
    # GET request - show form
    if animal_id:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT nama, spesies, status_kesehatan
                FROM sizopi.hewan
                WHERE id = %s
            """, [animal_id])
            animal = cursor.fetchone()
            
            context = {
                'animal': {
                    'id': animal_id,
                    'nama': animal[0],
                    'jenis': animal[1],
                    'kondisi': animal[2]
                }
            }
            
        return render(request, 'adoption_form.html', context)
    else:
        return render(request, 'adoption_form.html')

def extend_adoption(request, adoption_id=None):
    if request.method == 'POST':
        end_date = request.POST.get('end_date')
        additional_contribution = request.POST.get('contribution')
        
        try:
            # Parse adoption_id (format: adopter_id-animal_id)
            adopter_id, animal_id = adoption_id.split('-')
            
            with connection.cursor() as cursor:
                # Update adoption record
                cursor.execute("""
                    UPDATE sizopi.adopsi
                    SET tgl_berhenti_adopsi = %s,
                        kontribusi_finansial = kontribusi_finansial + %s
                    WHERE id_adopter = %s AND id_hewan = %s
                """, [end_date, additional_contribution, adopter_id, animal_id])
                
                # Update adopter's total contribution
                cursor.execute("""
                    UPDATE sizopi.adopter
                    SET total_kontribusi = total_kontribusi + %s
                    WHERE id_adopter = %s
                """, [additional_contribution, adopter_id])
                
            return redirect('adoption_detail', adoption_id=adoption_id)
            
        except Exception as e:
            error_message = str(e)
            return render(request, 'adoption_extension_form.html', {'error': error_message})
    
    # GET request - show form
    if adoption_id:
        try:
            adopter_id, animal_id = adoption_id.split('-')
            
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT a.tgl_mulai_adopsi, a.tgl_berhenti_adopsi, a.kontribusi_finansial,
                           h.nama, h.spesies,
                           ad.username_adopter
                    FROM sizopi.adopsi a
                    JOIN sizopi.hewan h ON a.id_hewan = h.id
                    JOIN sizopi.adopter ad ON a.id_adopter = ad.id_adopter
                    WHERE a.id_adopter = %s AND a.id_hewan = %s
                """, [adopter_id, animal_id])
                adoption = cursor.fetchone()
                
                if not adoption:
                    raise Http404("Adopsi tidak ditemukan")
                    
                context = {
                    'adoption': {
                        'id': adoption_id,
                        'mulai_adopsi': adoption[0],
                        'berhenti_adopsi': adoption[1],
                        'kontribusi_finansial': adoption[2],
                        'animal': {
                            'nama': adoption[3],
                            'jenis': adoption[4]
                        },
                        'adopter': {
                            'username': adoption[5]
                        }
                    }
                }
                
        except ValueError:
            raise Http404("Format ID adopsi tidak valid")
            
        return render(request, 'adoption_extension_form.html', context)
    else:
        return render(request, 'adoption_extension_form.html')

def end_adoption(request, adoption_id=None):
    if request.method == 'POST' and adoption_id:
        try:
            adopter_id, animal_id = adoption_id.split('-')
            
            with connection.cursor() as cursor:
                # Update adoption end date to current date
                cursor.execute("""
                    UPDATE sizopi.adopsi
                    SET tgl_berhenti_adopsi = CURRENT_DATE
                    WHERE id_adopter = %s AND id_hewan = %s
                """, [adopter_id, animal_id])
                
            return redirect('adoption_list')
            
        except Exception as e:
            error_message = str(e)
            return render(request, 'adoption_detail.html', {'error': error_message})
    
    return redirect('adoption_list')

def adopter_info(request, adopter_id=None):
    if adopter_id:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT a.username_adopter, a.total_kontribusi,
                       COUNT(ad.id_adopter) as jumlah_adopsi
                FROM sizopi.adopter a
                LEFT JOIN sizopi.adopsi ad ON a.id_adopter = ad.id_adopter
                WHERE a.id_adopter = %s
                GROUP BY a.username_adopter, a.total_kontribusi
            """, [adopter_id])
            adopter = cursor.fetchone()
            
            if not adopter:
                raise Http404("Adopter tidak ditemukan")
                
            cursor.execute("""
                SELECT ad.id_adopter, ad.id_hewan, h.nama, h.spesies, 
                       ad.tgl_mulai_adopsi, ad.tgl_berhenti_adopsi, ad.kontribusi_finansial
                FROM sizopi.adopsi ad
                JOIN sizopi.hewan h ON ad.id_hewan = h.id
                WHERE ad.id_adopter = %s
                AND ad.tgl_berhenti_adopsi >= CURRENT_DATE
            """, [adopter_id])
            adoptions = cursor.fetchall()
            
            adoption_list = []
            for adoption in adoptions:
                adoption_list.append({
                    'id': f"{adoption[0]}-{adoption[1]}",
                    'nama_hewan': adoption[2],
                    'jenis_hewan': adoption[3],
                    'mulai_adopsi': adoption[4],
                    'berhenti_adopsi': adoption[5],
                    'kontribusi_finansial': adoption[6]
                })
            
            context = {
                'adopter': {
                    'username': adopter[0],
                    'total_kontribusi': f"Rp {adopter[1]:,}",
                    'jumlah_adopsi': adopter[2]
                },
                'adoptions': adoption_list
            }
            
        return render(request, 'adopter_info.html', context)
    else:
        return render(request, 'adopter_info.html')

def adoption_certificate(request, adoption_id=None):
    if adoption_id:
        try:
            adopter_id, animal_id = adoption_id.split('-')
            
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT h.nama, h.spesies,
                           ad.username_adopter, a.tgl_mulai_adopsi, a.tgl_berhenti_adopsi,
                           a.kontribusi_finansial
                    FROM sizopi.adopsi a
                    JOIN sizopi.hewan h ON a.id_hewan = h.id
                    JOIN sizopi.adopter ad ON a.id_adopter = ad.id_adopter
                    WHERE a.id_adopter = %s AND a.id_hewan = %s
                """, [adopter_id, animal_id])
                adoption = cursor.fetchone()
                
                if not adoption:
                    raise Http404("Adopsi tidak ditemukan")
                    
                context = {
                    'adoption': {
                        'id': adoption_id,
                        'animal': {
                            'nama': adoption[0],
                            'jenis': adoption[1]
                        },
                        'adopter': {
                            'username': adoption[2]
                        },
                        'mulai_adopsi': adoption[3],
                        'berhenti_adopsi': adoption[4],
                        'kontribusi_finansial': f"Rp {adoption[5]:,}"
                    }
                }
                
        except ValueError:
            raise Http404("Format ID adopsi tidak valid")
            
        return render(request, 'adoption_certificate.html', context)
    else:
        return render(request, 'adoption_certificate.html')

def animal_condition_report(request, adoption_id=None):
    if adoption_id:
        try:
            adopter_id, animal_id = adoption_id.split('-')
            
            with connection.cursor() as cursor:
                # Get adoption info
                cursor.execute("""
                    SELECT h.nama, h.spesies, h.nama_habitat,
                           ad.username_adopter, a.tgl_mulai_adopsi, a.tgl_berhenti_adopsi
                    FROM sizopi.adopsi a
                    JOIN sizopi.hewan h ON a.id_hewan = h.id
                    JOIN sizopi.adopter ad ON a.id_adopter = ad.id_adopter
                    WHERE a.id_adopter = %s AND a.id_hewan = %s
                """, [adopter_id, animal_id])
                adoption = cursor.fetchone()
                
                if not adoption:
                    raise Http404("Adopsi tidak ditemukan")
                    
                # Get medical records (assuming table exists)
                cursor.execute("""
                    SELECT tanggal_pemeriksaan, nama_dokter, status_kesehatan, 
                           diagnosa, pengobatan, catatan_tindak_lanjut
                    FROM sizopi.rekam_medis
                    WHERE id_hewan = %s
                    ORDER BY tanggal_pemeriksaan DESC
                """, [animal_id])
                medical_records = cursor.fetchall()
                
                # Get condition reports (assuming table exists)
                cursor.execute("""
                    SELECT tanggal_laporan, kondisi_satwa, foto_kondisi, 
                           berat_badan, suhu_tubuh, nafsu_makan
                    FROM sizopi.laporan_kondisi
                    WHERE id_hewan = %s
                    ORDER BY tanggal_laporan DESC
                """, [animal_id])
                condition_reports = cursor.fetchall()
                
                context = {
                    'adoption': {
                        'id': adoption_id,
                        'animal': {
                            'nama': adoption[0],
                            'jenis': adoption[1],
                            'habitat': adoption[2]
                        },
                        'adopter': {
                            'username': adoption[3]
                        },
                        'periode': f"{adoption[4]} s/d {adoption[5]}"
                    },
                    'medical_records': medical_records,
                    'condition_reports': condition_reports
                }
                
        except ValueError:
            raise Http404("Format ID adopsi tidak valid")
            
        return render(request, 'animal_condition_report.html', context)
    else:
        return render(request, 'animal_condition_report.html')

def create_animal_report(request, adoption_id=None):
    if request.method == 'POST':
        condition = request.POST.get('condition')
        photo = request.FILES.get('photo')
        weight = request.POST.get('weight')
        temperature = request.POST.get('temperature')
        appetite = request.POST.get('appetite')
        
        try:
            adopter_id, animal_id = adoption_id.split('-')
            
            with connection.cursor() as cursor:
                # Insert condition report
                cursor.execute("""
                    INSERT INTO sizopi.laporan_kondisi
                    (id_hewan, tanggal_laporan, kondisi_satwa, foto_kondisi,
                     berat_badan, suhu_tubuh, nafsu_makan)
                    VALUES (%s, CURRENT_DATE, %s, %s, %s, %s, %s)
                """, [animal_id, condition, photo.read() if photo else None, 
                      weight, temperature, appetite])
                
            return redirect('animal_condition_report', adoption_id=adoption_id)
            
        except Exception as e:
            error_message = str(e)
            return render(request, 'create_animal_report.html', {'error': error_message})
    
    # GET request - show form
    if adoption_id:
        try:
            adopter_id, animal_id = adoption_id.split('-')
            
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT h.nama, h.spesies,
                           ad.username_adopter, a.tgl_mulai_adopsi, a.tgl_berhenti_adopsi
                    FROM sizopi.adopsi a
                    JOIN sizopi.hewan h ON a.id_hewan = h.id
                    JOIN sizopi.adopter ad ON a.id_adopter = ad.id_adopter
                    WHERE a.id_adopter = %s AND a.id_hewan = %s
                """, [adopter_id, animal_id])
                adoption = cursor.fetchone()
                
                if not adoption:
                    raise Http404("Adopsi tidak ditemukan")
                    
                context = {
                    'adoption': {
                        'id': adoption_id,
                        'animal': {
                            'nama': adoption[0],
                            'jenis': adoption[1]
                        },
                        'adopter': {
                            'username': adoption[2]
                        },
                        'periode': f"{adoption[3]} s/d {adoption[4]}"
                    }
                }
                
        except ValueError:
            raise Http404("Format ID adopsi tidak valid")
            
        return render(request, 'create_animal_report.html', context)
    else:
        return render(request, 'create_animal_report.html')