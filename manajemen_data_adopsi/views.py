from django.shortcuts import render, redirect 
from django.db import connection
from django.http import Http404, HttpResponse
from datetime import datetime, timedelta 
import uuid
from utils.decorators import role_required

@role_required(('staff', 'pengunjung_adopter'))
def adoption_list(request):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT h.id, h.nama, h.spesies, h.status_kesehatan, h.url_foto,
                   CASE WHEN a.id_hewan IS NOT NULL THEN 'Diadopsi' ELSE 'Belum Diadopsi' END as status_adopsi,
                   CASE WHEN a.id_hewan IS NOT NULL THEN CONCAT(CAST(a.id_adopter AS VARCHAR), '-', CAST(a.id_hewan AS VARCHAR)) ELSE NULL END as adoption_id
            FROM sizopi.hewan h
            LEFT JOIN sizopi.adopsi a ON h.id = a.id_hewan AND a.tgl_berhenti_adopsi >= CURRENT_DATE
        """)
        animals = cursor.fetchall()
        
        animal_list = []
        for animal in animals:
            animal_list.append({
                'id_hewan': str(animal[0]),
                'nama': animal[1],
                'spesies': animal[2],
                'status_kesehatan': animal[3],
                'url_foto': animal[4],  
                'status_adopsi': animal[5],
                'adoption_id': animal[6]
            })
    
    return render(request, 'adoption_list.html', {'animals': animal_list})
    
def _parse_adoption_id(adoption_id_str):
    """Helper function to parse combined adoption ID."""
    parts = adoption_id_str.split('-')
    if len(parts) != 10:  # UUID format: 8-4-4-4-12 (5 parts). Two UUIDs = 10 parts.
        raise ValueError(f"Invalid adoption ID format: {adoption_id_str}")
    
    try:
        adopter_id = uuid.UUID('-'.join(parts[:5]))
        animal_id = uuid.UUID('-'.join(parts[5:]))
        return adopter_id, animal_id
    except ValueError as e:
        raise ValueError(f"Invalid UUID in adoption ID: {adoption_id_str} - {e}")

@role_required(('staff', 'pengunjung_adopter'))
def adoption_detail(request, adoption_id): # adoption_id adalah string gabungan
    try:
        adopter_uuid, animal_uuid = _parse_adoption_id(adoption_id)

        with connection.cursor() as cursor:
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
            cursor.execute(query, [adopter_uuid, animal_uuid])
            
            adoption_data = cursor.fetchone()
            
            if not adoption_data:
                raise Http404(f"Adoption not found for adopter_id={adopter_uuid}, animal_id={animal_uuid}")
            
            mulai_adopsi = datetime.strptime(str(adoption_data[3]), '%Y-%m-%d').strftime('%d %B %Y')
            berhenti_adopsi = datetime.strptime(str(adoption_data[4]), '%Y-%m-%d').strftime('%d %B %Y')
            
            context = {
                'adoption': {
                    'id': adoption_id, # Kirim ID string gabungan asli ke template
                    'status_pembayaran': adoption_data[2],
                    'mulai_adopsi': mulai_adopsi,
                    'berhenti_adopsi': berhenti_adopsi,
                    'kontribusi_finansial': f"Rp {adoption_data[5]:,}",
                    'animal': {
                        'nama': adoption_data[6],
                        'jenis': adoption_data[7],
                        'kondisi': adoption_data[8]
                    },
                    'adopter': {
                        'username': adoption_data[9],
                        'total_kontribusi': f"Rp {adoption_data[10]:,}",
                        'nama_adopter': adoption_data[11],
                        'tipe_adopter': adoption_data[12]
                    }
                }
            }
        return render(request, 'adoption_detail.html', context)

    except ValueError as ve: # Tangkap error dari _parse_adoption_id
        raise Http404(f"Invalid adoption ID format in URL: {str(ve)}")
    except Http404: # Biarkan Http404 dari dalam view terlempar
        raise
    except Exception as e:
        raise # Melempar ulang error untuk debugging

@role_required(('staff', 'pengunjung_adopter'))
def register_adopter(request, animal_id=None):
    animal_uuid = None  # Initialize the variable
    
    if animal_id:
        try:
            animal_uuid = uuid.UUID(animal_id)
        except ValueError:
            raise Http404("Invalid animal ID format for registration.")

    if request.method == 'POST':
        username = request.POST.get('username')
        start_date_str = request.POST.get('start_date')
        adoption_period_months = request.POST.get('adoption_period')
        contribution_str = request.POST.get('contribution')
        
        # Get animal_id from form if not in URL
        if not animal_uuid and request.POST.get('animal_id'):
            try:
                animal_uuid = uuid.UUID(request.POST.get('animal_id'))
            except ValueError:
                return render(request, 'adoption_form.html', {
                    'error': "Format ID hewan tidak valid.",
                    'animal': None,
                    'animal_id': None
                })
        
        if not animal_uuid:
            return render(request, 'adoption_form.html', {
                'error': "ID hewan diperlukan untuk registrasi adopsi.",
                'animal': None,
                'animal_id': None
            })
        
        try:
            contribution = int(contribution_str)
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            months_to_add = int(adoption_period_months)

            with connection.cursor() as cursor:
                cursor.execute("SELECT id_adopter FROM sizopi.adopter WHERE username_adopter = %s", [username])
                adopter_result = cursor.fetchone()
                if not adopter_result:
                    raise Exception("Adopter tidak ditemukan")
                adopter_uuid = adopter_result[0]
                
                # Calculate end date
                new_month = start_date.month - 1 + months_to_add
                new_year = start_date.year + new_month // 12
                new_month = new_month % 12 + 1
                try:
                    end_date = start_date.replace(year=new_year, month=new_month)
                except ValueError:
                    end_date = start_date.replace(year=new_year, month=new_month, day=1) + timedelta(days=-1)

                cursor.execute("""
                    INSERT INTO sizopi.adopsi 
                    (id_adopter, id_hewan, status_pembayaran, tgl_mulai_adopsi, tgl_berhenti_adopsi, kontribusi_finansial)
                    VALUES (%s, %s, 'Tertunda', %s, %s, %s)
                """, [
                    adopter_uuid,
                    animal_uuid,
                    start_date_str,
                    end_date.strftime('%Y-%m-%d'),
                    contribution
                ])
                
                cursor.execute("""
                    UPDATE sizopi.adopter
                    SET total_kontribusi = total_kontribusi + %s
                    WHERE id_adopter = %s
                """, [contribution, adopter_uuid])
                
            return redirect('adoption_list')
            
        except Exception as e:
            error_message = str(e)
            animal_data_for_form = None
            
            # Now animal_uuid is always defined here
            if animal_uuid:
                with connection.cursor() as cursor_err:
                    cursor_err.execute("SELECT nama, spesies, status_kesehatan FROM sizopi.hewan WHERE id = %s", [animal_uuid])
                    animal_q_res = cursor_err.fetchone()
                    if animal_q_res:
                        animal_data_for_form = {
                            'id': str(animal_uuid), 
                            'nama': animal_q_res[0], 
                            'spesies': animal_q_res[1], 
                            'status_kesehatan': animal_q_res[2]
                        }
            
            return render(request, 'adoption_form.html', {
                'error': error_message, 
                'animal': animal_data_for_form, 
                'animal_id': str(animal_uuid) if animal_uuid else None
            })
    
    # GET request
    if animal_id:
        try:
            animal_uuid_get = uuid.UUID(animal_id)
            with connection.cursor() as cursor:
                cursor.execute("SELECT nama, spesies, status_kesehatan FROM sizopi.hewan WHERE id = %s", [animal_uuid_get])
                animal = cursor.fetchone()
                if not animal:
                    raise Http404("Hewan tidak ditemukan")
                context = {
                    'animal': {
                        'id': str(animal_uuid_get), 
                        'nama': animal[0], 
                        'spesies': animal[1], 
                        'status_kesehatan': animal[2]
                    },
                    'animal_id': str(animal_uuid_get)
                }
            return render(request, 'adoption_form.html', context)
        except ValueError:
            raise Http404("Format ID hewan tidak valid.")
    else:
        return render(request, 'adoption_form.html')
    
    # GET request
    if animal_id: # animal_id adalah string UUID dari URL
        try:
            animal_uuid_get = uuid.UUID(animal_id) # Validasi lagi untuk GET
            with connection.cursor() as cursor:
                cursor.execute("SELECT nama, spesies, status_kesehatan FROM sizopi.hewan WHERE id = %s", [animal_uuid_get])
                animal = cursor.fetchone()
                if not animal:
                    raise Http404("Hewan tidak ditemukan")
                context = {
                    'animal': {'id': str(animal_uuid_get), 'nama': animal[0], 'spesies': animal[1], 'status_kesehatan': animal[2]},
                    'animal_id': str(animal_uuid_get) # Kirim animal_id ke template
                }
            return render(request, 'adoption_form.html', context)
        except ValueError:
            raise Http404("Format ID hewan tidak valid.")
    else:
        return render(request, 'adoption_form.html') # Form untuk adopsi tanpa pra-seleksi hewan

@role_required(('staff', 'pengunjung_adopter'))
def extend_adoption(request, adoption_id=None): # adoption_id adalah string gabungan
    if not adoption_id:
        raise Http404("ID Adopsi diperlukan.")

    try:
        adopter_uuid, animal_uuid = _parse_adoption_id(adoption_id)
    except ValueError as e:
        raise Http404(str(e))

    if request.method == 'POST':
        end_date_str = request.POST.get('end_date')
        additional_contribution_str = request.POST.get('contribution')
        
        try:
            additional_contribution = int(additional_contribution_str)

            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE sizopi.adopsi
                    SET tgl_berhenti_adopsi = %s,
                        kontribusi_finansial = kontribusi_finansial + %s
                    WHERE id_adopter = %s AND id_hewan = %s
                """, [end_date_str, additional_contribution, adopter_uuid, animal_uuid])
                
                cursor.execute("""
                    UPDATE sizopi.adopter
                    SET total_kontribusi = total_kontribusi + %s
                    WHERE id_adopter = %s
                """, [additional_contribution, adopter_uuid])
                
            return redirect('adoption_detail', adoption_id=adoption_id) # Redirect kembali dengan ID gabungan
            
        except Exception as e:
            error_message = str(e)
            return render(request, 'adoption_extension_form.html', {'error': error_message, 'adoption_id': adoption_id}) # Sertakan adoption_id
    
    # GET request
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT a.tgl_mulai_adopsi, a.tgl_berhenti_adopsi, a.kontribusi_finansial,
                   h.nama, h.spesies,
                   ad.username_adopter
            FROM sizopi.adopsi a
            JOIN sizopi.hewan h ON a.id_hewan = h.id
            JOIN sizopi.adopter ad ON a.id_adopter = ad.id_adopter
            WHERE a.id_adopter = %s AND a.id_hewan = %s
        """, [adopter_uuid, animal_uuid])
        adoption_data = cursor.fetchone()
        
        if not adoption_data:
            raise Http404("Adopsi tidak ditemukan")
            
        context = {
            'adoption': {
                'id': adoption_id, # Kirim ID string gabungan
                'mulai_adopsi': adoption_data[0],
                'berhenti_adopsi': adoption_data[1],
                'kontribusi_finansial': adoption_data[2],
                'animal': {'nama': adoption_data[3], 'spesies': adoption_data[4]},
                'adopter': {'username': adoption_data[5]}
            },
            'adoption_id': adoption_id # Untuk form action
        }
    return render(request, 'adoption_extension_form.html', context)

@role_required(('staff', 'pengunjung_adopter'))
def end_adoption(request, adoption_id=None): # adoption_id adalah string gabungan
    if not adoption_id:
        return redirect('adoption_list') # Atau tampilkan error

    if request.method == 'POST': # Hanya proses jika POST
        try:
            adopter_uuid, animal_uuid = _parse_adoption_id(adoption_id)
            
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE sizopi.adopsi
                    SET tgl_berhenti_adopsi = CURRENT_DATE
                    WHERE id_adopter = %s AND id_hewan = %s
                """, [adopter_uuid, animal_uuid])
                
            return redirect('adoption_list')
            
        except ValueError as e: # Dari _parse_adoption_id
            return redirect('adoption_list') 
        except Exception as e: # Error database atau lainnya
            return redirect('adoption_detail', adoption_id=adoption_id) 
    
    return redirect('adoption_detail', adoption_id=adoption_id) # Redirect ke detail jika bukan POST

