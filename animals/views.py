from django.shortcuts import render
from types import SimpleNamespace

# Menampilkan daftar satwa
from types import SimpleNamespace
from django.shortcuts import render

def animal_list(request):
    # Data dummy untuk melihat tampilan
    sample_animals = [
        SimpleNamespace(
            id=1,
            name='Simba',
            species='Singa',
            origin='Afrika',
            birth_date='2018-05-12',
            health_status='Sehat',
            habitat='Savana',
            photo_url='https://i.pinimg.com/236x/06/bc/e0/06bce0b581f157da6aa8ea0ebf769b9d.jpg'
        ),
        SimpleNamespace(
            id=2,
            name='Momo',
            species='Monyet Ekor Panjang',
            origin='Sumatra',
            birth_date='2020-02-20',
            health_status='Sakit Ringan',
            habitat='Hutan Tropis',
            photo_url='https://i.pinimg.com/474x/5d/c7/bb/5dc7bb34bb89d12a5126adcf0e39f4a1.jpg'
        ),
        SimpleNamespace(
            id=3,
            name='Bimo',
            species='Gajah Sumatra',
            origin='Sumatra',
            birth_date='2016-11-02',
            health_status='Sehat',
            habitat='Padang Rumput',
            photo_url='https://i.pinimg.com/236x/c3/df/63/c3df63ffd3c259796906e82236a671b5.jpg'
        ),
        SimpleNamespace(
            id=4,
            name='Luna',
            species='Serigala Abu-abu',
            origin='Amerika Utara',
            birth_date='2019-09-09',
            health_status='Cedera Ringan',
            habitat='Hutan Salju',
            photo_url='https://i.pinimg.com/236x/17/ef/57/17ef5717f09cd0dac10cd39086da7161.jpg'
        ),
        SimpleNamespace(
            id=5,
            name='Chika',
            species='Penyu Hijau',
            origin='Sulawesi',
            birth_date='2015-07-23',
            health_status='Sehat',
            habitat='Pantai',
            photo_url='https://i.pinimg.com/236x/63/f4/3a/63f43a867859044d15c09e291cd45acf.jpg'
        ),
    ]

    return render(request, 'animals/animal_list.html', {
        'animals': sample_animals,
    })


# Menambah data satwa
# TODO: tambahkan handling form submission
def animal_create(request):
    return render(request, 'animals/animal_form.html', {
        'animal': None,  # form kosong
        'habitats': [],  # TODO: ganti dengan queryset habitat
        'health_choices': [],  # TODO: ganti dengan HEALTH_STATUS_CHOICES
    })

# Mengedit data satwa
# TODO: fetch instance berdasarkan pk, handle form

def animal_update(request, pk):
    return render(request, 'animals/animal_form.html', {
        'animal': None,  # TODO: ganti dengan instance satwa
        'habitats': [],  # TODO: ganti dengan queryset habitat
        'health_choices': [],  # TODO: ganti dengan HEALTH_STATUS_CHOICES
    })

