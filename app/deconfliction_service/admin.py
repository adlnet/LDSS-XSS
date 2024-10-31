from django.contrib import admin
from django.urls import path
from django.db import models
from django.shortcuts import redirect
from . import views

class Deconfliction(models.Model):
    class Meta:
        verbose_name_plural = "Deconfliction"
        managed = False 


class DeconflictionAdmin(admin.ModelAdmin):
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('', self.admin_site.admin_view(self.redirect_to_deconfliction),
                 name='deconfliction_service_deconfliction_changelist'),
            path('deconfliction/', 
                 self.admin_site.admin_view(views.deconfliction_admin_view),
                 name='admin_deconfliction_view'),
            path('resolve-collision/<int:id_1>/<int:id_2>/',
                self.admin_site.admin_view(views.resolve_collision),
                name='admin_resolve_collision') 
        ]
        return custom_urls + urls
    
    def redirect_to_deconfliction(self, request):
        """Redirect the default list view to our custom view"""
        return redirect('admin:admin_deconfliction_view')
    
    def has_add_permission(self, request):
        """Disable add permission since this is just for the custom view"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable change permission since this is just for the custom view"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Disable delete permission since this is just for the custom view"""
        return False
    
    def has_view_permission(self, request, obj=None):
        """Enable view permission to allow access to the custom view"""
        return True

admin.site.register(Deconfliction, DeconflictionAdmin)