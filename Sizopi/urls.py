"""
URL configuration for Sizopi project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from register.views import register

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('main.urls')),
    path('', include('manajemen_data_adopsi.urls')),
    path('', include('adopter_dan_riwayat.urls')),
    path('', include('pengaturan_profil.urls')),
    path('', include('login_and_logout.urls')),
    path('register/', include('register.urls')),
    path('animals/', include(('animals.urls', 'animals'), namespace='animals')),
    path('habitat/', include(('habitat.urls', 'habitat'), namespace='habitat')),
    path('rekam_medis/', include('rekam_medis_hewan.urls')),
    path('jadwal_pemeriksaan/', include('penjadwalan_pemeriksaan.urls')),
    path('pemberian_pakan/', include('pemberian_pakan.urls')),
]
