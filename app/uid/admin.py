from django.contrib import admin
from .models import Provider
# from .models import Provider, LCVTerm
from .models import ProviderDjangoModel, LCVTermDjangoModel, UIDRequestToken
# from .models import UIDCounterDjangoModel  # Import the Django model
#from .models import LastGeneratedUID

#@admin.register(LastGeneratedUID)
#class LastGeneratedUIDAdmin(admin.ModelAdmin):
#    list_display = ('uid')

# # Admin registration for UIDCounterDjangoModel
# @admin.register(UIDCounterDjangoModel)
# class UIDCounterAdmin(admin.ModelAdmin):
#     list_display = ('id', 'counter_value')
#     search_fields = ('id',)

class ProviderAdmin(admin.ModelAdmin):
    list_display = ('name', )
    search_fields = ('name', )

class LCVTermAdmin(admin.ModelAdmin):
    list_display = ('provider_name', 'term', 'echelon', 'structure')
    search_fields = ('provider_name', 'term', 'echelon', 'structure')

class UIDRequestAdmin(admin.ModelAdmin):
    list_display = ('provider_uid', 'echelon', 'termset', 'token', )
    search_fields = ('provider_uid', 'echelon', 'termset', 'token', )
    exclude = ('token', )

admin.site.register(ProviderDjangoModel, ProviderAdmin)
admin.site.register(LCVTermDjangoModel, LCVTermAdmin)
admin.site.register(UIDRequestToken, UIDRequestAdmin)
