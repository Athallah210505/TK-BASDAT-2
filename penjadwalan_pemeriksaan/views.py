from django.shortcuts import render

def show_jadwal_pemeriksaan(request):
    return render(request, 'show_jadwal_pemeriksaan.html')

def show_jadwal_satu_hewan(request):
    return render(request, 'show_jadwal_satu_hewan.html')