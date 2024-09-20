from django.urls import path
from . import views

app_name = 'uid'

urlpatterns = [
    path('generate-uid/', views.generate_uid)
]