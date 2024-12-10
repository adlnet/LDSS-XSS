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
     path('import-csv/', views.ImportCSVView.as_view(), name='import-csv'),
     path('export-terms/', views.ExportTermsView.as_view(), name='export-terms'),

     ## Downstream to send terms
     path('send-terms/', views.SendTermsToExternalAPI.as_view(), name='send-terms'),
     path('requested-terms/', views.RequestTermsFromExternalAPI.as_view(), name='requested-terms'),
     path('search/', views.Search.as_view(), name='search'),
]
