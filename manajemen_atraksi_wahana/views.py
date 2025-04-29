
from django.shortcuts import render

def show_management(request):
    return render(request, 'management.html')

def show_atraksi_management(request):
    return render(request, 'atraksi_management.html')

def show_wahana_management(request):
    return render(request, 'wahana_management.html')
# Create your views here.
