from django.contrib import admin
from .models import Animal, Adopter, Adoption, AdoptionReport

class AnimalAdmin(admin.ModelAdmin):
    list_display = ('name', 'species', 'is_adopted')
    search_fields = ('name', 'species')

class AdopterAdmin(admin.ModelAdmin):
    list_display = ('user', 'adopter_type', 'contact')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')

class AdoptionAdmin(admin.ModelAdmin):
    list_display = ('animal', 'adopter', 'start_date', 'end_date', 'status')
    list_filter = ('status',)
    search_fields = ('animal__name', 'adopter__user__username')

class AdoptionReportAdmin(admin.ModelAdmin):
    list_display = ('adoption', 'report_date')
    list_filter = ('report_date',)
    search_fields = ('adoption__animal__name',)

admin.site.register(Animal, AnimalAdmin)
admin.site.register(Adopter, AdopterAdmin)
admin.site.register(Adoption, AdoptionAdmin)
admin.site.register(AdoptionReport, AdoptionReportAdmin)