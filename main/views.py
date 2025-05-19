from django.shortcuts import render
from utils.decorators import role_required

# Create your views here.
def show_main(request):
    return render(request, 'main.html')

@role_required('staff')
def show_staff_dashboard(request):
    return render(request, 'staff_dashboard.html')

@role_required('dokter')
def dokter_hewan_dashboard(request):
    return render(request, 'dokter_hewan_dashboard.html')

@role_required('pengunjung')
def pengunjung_dashboard(request):
    return render(request, 'pengunjung_dashboard.html')

@role_required('penjaga_hewan')
def penjaga_hewan_dashboard(request):
    return render(request, 'penjaga_hewan_dashboard.html')

@role_required('pelatih_pertunjukan')
def pelatih_pertunjukan_dashboard(request):
    return render(request, 'pelatih_pertunjukan_dashboard.html')

@role_required('pengunjung_adopter')
def pengunjung_adopter_dashboard(request):
    return render(request, 'pengunjung_adopter_dashboard.html')

