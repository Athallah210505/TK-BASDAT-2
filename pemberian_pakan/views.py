from django.shortcuts import render

def show_pemberian_pakan(request):
    return render(request, 'show_pemberian_pakan.html')

def riwayat_pemberian_pakan(request):
    return render(request, 'riwayat_pemberian_pakan.html')