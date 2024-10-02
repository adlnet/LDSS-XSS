from django.urls import path
from rest_framework.routers import DefaultRouter

from api import views

router = DefaultRouter()

app_name = 'api'

urlpatterns = [
     path('schemas/', views.SchemaLedgerDataView.as_view(),
         name='schemaledger'),
     path('mappings/', views.TransformationLedgerDataView.as_view(),
         name='transformationledger'),
     path('json-ld/<path:pk>', views.JSONLDDataView.as_view(),
         name='json-ld'),
     path('csv-upload/', views.CSVUploadView.as_view(), name='csv-upload'),
]
