from django.shortcuts import render

def  show_user_booking(request):
    return render(request, 'user_booking.html')

def show_admin_booking(request):
    return render(request, 'admin_booking.html')

def show_user_add_booking(request):
    return render(request, 'user_add_booking.html')

def show_user_edit_booking(request):
    return render(request, 'user_edit_booking.html')
