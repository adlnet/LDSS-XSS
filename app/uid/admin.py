from django.contrib import admin

from django.contrib import messages
from .ccvmodels import CCVUpstream, CCVDownstream

from django.forms import ModelForm
from django.http import HttpRequest
from .models import Provider, UIDNode, UIDRequestNode
# from .models import Provider, LCVTerm
from .models import ProviderDjangoModel, LCVTermDjangoModel, UIDRequestToken

#from .models import LastGeneratedUID
from uuid import uuid4

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
    list_display = ('provider_name', 'token', 'uid', 'uid_chain', )
    search_fields = ('provider_name', 'token', 'uid', 'uid_chain', )
    exclude = ('token', 'echelon', 'termset', 'uid', 'uid_chain' )


# testing the admin features brought over from ccv: 

# we need to add API credentials username, pasword, API key.
@admin.register(CCVUpstream)
class CCVUpstreamAdmin(admin.ModelAdmin):
    list_display = ('ccv_api_endpoint', 'ccv_api_endpoint_status', 'ccv_api_username')
    fields = [('ccv_api_endpoint', 'ccv_api_endpoint_status', 'ccv_api_username', 'ccv_api_password', 'ccv_api_key'), ]
    filter_horizontal = ['metadata_experiences', 'supplemental_experiences']

## Alert user that save was successfull
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        messages.success(request, "API endpoint and credentials have been successfully configured.")

@admin.register(CCVDownstream)
class CCVDownstreamAdmin(admin.ModelAdmin):
    list_display = ('ccv_api_endpoint', 'ccv_api_endpoint_status')
    fields = [('ccv_api_endpoint', 'ccv_api_key', 'ccv_api_endpoint_status')]


admin.site.register(ProviderDjangoModel, ProviderAdmin)
admin.site.register(LCVTermDjangoModel, LCVTermAdmin)
admin.site.register(UIDRequestToken, UIDRequestAdmin)
