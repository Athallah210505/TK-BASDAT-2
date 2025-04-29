from django.shortcuts import render

def adoption_list(request):
    return render(request, 'adoption_list.html')  

def adoption_detail(request, adoption_id):
    return render(request, 'adoption_detail.html')

def register_adopter(request, animal_id):
    return render(request, 'adoption_form.html')

def extend_adoption(request, adoption_id):
    return render(request, 'adoption_extension_form.html')

def end_adoption(request, adoption_id):
    return render(request, 'adoption_list.html')

def adopter_info(request, adopter_id):
    return render(request, 'adopter_info.html')

def adoption_certificate(request, adoption_id):
    return render(request, 'adoption_certificate.html')

def animal_condition_report(request, adoption_id):
    return render(request, 'animal_condition_report.html')

def create_animal_report(request, adoption_id):
    return render(request, 'create_animal_report.html')

def register_adopter_no_id(request):
    return render(request, 'adoption_form.html', {'animal_id': None})

def extend_adoption_no_id(request):
    return render(request, 'adoption_extension_form.html', {'adoption_id': None})

def end_adoption_no_id(request):
    return render(request, 'adoption_list.html', {'message': 'Silakan pilih adopsi yang akan diakhiri'})

def adopter_info_no_id(request):
    return render(request, 'adopter_info.html', {'adopter_id': None})

def adoption_certificate_no_id(request):
    return render(request, 'adoption_certificate.html', {'adoption_id': None})

def animal_condition_report_no_id(request):
    return render(request, 'animal_condition_report.html', {'adoption_id': None})

def create_animal_report_no_id(request):
    return render(request, 'create_animal_report.html', {'adoption_id': None})