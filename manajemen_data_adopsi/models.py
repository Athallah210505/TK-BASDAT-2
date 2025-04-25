from django.db import models
from django.contrib.auth.models import User

class Animal(models.Model):
    name = models.CharField(max_length=100)
    species = models.CharField(max_length=100)
    condition = models.TextField()
    photo = models.ImageField(upload_to='animal_photos/', null=True, blank=True)
    
    def __str__(self):
        return f"{self.name} - {self.species}"
    
    def is_adopted(self):
        active_adoptions = self.adoption_set.filter(
            end_date__gte=models.functions.Now(),
            status='active'
        )
        return active_adoptions.exists()

class Adopter(models.Model):
    TYPE_CHOICES = (
        ('individual', 'Individual'),
        ('organization', 'Organization'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    adopter_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    address = models.TextField()
    contact = models.CharField(max_length=100)
    
    def __str__(self):
        return f"{self.user.username} ({self.get_adopter_type_display()})"

class Adoption(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    )
    
    animal = models.ForeignKey(Animal, on_delete=models.CASCADE)
    adopter = models.ForeignKey(Adopter, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    contribution = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    adoption_date = models.DateField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.animal.name} adopted by {self.adopter}"

class AdoptionReport(models.Model):
    adoption = models.ForeignKey(Adoption, on_delete=models.CASCADE)
    report_date = models.DateField()
    condition = models.TextField()
    photo = models.ImageField(upload_to='report_photos/', null=True, blank=True)
    
    def __str__(self):
        return f"Report for {self.adoption.animal.name} on {self.report_date}"