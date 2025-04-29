from django.shortcuts import render

# Create your views here.
def show_main(request):
    return render(request, 'main.html')

def show_staff_dashboard(request):
    return render(request, 'staff_dashboard.html')

def dokter_hewan_dashboard(request):
    return render(request, 'dokter_hewan_dashboard.html')

def pengunjung_dashboard(request):
    return render(request, 'pengunjung_dashboard.html')

def penjaga_hewan_dashboard(request):
    return render(request, 'penjaga_hewan_dashboard.html')

def pelatih_pertunjukan_dashboard(request):
    return render(request, 'pelatih_pertunjukan_dashboard.html')


