from django.contrib import admin, messages
from django import forms
from django.urls import path, reverse
from django.shortcuts import render
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
import xml.etree.ElementTree as ET

from core.exceptions import MissingColumnsError, MissingRowsError, TermCreationError
from core.models import (ChildTermSet, SchemaLedger, Term, TermSet,
                         TransformationLedger, NeoTerm)
from .views import export_terms_as_json, export_terms_as_xml

from django_neomodel import admin as neo_admin
import logging
import pandas as pd

logger = logging.getLogger('dict_config_logger')


class CSVUploadForm(forms.Form):
    csv_file = forms.FileField()


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
                    'modified',)
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

class NeoTermAdmin(admin.ModelAdmin):
    list_display = ('term', 'definition', 'context_description', 'context')
    change_list_template = 'admin/neoterm_change_list.html'
    actions = ['export_as_json', 'export_as_xml', 'upload_csv']

    REQUIRED_COLUMNS = [
        field.name.replace("_", " ").title() for field in NeoTerm._meta.get_fields()
        if hasattr(field, 'required') and field.required
    ]

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('upload-csv/', self.upload_csv),
            path('admin/export-terms-json/', export_terms_as_json, name='export_terms_as_json'),
            path('admin/export-terms-xml/', export_terms_as_xml, name='export_terms_as_xml')
        ]
        return my_urls + urls
    

    def upload_csv(self, request):
        logger.info('Uploading CSV file...')
        if request.method == 'POST':
            form = CSVUploadForm(request.POST, request.FILES)
            if form.is_valid():
                csv_file = form.cleaned_data['csv_file']
                try:
                    data = self.validate_csv_file(csv_file)
                    self.create_terms_from_csv(data['data_frame'])
                    messages.success(request, 'CSV file uploaded successfully.')
                    return HttpResponseRedirect(reverse('admin:core_neoterm_changelist'))

                except MissingColumnsError as e:
                    messages.error(request, f"Missing required columns: {', '.join(e.missing_columns)}")
                except MissingRowsError as e:
                    for row in e.missing_rows:
                        indices_message = ', '.join(map(str, row['row_indices'][:5])) + (' and more' if len(row['row_indices']) > 5 else '')
                        messages.error(request, f"Missing data in column '{row['column']}' for row {indices_message}")
                except TermCreationError as e:
                    messages.error(request, "Error creating terms from CSV file.")
                except Exception as e:
                    messages.error(request, str(e))

        else:
            form = CSVUploadForm()
        return render(request, 'upload_csv.html', {'form': form})

    def validate_csv_file(self, csv_file):
        if not csv_file.name.endswith('.csv'):
            raise ValueError('The file extension is not .csv')

        try:
            logger.info('Validating CSV file...')
            df = pd.read_csv(csv_file)
            logger.info(f'{len(df)} rows found in CSV file.')
        except pd.errors.EmptyDataError:
            raise ValueError('The CSV file is empty.')
        except pd.errors.ParserError:
            raise ValueError('The CSV file is malformed or not valid.')

        missing_columns = self.check_missing_columns(df)
        if missing_columns:
            raise MissingColumnsError(missing_columns)

        missing_rows = self.check_missing_rows(df)
        if missing_rows:
            raise MissingRowsError(missing_rows)

        return {'data_frame': df}
    
    def check_missing_columns(self, df):
        missing_columns = [col for col in NeoTermAdmin.REQUIRED_COLUMNS if col not in df.columns]
        return missing_columns

    def check_missing_rows(self, df):
        missing_rows = {}

        for index, row in df.iterrows():
            for column in NeoTermAdmin.REQUIRED_COLUMNS:
                if pd.isna(row[column]) or row[column].strip() == '':
                    if column not in missing_rows:
                        missing_rows[column] = []
                    missing_rows[column].append(index + 1)

        return [{'column': column, 'row_indices': indices} for column, indices in missing_rows.items()]

    def create_terms_from_csv(self, df):
        logger.info('Creating terms from CSV file...')
        logger.info(f'{len(df)} rows found in data frame file.')

        for index, row in df.iterrows():
            try:
                logger.info(f"This is the term for index {index}: {row['Term']}")
                term = NeoTerm(
                    term=row['Term'],
                    definition=row['Definition'],
                    context=row['Context'],
                    context_description=row['Context Description']
                )
                term.save()
            except Exception as e:
                logger.error(f'Error creating term for index {index}: {str(e)}')
                raise TermCreationError(f'Failed to create term for row {index + 1}: {str(e)}')

        logger.info(f'{len(df)} terms created from CSV file.')

neo_admin.register(NeoTerm, NeoTermAdmin)