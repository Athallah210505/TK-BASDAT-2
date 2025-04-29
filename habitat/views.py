from django.shortcuts import render

# Create your views here.
def habitat_list(request):
    return render(request, 'habitats/habitat_list.html')

def habitat_create(request):
    return render(request, 'habitats/habitat_create.html')

def habitat_detail(request):
    return render(request, 'habitats/habitat_detail.html')