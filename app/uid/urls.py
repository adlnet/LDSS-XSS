from django.urls import path
from . import views
from .views import export_to_postman
from .views import generate_report
from .views import UIDRepoViewSet

app_name = 'uid'

urlpatterns = [
    path('generate-uid/', views.generate_uid_node, name='generate_uid'),
    path('create-provider/', views.create_provider, name='create_provider'),
    path('create-lcvterm/', views.create_lcvterm, name='create_lcvterm'),
    path('success/', views.success_view, name='success'),
    path('export/<str:uid>/', export_to_postman, name='export_to_postman'),
    path('report/<str:echelon_level>/', generate_report, name='generate_report'),
    path('api/uid-repo/', UIDRepoViewSet.as_view({'get': 'list'}), name='uid-repo'),
]
