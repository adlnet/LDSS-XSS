from django.contrib import admin
from .models import Provider, LCVTerm
from .models import UIDCounterDjangoModel  # Import the Django model

# Admin registration for UIDCounterDjangoModel
@admin.register(UIDCounterDjangoModel)
class UIDCounterAdmin(admin.ModelAdmin):
    list_display = ('id', 'counter_value')
    search_fields = ('id',)

class ProviderAdmin(admin.ModelAdmin):
    list_display = ('uid', 'name')
    search_fields = ('name',)

class LCVTermAdmin(admin.ModelAdmin):
    list_display = ('uid', 'term')
    search_fields = ('term',)

admin.site.register(Provider, ProviderAdmin)
admin.site.register(LCVTerm, LCVTermAdmin)
