import uuid

from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models
##For encryption of key values
from encrypted_model_fields.fields import EncryptedTextField, EncryptedCharField
from django.forms import ValidationError
from django.urls import reverse

regex_check = (r'(?!(\A( \x09\x0A\x0D\x20-\x7E # ASCII '
               r'| \xC2-\xDF # non-overlong 2-byte '
               r'| \xE0\xA0-\xBF # excluding overlongs '
               r'| \xE1-\xEC\xEE\xEF{2} # straight 3-byte '
               r'| \xED\x80-\x9F # excluding surrogates '
               r'| \xF0\x90-\xBF{2} # planes 1-3 '
               r'| \xF1-\xF3{3} # planes 4-15 '
               r'| \xF4\x80-\x8F{2} # plane 16 )*\Z))')
 
    ###These ledgers are to help return query and from XIS original code, we may not need

class MetadataLedger(models.Model):
    """Model for MetadataLedger"""

    METADATA_VALIDATION_CHOICES = [('Y', 'Yes'), ('N', 'No')]
    RECORD_ACTIVATION_STATUS_CHOICES = [('Active', 'A'), ('Inactive', 'I')]
    RECORD_TRANSMISSION_STATUS_CHOICES = [('Successful', 'S'), ('Failed', 'F'),
                                          ('Pending', 'P'), ('Ready', 'R'),
                                          ('Cancelled', 'C')]
    composite_ledger_transmission_date = models.DateTimeField(blank=True,
                                                              null=True)
    composite_ledger_transmission_status = \
        models.CharField(max_length=10,
                         blank=True,
                         default='Ready',
                         choices=RECORD_TRANSMISSION_STATUS_CHOICES)
    date_deleted = models.DateTimeField(blank=True, null=True)
    date_inserted = models.DateTimeField(blank=True, null=True)
    date_validated = models.DateTimeField(blank=True, null=True)
    metadata = models.JSONField(blank=True,
                                validators=[RegexValidator
                                            (regex=regex_check,
                                             message="Wrong Format Entered")])
    metadata_hash = models.CharField(max_length=200)
    metadata_key = models.CharField(max_length=200)
    metadata_key_hash = models.CharField(max_length=200)
    metadata_validation_status = \
        models.CharField(max_length=10, blank=True,
                         choices=METADATA_VALIDATION_CHOICES)
    provider_name = models.CharField(max_length=255, blank=True)
    record_status = models.CharField(max_length=10, blank=True,
                                     choices=RECORD_ACTIVATION_STATUS_CHOICES)
    unique_record_identifier = models.CharField(max_length=250,
                                                primary_key=True)
    updated_by = models.CharField(max_length=10, blank=True, default='System')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL,
                                   on_delete=models.PROTECT,
                                   related_name="created_metadata",
                                   blank=True, null=True)


class SupplementalLedger(models.Model):
    """Model for SupplementalLedger"""

    RECORD_ACTIVATION_STATUS_CHOICES = [('Active', 'A'), ('Inactive', 'I')]
    RECORD_TRANSMISSION_STATUS_CHOICES = [('Successful', 'S'),
                                          ('Failed', 'F'),
                                          ('Pending', 'P'),
                                          ('Ready', 'R'),
                                          ('Cancelled', 'C')]

    composite_ledger_transmission_date = models.DateTimeField(blank=True,
                                                              null=True)
    composite_ledger_transmission_status = \
        models.CharField(max_length=10,
                         blank=True,
                         default='Ready',
                         choices=RECORD_TRANSMISSION_STATUS_CHOICES)
    date_deleted = models.DateTimeField(blank=True, null=True)
    date_inserted = models.DateTimeField(blank=True, null=True)
    metadata = models.JSONField(null=True, blank=True,
                                validators=[RegexValidator
                                            (regex=regex_check,
                                             message="Wrong Format Entered")])
    metadata_hash = models.TextField(max_length=200)
    metadata_key = models.TextField(max_length=200)
    metadata_key_hash = models.CharField(max_length=200)
    provider_name = models.CharField(max_length=255, blank=True)
    record_status = models.CharField(max_length=10, blank=True,
                                     choices=RECORD_ACTIVATION_STATUS_CHOICES)
    unique_record_identifier = models.CharField(max_length=250,
                                                primary_key=True)
    updated_by = models.CharField(max_length=10, blank=True, default='System')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL,
                                   on_delete=models.PROTECT,
                                   related_name="created_supplemental_data",
                                   blank=True, null=True)


