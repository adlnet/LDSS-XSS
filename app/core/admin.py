from django.contrib import admin
from django.http import HttpRequest

from deconfliction_service.views import run_deconfliction
from core.models import (ChildTermSet, SchemaLedger, Term, TermSet,
                         TransformationLedger)
from django_neomodel import admin as neomodel_admin
from core.models import NeoAlias, NeoContext, NeoDefinition, NeoTerm
from django import forms

import logging

logger = logging.getLogger('dict_config_logger')

# Register your models here.
@admin.register(SchemaLedger)
class SchemaLedgerAdmin(admin.ModelAdmin):
    """Admin form for the SchemaLedger model"""
    list_display = ('schema_name', 'status', 'version',)
    fields = [('schema_name', 'schema_file', 'status',),
              ('major_version', 'minor_version', 'patch_version',)]

    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ('schema_name', 'schema_file',
                                           'major_version', 'minor_version',
                                           'patch_version')
        return self.readonly_fields

    def save_model(self, request, obj, form, change):
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(TransformationLedger)
class TransformationLedgerAdmin(admin.ModelAdmin):
    """Admin form for the TransformationLedger model"""
    list_display = ('id', 'source_schema', 'target_schema', 'status',)
    fields = [('source_schema', 'target_schema',),
              ('schema_mapping_file', 'status',)]

    # Override the foreign key fields to show the name and version in the
    # admin form instead of the ID
    def get_form(self, request, obj=None, **kwargs):
        form = super(TransformationLedgerAdmin, self).get_form(request,
                                                               obj,
                                                               **kwargs)
        form.base_fields['source_schema'].label_from_instance = \
            lambda obj: "{}".format(obj.iri)
        form.base_fields['target_schema'].label_from_instance = \
            lambda obj: "{}".format(obj.iri)
        return form


@admin.register(TermSet)
class TermSetAdmin(admin.ModelAdmin):
    """Admin form for the Term Set model"""
    list_display = ('iri', 'status', 'updated_by', 'modified',)
    fieldsets = (
        (None, {'fields': ('iri', 'name', 'version', 'uuid',)}),
        ('Availability', {'fields': ('status',)}),
    )
    readonly_fields = ('iri', 'updated_by', 'modified', 'uuid',)
    search_fields = ['iri', ]
    list_filter = ('status', 'name')

    def save_model(self, request, obj, form, change):
        """Overide save_model to pass along current user"""
        obj.updated_by = request.user
        return super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(childtermset=None)


@admin.register(ChildTermSet)
class ChildTermSetAdmin(TermSetAdmin):
    """Admin form for the Child Term Set model"""
    list_display = ('iri', 'status', 'parent_term_set', 'updated_by',
                    'modified',)
    fieldsets = (
        (None, {'fields': ('iri', 'name', 'uuid',)}),
        ('Availability', {'fields': ('status',)}),
        ('Parent', {'fields': ('parent_term_set',)}),
    )
    list_filter = ('status', ('parent_term_set',
                   admin.RelatedOnlyFieldListFilter))

    def get_queryset(self, request):
        return super(TermSetAdmin, self).get_queryset(request)


@admin.register(Term)
class TermAdmin(admin.ModelAdmin):
    """Admin form for the Term model"""
    list_display = ('iri', 'status', 'term_set', 'updated_by',
                    'modified', )
    fieldsets = (
        (None, {'fields': ('iri', 'name', 'uuid', 'description', 'status',)}),
        ('Info', {'fields': ('data_type', 'use', 'source',)}),
        ('Connections', {'fields': ('term_set', 'mapping',)}),
        ('Updated', {'fields': ('updated_by',), })
    )
    readonly_fields = ('iri', 'updated_by', 'modified', 'uuid',)
    filter_horizontal = ('mapping',)
    search_fields = ['iri', ]
    list_filter = ('status', ('term_set', admin.RelatedOnlyFieldListFilter))

    def save_model(self, request, obj, form, change):
        """Overide save_model to pass along current user"""
        obj.updated_by = request.user
        return super().save_model(request, obj, form, change)

    def get_form(self, request, obj=None, **kwargs):
        form = super(TermAdmin, self).get_form(request, obj, **kwargs)
        if obj is not None:
            form.base_fields['mapping'].queryset = Term.objects.exclude(
                iri__startswith=obj.root_term_set())
        return form

class NeoTermAdminForm(forms.ModelForm):
    definition = forms.CharField(required=False)
    context = forms.CharField(required=False)
    context_description = forms.CharField(required=False)

    class Meta:
        model = NeoTerm
        fields = ['term']

class NeoTermAdmin(admin.ModelAdmin):
    form = NeoTermAdminForm

    def save_model(self, request, obj, form, change):
        term = form.cleaned_data.get('term')
        definition = form.cleaned_data.get('definition')
        context = form.cleaned_data.get('context')
        context_description = form.cleaned_data.get('context description')
        try: 
            result = run_deconfliction()
            if result is not None:
                return redirect('admin:core_neoterm_changelist')
            

        #neoterm = {'term': term, 'definition': definition, 'context': context, 'context_description': context_description}
        
        #single_term_comparision(term, definition)
        #do cosine stuff
        # if cosine stuff valid 
        #save term
        except Exception as e:
            logger.error(f"Error in save_model: {e}")
            messages.error(request, f"Error in save_model: {e}")
            return
        logger.info(definition)
        obj.save()


neomodel_admin.register(NeoTerm, NeoTermAdmin)


class NeoAliasAdmin(admin.ModelAdmin):
    list_display = ('alias', 'term')


neomodel_admin.register(NeoAlias, NeoAliasAdmin)

class NeoContextAdmin(admin.ModelAdmin):
    list_display = ('context', 'context_description')
    readonly_fields = ('context', 'context_description')

neomodel_admin.register(NeoContext, NeoContextAdmin)

class NeoDefinitionAdmin(admin.ModelAdmin):
    list_display = ('definition',)
    readonly_fields = ('definition',)

neomodel_admin.register(NeoDefinition, NeoDefinitionAdmin)