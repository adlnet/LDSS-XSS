from django.urls import path
from rest_framework.routers import DefaultRouter

from ccv import views

urlpatterns = [
    path('data-ingest/', views.CCVDataIngest.as_view(), name='data-ingest'),
]