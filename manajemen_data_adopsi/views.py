from django.shortcuts import render
from django.db import connection
from django.http import Http404, HttpResponse
from datetime import datetime
import uuid

def adoption_list(request):
    with connection.cursor() as cursor:
        # Get all animals with their adoption status and adoption ID if adopted
        cursor.execute("""
            SELECT h.id, h.nama, h.spesies, h.status_kesehatan, 
                   CASE WHEN a.id_hewan IS NOT NULL THEN 'Diadopsi' ELSE 'Belum Diadopsi' END as status_adopsi,
                   CASE WHEN a.id_hewan IS NOT NULL THEN CONCAT(a.id_adopter, '-', a.id_hewan) ELSE NULL END as adoption_id
            FROM sizopi.hewan h
            LEFT JOIN sizopi.adopsi a ON h.id = a.id_hewan AND a.tgl_berhenti_adopsi >= CURRENT_DATE
        """)
        animals = cursor.fetchall()
        
        # Convert to list of dicts for easier template access
        animal_list = []
        for animal in animals:
            animal_list.append({
                'id_hewan': str(animal[0]),
                'nama': animal[1],
                'spesies': animal[2],
                'status_kesehatan': animal[3],
                'status_adopsi': animal[4],
                'adoption_id': animal[5]
            })
    
    return render(request, 'adoption_list.html', {'animals': animal_list})

def adoption_detail(request, adoption_id):
    try:
        # Split the adoption_id into its components
        parts = adoption_id.split('-')
        if len(parts) != 10:  # Expecting 10 parts for two UUIDs
            return HttpResponse(f"Invalid adoption ID format: {adoption_id}")

        # Reconstruct the UUIDs
        adopter_id = '-'.join(parts[:5])  # First 5 parts for adopter_id
        animal_id = '-'.join(parts[5:])   # Last 5 parts for animal_id

        # Convert both IDs to UUID
        try:
            adopter_id = uuid.UUID(adopter_id)
            animal_id = uuid.UUID(animal_id)
        except ValueError:
            return HttpResponse(f"Invalid UUID in adoption ID: adopter_id={adopter_id}, animal_id={animal_id}")

        with connection.cursor() as cursor:
            # Updated query with potential column name fixes
            query = """
                SELECT a.id_adopter, a.id_hewan, a.status_pembayaran, 
                       a.tgl_mulai_adopsi, a.tgl_berhenti_adopsi, a.kontribusi_finansial,
                       h.nama, h.spesies, h.status_kesehatan,
                       ad.username_adopter, ad.total_kontribusi,
                       COALESCE(i.nama, o.nama_organisasi) as nama_adopter,
                       CASE 
                           WHEN i.id_adopter IS NOT NULL THEN 'Individu'
                           WHEN o.id_adopter IS NOT NULL THEN 'Organisasi'
                           ELSE 'Tidak Diketahui'
                       END as tipe_adopter
                FROM sizopi.adopsi a
                JOIN sizopi.hewan h ON a.id_hewan = h.id
                JOIN sizopi.adopter ad ON a.id_adopter = ad.id_adopter
                LEFT JOIN sizopi.individu i ON ad.id_adopter = i.id_adopter
                LEFT JOIN sizopi.organisasi o ON ad.id_adopter = o.id_adopter
                WHERE a.id_adopter = %s AND a.id_hewan = %s
            """
            cursor.execute(query, [adopter_id, animal_id])
            
            adoption = cursor.fetchone()
            
            if not adoption:
                return HttpResponse(f"Adoption not found for adopter_id={adopter_id}, animal_id={animal_id}")
            
            # Format dates
            mulai_adopsi = datetime.strptime(str(adoption[3]), '%Y-%m-%d').strftime('%d %B %Y')
            berhenti_adopsi = datetime.strptime(str(adoption[4]), '%Y-%m-%d').strftime('%d %B %Y')
            
            context = {
                'adoption': {
                    'id': adoption_id,
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
                        'total_kontribusi': f"Rp {adoption[10]:,}",
                        'nama_adopter': adoption[11],
                        'tipe_adopter': adoption[12]
                    }
                }
            }

    except Exception as e:
        # Log the error for debugging
        return HttpResponse(f"Error in adoption_detail: {str(e)}")

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
                months_to_add = int(adoption_period)
                new_month = end_date.month + months_to_add
                new_year = end_date.year + (new_month - 1) // 12
                new_month = ((new_month - 1) % 12) + 1
                end_date = end_date.replace(year=new_year, month=new_month)
                
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
            
            if not animal:
                raise Http404("Hewan tidak ditemukan")
            
            context = {
                'animal': {
                    'id': animal_id,
                    'nama': animal[0],
                    'spesies': animal[1],
                    'status_kesehatan': animal[2]
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
            adopter_id, animal_id = adoption_id.split('-', 1)
            
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
            adopter_id, animal_id = adoption_id.split('-', 1)
            
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
                            'spesies': adoption[4]
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
            adopter_id, animal_id = adoption_id.split('-', 1)
            
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
            adopter_id, animal_id = adoption_id.split('-', 1)
            
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
                            'spesies': adoption[1]
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
            adopter_id, animal_id = adoption_id.split('-', 1)
            
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
                
                # Try to get medical records (table might not exist)
                try:
                    cursor.execute("""
                        SELECT tanggal_pemeriksaan, nama_dokter, status_kesehatan, 
                               diagnosa, pengobatan, catatan_tindak_lanjut
                        FROM sizopi.rekam_medis
                        WHERE id_hewan = %s
                        ORDER BY tanggal_pemeriksaan DESC
                    """, [animal_id])
                    medical_records = cursor.fetchall()
                except:
                    medical_records = []
                
                # Try to get condition reports (table might not exist)
                try:
                    cursor.execute("""
                        SELECT tanggal_laporan, kondisi_satwa, foto_kondisi, 
                               berat_badan, suhu_tubuh, nafsu_makan
                        FROM sizopi.laporan_kondisi
                        WHERE id_hewan = %s
                        ORDER BY tanggal_laporan DESC
                    """, [animal_id])
                    condition_reports = cursor.fetchall()
                except:
                    condition_reports = []
                
                context = {
                    'adoption': {
                        'id': adoption_id,
                        'animal': {
                            'nama': adoption[0],
                            'spesies': adoption[1],
                            'habitat': adoption[2] if adoption[2] else 'N/A'
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
            adopter_id, animal_id = adoption_id.split('-', 1)
            
            with connection.cursor() as cursor:
                # Insert condition report (table might not exist)
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
            adopter_id, animal_id = adoption_id.split('-', 1)
            
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
                            'spesies': adoption[1]
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