from django.contrib import admin, messages
from django.urls import path
from django.shortcuts import render, redirect
from django.http import HttpRequest

from deconfliction_service.node_utils import get_terms_with_multiple_definitions, is_any_node_present
from core.models import (ChildTermSet, SchemaLedger, Term, TermSet,
                         TransformationLedger)
from django_neomodel import admin as neomodel_admin
from core.models import NeoAlias, NeoContext, NeoDefinition, NeoTerm, NeoContextDescription
from core.utils import run_node_creation
from deconfliction_service.views import run_deconfliction
from django import forms
from uuid import uuid4
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
    alias = forms.CharField(required=True, help_text="Enter alias")  # Custom field
    definition = forms.CharField(required=True, help_text="Enter definition")  # Custom field
    context = forms.CharField(required=True, help_text="Enter context")  # Custom field
    context_description = forms.CharField(required=True, help_text="Enter context description")  # Custom field

    class Meta:
        model = NeoTerm
        fields = ['lcvid', 'alias', 'definition', 'context', 'context_description']

    def clean_definition(self):
        definition = self.cleaned_data.get('definition')

        get_terms_with_multiple_definitions()
        # Check if the definition already exists in the NeoDefinition model
        if is_any_node_present(NeoDefinition, definition=definition):
            raise forms.ValidationError(f"A definition of '{definition}' already exists.")
        
        return definition  # Return the cleaned value

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
            alias = form.cleaned_data['alias']
            definition = form.cleaned_data['definition']
            context = form.cleaned_data['context']
            context_description = form.cleaned_data['context_description']

            run_node_creation(alias, definition, context, context_description)

            # logger.info('Running Deconfliction')
            # definition_vector_embedding, deconfliction_status = run_deconfliction(alias, definition, context, context_description)
            # logger.info('Deconfliction complete')
            # logger.info(f'Deconfliction result: {deconfliction_status}')
            
            # if deconfliction_status == 'unique':
            #     termId = uuid4()
            #     obj.uid = ter
            #     alias_node,created = NeoAlias.get_or_create(alias=alias)
            #     definition_node = NeoDefinition(definition=definition, embedding=definition_vector_embedding)
            #     definition_node.save()
            #     context_node, created = NeoContext.get_or_create(context=context, context_description=context_description)
            #     context_description_node = NeoContextDescription.get_or_create(context_description=context_description)


            # alias_node, created = NeoAlias.get_or_create(alias=alias)
            # definition_node = NeoDefinition(definition=definition, embedding=definition_vector_embedding)
            # definition_node.save()
            # context_node, created = NeoContext.get_or_create(context=context)
            # definition_node.context.connect(context_node)
            # context_node.definition.connect(definition_node)

            
            # obj.save()
            # obj.alias.connect(alias_node)
            # obj.definition.connect(definition_node)
            # obj.context.connect(context_node)

            # if perfect dupe, return --- is perfect dupe - alias and definition and context are the same

            # im saving my neoterm: ------- unique case - if the definition is unique 

            # create neodefinition
                # embed the definition-------- end unique case
            
            # if embedding is similar -- --- - - - is duplicate - definition is same but alias and context are different
                # create neoalias
                # connect alias to neoterm

                # if context is new
                    # create neocontext
                    # connect context to neoalias
                    # connect context to neoterm
                
                # if context already exists
                    # connect context to neoalias
            
            # common tasks
            # (1) see if exists
            # (2) connect

            
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