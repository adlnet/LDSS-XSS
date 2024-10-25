from django.contrib import admin
# from .models import Provider, LCVTerm
from .models import UIDCounterDjangoModel  # Import the Django model

# Admin registration for UIDCounterDjangoModel
@admin.register(UIDCounterDjangoModel)
class UIDCounterAdmin(admin.ModelAdmin):
    list_display = ('id', 'counter_value')
    search_fields = ('id',)

# @admin.register(Provider)
# class ProviderAdmin(admin.ModelAdmin):
#     list_display = ('uid', 'name')

# @admin.register(LCVTerm)
# class LCVTermAdmin(admin.ModelAdmin):
#     list_display = ('uid', 'term', 'ld_lcv_structure')

# Register additional models here.
