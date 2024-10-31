from django.contrib import admin
from django.contrib import messages
from .models import Provider, LCVTerm
from .models import ProviderDjangoModel, LCVTermDjangoModel
from .ccvmodels import CCVUpstream, CCVDownstream

from .models import UIDCounterDjangoModel  # Import the Django model
#from .models import LastGeneratedUID

#@admin.register(LastGeneratedUID)
#class LastGeneratedUIDAdmin(admin.ModelAdmin):
#    list_display = ('uid')

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
