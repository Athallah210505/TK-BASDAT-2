from django.shortcuts import render

# Create your views here.
def show_main(request):
    return render(request, 'main.html')

def show_management(request):
    return render(request, 'management.html')

def show_atraksi_management(request):
    return render(request, 'atraksi_management.html')

def show_wahana_management(request):
    return render(request, 'wahana_management.html')

def  show_user_booking(request):
    return render(request, 'user_booking.html')

def show_admin_booking(request):
    return render(request, 'admin_booking.html')