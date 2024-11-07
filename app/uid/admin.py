from django.contrib import admin
from django.forms import ModelForm
from django.http import HttpRequest
from .models import Provider, UIDNode, UIDRequestNode
# from .models import Provider, LCVTerm
from .models import ProviderDjangoModel, LCVTermDjangoModel, UIDRequestToken
# from .models import UIDCounterDjangoModel  # Import the Django model
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
    list_display = ('provider_name', 'token', 'uid', )
    search_fields = ('provider_name', 'token', 'uid', )
    exclude = ('token', 'echelon', 'termset', 'uid', )

    def save_form(self, request: HttpRequest, form: ModelForm, change: bool):

        given_provider = form.cleaned_data["provider_name"]

        provider_already_exists = Provider.does_provider_exist(given_provider)
        if not provider_already_exists:
            new_provider = ProviderDjangoModel(given_provider)
            new_provider.save()
        
        requested_node = UIDRequestNode.create_requested_uid(given_provider)
        requested_node.save()

        form.cleaned_data["token"] = uuid4()
        form.cleaned_data["uid"] = requested_node.default_uid

        return super().save_form(request, form, change)

admin.site.register(ProviderDjangoModel, ProviderAdmin)
admin.site.register(LCVTermDjangoModel, LCVTermAdmin)
admin.site.register(UIDRequestToken, UIDRequestAdmin)