class CompositeLedger(models.Model):
    """Model for CompositeLedger"""

    RECORD_ACTIVATION_STATUS_CHOICES = [('Active', 'A'), ('Inactive', 'I')]
    RECORD_TRANSMISSION_STATUS_CHOICES = [('Successful', 'S'), ('Failed', 'F'),
                                          ('Pending', 'P'),
                                          ('Ready', 'R'),
                                          ('Cancelled', 'C')]
    date_deleted = models.DateTimeField(blank=True, null=True)
    date_inserted = models.DateTimeField(blank=True, null=True)
    date_transmitted = models.DateTimeField(blank=True, null=True)
    metadata = models.JSONField(blank=True)
    metadata_hash = models.TextField(max_length=200)
    metadata_key = models.TextField(max_length=200)
    metadata_key_hash = models.CharField(max_length=200)
    metadata_transmission_status = \
        models.CharField(max_length=10, blank=True,
                         default='Ready',
                         choices=RECORD_TRANSMISSION_STATUS_CHOICES)
    metadata_transmission_status_code = models.CharField(max_length=200,
                                                         blank=True)
    provider_name = models.CharField(max_length=255, blank=True)
    record_status = models.CharField(max_length=10, blank=True,
                                     choices=RECORD_ACTIVATION_STATUS_CHOICES)
    unique_record_identifier = models.UUIDField(primary_key=True,
                                                default=uuid.uuid4,
                                                editable=False)
    updated_by = models.CharField(max_length=10, blank=True)
    metadata_transmission_status_neo4j = \
        models.CharField(max_length=10, blank=True,
                         default='Ready',
                         choices=RECORD_TRANSMISSION_STATUS_CHOICES)


#### downstream filters,

class FilterRecord(models.Model):
    """Model for Filtering Composite Ledger Experiences for XIS Syndication """
    EQUAL = 'EQUAL'
    UNEQUAL = 'UNEQUAL'
    CONTAINS = 'CONTAINS'

    COMPARATORS = [
        (EQUAL, 'Equal'),
        (UNEQUAL, 'Not Equal'),
        (CONTAINS, 'Contains')]

    field_name = models.CharField(
        help_text='Enter the field path', max_length=255)

    comparator = models.CharField(max_length=200, choices=COMPARATORS)

    field_value = models.CharField(
        help_text='Enter the field value', max_length=255, blank=True)

    def __str__(self):
        """String for representing the Model object."""
        return ' '.join([self.field_name, self.comparator, self.field_value])

    def __root_filter(self, queryset):
        """run a query for filtering based on root data"""
        # if using EQUAL, perform a case insensitive exact filter on queryset
        if (self.comparator == self.EQUAL):
            return queryset.filter(
                **{f"{self.field_name}__iexact": self.field_value})
        # if using UNEQUAL, perform a case insensitive exact exclusion
        # on queryset
        elif (self.comparator == self.UNEQUAL):
            return queryset.exclude(
                **{f"{self.field_name}__iexact": self.field_value})
        # if using CONTAINS, perform a case insensitive contains filter
        # on queryset
        elif (self.comparator == self.CONTAINS):
            return queryset.filter(
                **{f"{self.field_name}__icontains": self.field_value})

    def __simple_metadata_filter(self, queryset):
        """run a simple query to filter based on metadata"""
        # if using EQUAL or CONTAINS make a quick query to remove elements
        # that are missing the filter value in metadata
        if (self.comparator == self.EQUAL or self.comparator == self.CONTAINS):
            return queryset.filter(metadata__icontains=self.field_value)
        return queryset

    def __metadata_filter(self, queryset):
        """run the more strict query to filter metadata"""
        return_qs = queryset
        # iterate over each item in the queryset
        for exp in queryset:
            # iterate over the fields within metadata to the field
            try:
                path = self.field_name.split('.')[1:]
                metadata = exp.metadata
                for step in path:
                    metadata = metadata[step]
            # if the field does not exist, use an empty string
            except Exception:
                metadata = ''
            # cast metadata field retrieved to a string and exclude items that
            # do not match
            return_qs = self.__check_match(return_qs, exp, metadata)

        return return_qs

    def __check_match(self, return_qs, exp, metadata):
        """remove non-matching items"""
        if (self.comparator == self.EQUAL):
            if self.field_value != str(metadata):
                return_qs = return_qs.exclude(pk=exp.pk)
        elif (self.comparator == self.UNEQUAL):
            if self.field_value == str(metadata):
                return_qs = return_qs.exclude(pk=exp.pk)
        elif (self.comparator == self.CONTAINS):
            if self.field_value not in str(metadata):
                return_qs = return_qs.exclude(pk=exp.pk)
        return return_qs

    def apply_filter(self, queryset):
        """Filter the queryset using this filter"""
        if ('.' in self.field_name):
            return self.__metadata_filter(
                self.__simple_metadata_filter(queryset))
        else:
            return self.__root_filter(queryset)


