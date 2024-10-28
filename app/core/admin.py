from django.contrib import admin, messages
from django.urls import path
from django.shortcuts import render, redirect
from django.http import HttpRequest

from deconfliction_service.views import run_deconfliction
from core.models import (ChildTermSet, SchemaLedger, Term, TermSet,
                         TransformationLedger)
from django_neomodel import admin as neomodel_admin
from core.models import NeoAlias, NeoContext, NeoDefinition, NeoTerm, NeoContextDescription
from django import forms
from uuid import uuid4
import logging
from deconfliction_service.utils import ElasticsearchClient

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
    term = forms.CharField(required=True, help_text="Enter term")  # Custom field
    definition = forms.CharField(required=True, help_text="Enter definition")  # Custom field
    context = forms.CharField(required=True, help_text="Enter context")  # Custom field
    context_description = forms.CharField(required=True, help_text="Enter context description")  # Custom field

    # def validate_definition(self, definition):

    #     if definition is None:
    #         raise forms.ValidationError('Definition is required')
        
    #     check_definition_conflicts

    class Meta:
        model = NeoTerm
        fields = ['lcvid']

class NeoTermAdmin(admin.ModelAdmin):
    form = NeoTermAdminForm
    list_display = ('lcvid', 'uid')
    exclude = ['django_id', 'uid']

    def __init__(self,*args, **kwargs):
        
        super().__init__(*args, **kwargs)
        self.model.verbose_name = 'NeoTerm'
        self.model.verbose_name_plural = 'NeoTerms'


    def save_model(self, request, obj, form, change):
        try:
            if not obj.uid:
                obj.uid = str(uuid4())

            term = form.cleaned_data['term']
            definition = form.cleaned_data['definition']
            context = form.cleaned_data['context']
            context_description = form.cleaned_data['context_description']
            logger.info('Running Deconfliction')

            deconfliction_response = run_deconfliction(definition)

            es_client = ElasticsearchClient()
            es_client.connect()


            if deconfliction_response['type']=='duplicate':
                existing_term_uid = deconfliction_response['existingTerm']
                existing_term = NeoTerm.nodes.get(uid=existing_term_uid)
                messages.error(request, 'Duplicate definition detected. Creating Alias if applicable.')
                alias_node, created = NeoAlias.get_or_create(alias=term)
                existing_term.alias.connect(alias_node)
                alias_node.term.connect(existing_term)
                messages.info(request, 'Alias created for term: {}'.format(existing_term))
            if deconfliction_response['type']=='unique':

                messages.info(request, 'No duplicates found. Saving term.')
                index_document('xss_index',uid=obj.uid,definition_embedding=deconfliction_response["definition_embedding"])

            logger.info(deconfliction_response)

            logger.info(term)
            logger.info(definition)
            logger.info(context)
            logger.info(context_description)
            alias_node, created = NeoAlias.get_or_create(alias=term)
            definition_node = NeoDefinition(definition=definition)
            definition_node.save()
            context_node, created = NeoContext.get_or_create(context=context, context_description=context_description)
            definition_node.context.connect(context_node)
            context_node.definition.connect(definition_node)


            obj.save()
            obj.alias.connect(alias_node)
            obj.definition.connect(definition_node)
            obj.context.connect(context_node)

            
        except Exception as e:
            logger.error('Error saving NeoTerm: {}'.format(e))
            messages.error(request, 'Error saving NeoTerm: {}'.format(e))
            return
    

    def delete_model(self, request, obj) -> None:
        messages.error(request, 'Deleting terms is not allowed')

    def delete_queryset(self, request, queryset):
        """Prevent bulk deletion of NeoTerm objects and show a message."""
        messages.error(request, "You cannot delete terms.")


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