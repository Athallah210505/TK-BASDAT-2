from django.shortcuts import render, redirect
from django.contrib import messages


def profile_settings(request):
    """
    Render the profile settings page.
    This version doesn't require login.
    """
    # You can add dummy data for testing
    context = {
        # Show all sections for now
        'is_visitor': True,
        'is_vet': True,
        'is_staff': True,
    }
    
    return render(request, 'profile_settings.html', context)


def update_profile(request):
    """
    Handle profile update form submission.
    This version doesn't require login.
    """
    if request.method == 'POST':
        # In a real implementation, we would save the form data here
        messages.success(request, 'Profil berhasil diperbarui!')
    
    return redirect('profile_settings')


def change_password(request):
    """
    Handle password change form submission.
    This version doesn't require login.
    """
    if request.method == 'POST':
        # In a real implementation, we would validate and save the new password
        messages.success(request, 'Password berhasil diubah!')
    
    return redirect('profile_settings')