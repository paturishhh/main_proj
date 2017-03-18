from django.shortcuts import render, HttpResponse
from .models import Node

def index(request):
    return HttpResponse("Hello World. You are at the index")

def test(request):
	# query set
	nodes = Node.objects.order_by('node_name')
	return render(request, 'test/test.html', {'nodes': nodes})
# Create your views here.
