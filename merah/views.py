from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone

from .models import Animal, Adopter, Adoption, AdoptionReport
from .forms import UserForm, AdopterForm, AdoptionForm, AdoptionExtensionForm, AdoptionReportForm

def is_staff(user):
    return user.is_staff

@login_required
@user_passes_test(is_staff)
def adoption_list(request):
    animals = Animal.objects.all()
    return render(request, 'merah/adoption_list.html', {'animals': animals})

@login_required
@user_passes_test(is_staff)
def adoption_detail(request, adoption_id):
    adoption = get_object_or_404(Adoption, id=adoption_id)
    return render(request, 'merah/adoption_detail.html', {'adoption': adoption})

@login_required
@user_passes_test(is_staff)
def register_adopter(request, animal_id):
    animal = get_object_or_404(Animal, id=animal_id)
    
    # Check if animal is already adopted
    if animal.is_adopted():
        return redirect('adoption_list')
    
    if request.method == 'POST':
        # Check if using existing user or creating new one
        username = request.POST.get('username')
        adopter_type = request.POST.get('adopter_type')
        
        try:
            with transaction.atomic():
                # Try to get existing user or create new one
                try:
                    user = User.objects.get(username=username)
                except User.DoesNotExist:
                    # Create new user
                    user_form = UserForm(request.POST)
                    if user_form.is_valid():
                        user = user_form.save()
                    else:
                        raise ValueError("Invalid user data")
                
                # Create or get adopter
                try:
                    adopter = Adopter.objects.get(user=user)
                except Adopter.DoesNotExist:
                    adopter_form = AdopterForm(request.POST)
                    if adopter_form.is_valid():
                        adopter = adopter_form.save(commit=False)
                        adopter.user = user
                        adopter.save()
                    else:
                        raise ValueError("Invalid adopter data")
                
                # Create adoption
                adoption_form = AdoptionForm(request.POST)
                if adoption_form.is_valid():
                    adoption = adoption_form.save(commit=False)
                    adoption.animal = animal
                    adoption.adopter = adopter
                    adoption.save()
                    return redirect('adoption_list')
                else:
                    raise ValueError("Invalid adoption data")
        except ValueError as e:
            return render(request, 'merah/adoption_form.html', {
                'animal': animal,
                'error': str(e)
            })
    
    return render(request, 'merah/adoption_form.html', {'animal': animal})

@login_required
@user_passes_test(is_staff)
def extend_adoption(request, adoption_id):
    adoption = get_object_or_404(Adoption, id=adoption_id)
    
    if request.method == 'POST':
        form = AdoptionExtensionForm(request.POST, instance=adoption)
        if form.is_valid():
            form.save()
            return redirect('adoption_detail', adoption_id=adoption.id)
    else:
        form = AdoptionExtensionForm(instance=adoption)
    
    return render(request, 'merah/adoption_extension_form.html', {
        'form': form,
        'adoption': adoption
    })

@login_required
@user_passes_test(is_staff)
def adopter_info(request, adopter_id):
    adopter = get_object_or_404(Adopter, id=adopter_id)
    adoptions = Adoption.objects.filter(adopter=adopter).order_by('-start_date')
    
    return render(request, 'merah/adopter_info.html', {
        'adopter': adopter,
        'adoptions': adoptions
    })

@login_required
@user_passes_test(is_staff)
def end_adoption(request, adoption_id):
    adoption = get_object_or_404(Adoption, id=adoption_id)
    adoption.status = 'expired'
    adoption.end_date = timezone.now().date()
    adoption.save()
    return redirect('adoption_list')

@login_required
def adoption_certificate(request, adoption_id):
    adoption = get_object_or_404(Adoption, id=adoption_id)
    
    # Check if the requester is the adopter/staff
    if request.user.is_staff or (hasattr(request.user, 'adopter') and request.user.adopter == adoption.adopter):
        return render(request, 'merah/adoption_certificate.html', {'adoption': adoption})
    else:
        return redirect('home')  # ganti

@login_required
def animal_condition_report(request, adoption_id):
    adoption = get_object_or_404(Adoption, id=adoption_id)
    reports = AdoptionReport.objects.filter(adoption=adoption).order_by('-report_date')
    
    return render(request, 'merah/animal_condition_report.html', {
        'adoption': adoption,
        'reports': reports
    })

@login_required
@user_passes_test(is_staff)
def create_animal_report(request, adoption_id):
    adoption = get_object_or_404(Adoption, id=adoption_id)
    
    if request.method == 'POST':
        form = AdoptionReportForm(request.POST, request.FILES)
        if form.is_valid():
            report = form.save(commit=False)
            report.adoption = adoption
            report.report_date = timezone.now().date()
            report.save()
            return redirect('animal_condition_report', adoption_id=adoption.id)
    else:
        form = AdoptionReportForm()
    
    return render(request, 'merah/create_animal_report.html', {
        'form': form,
        'adoption': adoption
    })