@role_required(('staff', 'pengunjung_adopter'))
def adopter_info(request, adopter_id=None): # adopter_id di sini adalah UUID adopter tunggal
    if not adopter_id:
        raise Http404("ID Adopter diperlukan.")
    
    try:
        adopter_uuid = uuid.UUID(adopter_id)
    except ValueError:
        raise Http404("Format ID adopter tidak valid.")

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT a.username_adopter, a.total_kontribusi,
                   COUNT(ad.id_adopter) as jumlah_adopsi_aktif
            FROM sizopi.adopter a
            LEFT JOIN sizopi.adopsi ad ON a.id_adopter = ad.id_adopter AND ad.tgl_berhenti_adopsi >= CURRENT_DATE
            WHERE a.id_adopter = %s
            GROUP BY a.id_adopter, a.username_adopter, a.total_kontribusi 
            -- GROUP BY a.username_adopter, a.total_kontribusi (Jika id_adopter adalah PK)
        """, [adopter_uuid]) # Gunakan UUID
        adopter = cursor.fetchone()
        
        if not adopter:
            raise Http404("Adopter tidak ditemukan")
            
        cursor.execute("""
            SELECT CAST(ad.id_adopter AS VARCHAR), CAST(ad.id_hewan AS VARCHAR), h.nama, h.spesies, 
                   ad.tgl_mulai_adopsi, ad.tgl_berhenti_adopsi, ad.kontribusi_finansial
            FROM sizopi.adopsi ad
            JOIN sizopi.hewan h ON ad.id_hewan = h.id
            WHERE ad.id_adopter = %s
            AND ad.tgl_berhenti_adopsi >= CURRENT_DATE
        """, [adopter_uuid]) # Gunakan UUID
        adoptions_data = cursor.fetchall()
        
        adoption_list_for_template = []
        for adoption_row in adoptions_data:
            adoption_list_for_template.append({
                'id': f"{adoption_row[0]}-{adoption_row[1]}", # Buat ID gabungan untuk link
                'nama_hewan': adoption_row[2],
                'jenis_hewan': adoption_row[3],
                'mulai_adopsi': adoption_row[4],
                'berhenti_adopsi': adoption_row[5],
                'kontribusi_finansial': adoption_row[6]
            })
        
        context = {
            'adopter': {
                'id': str(adopter_uuid), # Kirim ID adopter untuk referensi jika perlu
                'username': adopter[0],
                'total_kontribusi': f"Rp {adopter[1]:,}",
                'jumlah_adopsi': adopter[2]
            },
            'adoptions': adoption_list_for_template
        }
            
    return render(request, 'adopter_info.html', context)

@role_required(('staff', 'pengunjung_adopter'))
def adoption_certificate(request, adoption_id=None): # adoption_id adalah string gabungan
    if not adoption_id:
        # return render(request, 'adoption_certificate.html') # Halaman kosong
        raise Http404("ID Adopsi diperlukan.")

    try:
        adopter_uuid, animal_uuid = _parse_adoption_id(adoption_id)
    except ValueError as e:
        raise Http404(str(e))
            
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT h.nama, h.spesies,
                   ad.username_adopter, a.tgl_mulai_adopsi, a.tgl_berhenti_adopsi,
                   a.kontribusi_finansial
            FROM sizopi.adopsi a
            JOIN sizopi.hewan h ON a.id_hewan = h.id
            JOIN sizopi.adopter ad ON a.id_adopter = ad.id_adopter
            WHERE a.id_adopter = %s AND a.id_hewan = %s
        """, [adopter_uuid, animal_uuid]) # Gunakan UUID
        adoption_data = cursor.fetchone()
        
        if not adoption_data:
            raise Http404("Adopsi tidak ditemukan")
            
        context = {
            'adoption': {
                'id': adoption_id, # Kirim ID string gabungan
                'animal': {'nama': adoption_data[0], 'spesies': adoption_data[1]},
                'adopter': {'username': adoption_data[2]},
                'mulai_adopsi': adoption_data[3],
                'berhenti_adopsi': adoption_data[4],
                'kontribusi_finansial': f"Rp {adoption_data[5]:,}"
            }
        }
    return render(request, 'adoption_certificate.html', context)

