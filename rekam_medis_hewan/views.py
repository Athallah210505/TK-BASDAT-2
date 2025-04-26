from django.shortcuts import render

def show_rekam_medis(request):
    return render(request, 'show_rekam_medis.html')

def form_rekam_medis(request):
    return render(request, 'form_rekam_medis.html')

