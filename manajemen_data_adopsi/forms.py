# from django import forms
# from django.contrib.auth.models import User
# from .models import Animal, Adopter, Adoption, AdoptionReport

# class UserForm(forms.ModelForm):
#     class Meta:
#         model = User
#         fields = ['username', 'first_name', 'last_name', 'email']

# class AdopterForm(forms.ModelForm):
#     class Meta:
#         model = Adopter
#         fields = ['adopter_type', 'address', 'contact']

# class AdoptionForm(forms.ModelForm):
#     class Meta:
#         model = Adoption
#         fields = ['start_date', 'end_date', 'contribution']
#         widgets = {
#             'start_date': forms.DateInput(attrs={'type': 'date'}),
#             'end_date': forms.DateInput(attrs={'type': 'date'}),
#         }

# class AdoptionExtensionForm(forms.ModelForm):
#     class Meta:
#         model = Adoption
#         fields = ['end_date', 'contribution']
#         widgets = {
#             'end_date': forms.DateInput(attrs={'type': 'date'}),
#         }
        
# class AdoptionReportForm(forms.ModelForm):
#     class Meta:
#         model = AdoptionReport
#         fields = ['condition', 'photo']