@role_required(('staff', 'pengunjung_adopter'))
def animal_condition_report(request, adoption_id=None): # adoption_id adalah string gabungan
    if not adoption_id:
        raise Http404("ID Adopsi diperlukan.")

    try:
        adopter_uuid, animal_uuid = _parse_adoption_id(adoption_id)
    except ValueError as e:
        raise Http404(str(e))
            
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT h.nama, h.spesies, h.nama_habitat, 
                   ad.username_adopter, a.tgl_mulai_adopsi, a.tgl_berhenti_adopsi
            FROM sizopi.adopsi a
            JOIN sizopi.hewan h ON a.id_hewan = h.id
            JOIN sizopi.adopter ad ON a.id_adopter = ad.id_adopter
            WHERE a.id_adopter = %s AND a.id_hewan = %s
        """, [adopter_uuid, animal_uuid]) # Gunakan UUID
        adoption_data = cursor.fetchone()
        
        if not adoption_data:
            raise Http404("Adopsi tidak ditemukan")
        
        medical_records = []
        try:
            cursor.execute("""
                SELECT tanggal_pemeriksaan, nama_dokter, status_kesehatan, 
                       diagnosa, pengobatan, catatan_tindak_lanjut
                FROM sizopi.rekam_medis
                WHERE id_hewan = %s
                ORDER BY tanggal_pemeriksaan DESC
            """, [animal_uuid]) # Gunakan UUID hewan
            medical_records = cursor.fetchall()
        except Exception: # Tangkap error jika tabel tidak ada atau query gagal
            pass # Biarkan medical_records kosong
        
        condition_reports = []
        try:
            cursor.execute("""
                SELECT tanggal_laporan, kondisi_satwa, foto_kondisi, 
                       berat_badan, suhu_tubuh, nafsu_makan
                FROM sizopi.laporan_kondisi
                WHERE id_hewan = %s
                ORDER BY tanggal_laporan DESC
            """, [animal_uuid]) # Gunakan UUID hewan
            condition_reports = cursor.fetchall()
        except Exception:
            pass
        
        context = {
            'adoption': {
                'id': adoption_id, # Kirim ID string gabungan
                'animal': {
                    'nama': adoption_data[0], 'spesies': adoption_data[1], 
                    'habitat': adoption_data[2] if adoption_data[2] else 'N/A'
                },
                'adopter': {'username': adoption_data[3]},
                'periode': f"{adoption_data[4]} s/d {adoption_data[5]}"
            },
            'medical_records': medical_records,
            'condition_reports': condition_reports
        }
            
    return render(request, 'animal_condition_report.html', context)

@role_required(('staff', 'pengunjung_adopter'))
def create_animal_report(request, adoption_id=None): # adoption_id adalah string gabungan
    if not adoption_id:
        raise Http404("ID Adopsi diperlukan.")

    try:
        _, animal_uuid = _parse_adoption_id(adoption_id) # Hanya butuh animal_uuid untuk insert
    except ValueError as e:
        raise Http404(str(e))

    if request.method == 'POST':
        condition = request.POST.get('condition')
        photo = request.FILES.get('photo') # Handle file upload
        weight = request.POST.get('weight')
        temperature = request.POST.get('temperature')
        appetite = request.POST.get('appetite')
        
        try:
            weight_val = float(weight) if weight else None
            temperature_val = float(temperature) if temperature else None
        except ValueError:
            # Handle error konversi tipe jika input tidak valid
            error_message = "Berat atau suhu tidak valid."
            pass 

        try:
            with connection.cursor() as cursor:
                photo_data = photo.read() if photo else None
                cursor.execute("""
                    INSERT INTO sizopi.laporan_kondisi
                    (id_hewan, tanggal_laporan, kondisi_satwa, foto_kondisi,
                     berat_badan, suhu_tubuh, nafsu_makan)
                    VALUES (%s, CURRENT_DATE, %s, %s, %s, %s, %s)
                """, [animal_uuid, condition, photo_data, 
                      weight_val, temperature_val, appetite])
                
            return redirect('animal_condition_report', adoption_id=adoption_id)
            
        except Exception as e:
            error_message = str(e)
            with connection.cursor() as cursor_err:
                cursor_err.execute("""
                    SELECT h.nama, h.spesies, ad.username_adopter, a.tgl_mulai_adopsi, a.tgl_berhenti_adopsi
                    FROM sizopi.adopsi a
                    JOIN sizopi.hewan h ON a.id_hewan = h.id
                    JOIN sizopi.adopter ad ON a.id_adopter = ad.id_adopter
                    WHERE a.id_hewan = %s AND a.id_adopter = %s -- (Perlu adopter_uuid juga jika query ini digunakan)
                                                                -- atau cukup WHERE a.id_hewan = animal_uuid jika informasi adopter tidak krusial di sini
                """, [_parse_adoption_id(adoption_id)[0], animal_uuid]) 

                adoption_data_for_form = None # Isi dengan data yang relevan
                # ... (logika untuk mengisi adoption_data_for_form)

            return render(request, 'create_animal_report.html', {
                'error': error_message, 
                'adoption_id': adoption_id, 
                'adoption': adoption_data_for_form # atau context yang sesuai
            })
    
    try:
        adopter_uuid_get, animal_uuid_get = _parse_adoption_id(adoption_id)
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT h.nama, h.spesies,
                       ad.username_adopter, a.tgl_mulai_adopsi, a.tgl_berhenti_adopsi
                FROM sizopi.adopsi a
                JOIN sizopi.hewan h ON a.id_hewan = h.id
                JOIN sizopi.adopter ad ON a.id_adopter = ad.id_adopter
                WHERE a.id_adopter = %s AND a.id_hewan = %s
            """, [adopter_uuid_get, animal_uuid_get])
            adoption_data = cursor.fetchone()
            
            if not adoption_data:
                raise Http404("Adopsi tidak ditemukan")
                
            context_get = {
                'adoption': {
                    'id': adoption_id,
                    'animal': {'nama': adoption_data[0], 'spesies': adoption_data[1]},
                    'adopter': {'username': adoption_data[2]},
                    'periode': f"{adoption_data[3]} s/d {adoption_data[4]}"
                },
                'adoption_id': adoption_id # Untuk form action
            }
        return render(request, 'create_animal_report.html', context_get)
    except ValueError as e: # Dari _parse_adoption_id saat GET
        raise Http404(str(e))