class FilterMetadata(models.Model):
    """Model for Filtering Metadata within Composite Ledger Experiences for
    XIS Syndication """
    INCLUDE = 'INCLUDE'
    EXCLUDE = 'EXCLUDE'

    OPERATIONS = [
        (INCLUDE, 'Include'),
        (EXCLUDE, 'Exclude')]

    field_name = models.CharField(
        help_text='Enter the field path', max_length=255)

    operation = models.CharField(max_length=200, choices=OPERATIONS)

    def __str__(self):
        """String for representing the Model object."""
        return ' '.join([self.operation, self.field_name])


    ####
## TODO - may need to change fields to not allow null
class CCVUpstream(models.Model):
    """Model for Upstream CCV communication """
    ACTIVE = 'ACTIVE'
    INACTIVE = 'INACTIVE'

    STATUS = [
        (ACTIVE, 'Active'),
        (INACTIVE, 'Inactive')]

    ccv_api_endpoint = models.CharField(
        max_length=200,
        help_text='Enter the CCV Instance API endpoint',
        null=True,
        blank=False
    )

    ccv_api_endpoint_status = models.CharField(max_length=200, choices=STATUS)

    ccv_api_username = EncryptedCharField(
        max_length=150,
        help_text='Enter the API username',
         null=True,
        blank=False
    )
    
    ccv_api_password =EncryptedCharField(
        max_length=150,
        help_text='Enter the API password',
         null=True,
        blank=False
    )

    ccv_api_key = EncryptedCharField(
        max_length=150,
        help_text='Enter the API key',
         null=True,
        blank=False
    )

    metadata_experiences = models.ManyToManyField(
        MetadataLedger, related_name='ccv_source', blank=True)
    supplemental_experiences = models.ManyToManyField(
        SupplementalLedger, related_name='ccv_source', blank=True)

    def __str__(self):
        """String for representing the Model object."""
        return f'{self.ccv_api_endpoint}'


class CCVDownstream(models.Model):
    """Model for Downstream CCV Communication """
    ACTIVE = 'ACTIVE'
    INACTIVE = 'INACTIVE'

    STATUS = [
        (ACTIVE, 'Active'),
        (INACTIVE, 'Inactive')]

    ccv_api_endpoint = models.CharField(
        max_length=200,
        help_text='Enter the CCV Instance API endpoint'
    )

    ccv_api_endpoint_status = models.CharField(max_length=200, choices=STATUS)

    ccv_api_key = models.CharField(
        help_text="Enter the CCV API Key",
        max_length=128
    )

    source_name = models.CharField(
        max_length=200, help_text='Enter the name to send data as')

    composite_experiences = models.ManyToManyField(
        CompositeLedger, related_name='ccv_destination', blank=True)

    filter_records = models.ManyToManyField(
        FilterRecord, related_name='ccv_downstream', blank=True)
    filter_metadata = models.ManyToManyField(
        FilterMetadata, related_name='ccv_downstream', blank=True)

    def __str__(self):
        """String for representing the Model object."""
        return f'{self.ccv_api_endpoint}'

    def determine_fields(self):
        """Determines the fields to use from the filter_metadata objects, and
        returns the fields as a tuple of lists include, exclude"""
        exclude = [field.field_name for field in self.filter_metadata.all().
                   filter(operation=FilterMetadata.EXCLUDE)]
        include = [field.field_name for field in self.filter_metadata.all().
                   filter(operation=FilterMetadata.INCLUDE)]
        return include, exclude

    def apply_filter(self, queryset=CompositeLedger.objects.all()):
        """Filter the queryset using this filter"""
        queryset = queryset.filter(
            record_status='Active').exclude(ccv_destination__pk=self.pk)
        # iterate FilterRecords to apply filters to queryset
        for record_filter in self.filter_records.all():
            queryset = record_filter.apply_filter(queryset)

        return queryset
   