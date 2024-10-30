from django.contrib import admin
from .models import Provider, LCVTerm
from .models import ProviderDjangoModel, LCVTermDjangoModel
from .ccvmodels import CCVUpstream, CCVDownstream

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


# testing the admin features brought over from ccv: 

@admin.register(CCVUpstream)
class CCVUpstreamAdmin(admin.ModelAdmin):
    list_display = ('ccv_api_endpoint', 'ccv_api_endpoint_status')
    fields = [('ccv_api_endpoint', 'ccv_api_endpoint_status'), ]
    filter_horizontal = ['metadata_experiences', 'supplemental_experiences']


@admin.register(CCVDownstream)
class CCVDownstreamAdmin(admin.ModelAdmin):
    list_display = ('ccv_api_endpoint', 'ccv_api_endpoint_status')
    fields = [('ccv_api_endpoint', 'ccv_api_key', 'ccv_api_endpoint_status'),
              ('filter_records', 'filter_metadata'),
              ('source_name',)]
    filter_horizontal = ['composite_experiences',
                         'filter_records', 'filter_metadata']


admin.site.register(ProviderDjangoModel, ProviderAdmin)
admin.site.register(LCVTermDjangoModel, LCVTermAdmin)
