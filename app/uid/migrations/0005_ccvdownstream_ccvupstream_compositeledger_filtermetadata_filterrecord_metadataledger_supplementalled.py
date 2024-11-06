# Generated by Django 3.2.25 on 2024-10-31 20:37

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import encrypted_model_fields.fields
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('uid', '0004_auto_20241031_1227'),
    ]

    operations = [
        migrations.CreateModel(
            name='CompositeLedger',
            fields=[
                ('date_deleted', models.DateTimeField(blank=True, null=True)),
                ('date_inserted', models.DateTimeField(blank=True, null=True)),
                ('date_transmitted', models.DateTimeField(blank=True, null=True)),
                ('metadata', models.JSONField(blank=True)),
                ('metadata_hash', models.TextField(max_length=200)),
                ('metadata_key', models.TextField(max_length=200)),
                ('metadata_key_hash', models.CharField(max_length=200)),
                ('metadata_transmission_status', models.CharField(blank=True, choices=[('Successful', 'S'), ('Failed', 'F'), ('Pending', 'P'), ('Ready', 'R'), ('Cancelled', 'C')], default='Ready', max_length=10)),
                ('metadata_transmission_status_code', models.CharField(blank=True, max_length=200)),
                ('provider_name', models.CharField(blank=True, max_length=255)),
                ('record_status', models.CharField(blank=True, choices=[('Active', 'A'), ('Inactive', 'I')], max_length=10)),
                ('unique_record_identifier', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('updated_by', models.CharField(blank=True, max_length=10)),
                ('metadata_transmission_status_neo4j', models.CharField(blank=True, choices=[('Successful', 'S'), ('Failed', 'F'), ('Pending', 'P'), ('Ready', 'R'), ('Cancelled', 'C')], default='Ready', max_length=10)),
            ],
        ),
        migrations.CreateModel(
            name='FilterMetadata',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('field_name', models.CharField(help_text='Enter the field path', max_length=255)),
                ('operation', models.CharField(choices=[('INCLUDE', 'Include'), ('EXCLUDE', 'Exclude')], max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='FilterRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('field_name', models.CharField(help_text='Enter the field path', max_length=255)),
                ('comparator', models.CharField(choices=[('EQUAL', 'Equal'), ('UNEQUAL', 'Not Equal'), ('CONTAINS', 'Contains')], max_length=200)),
                ('field_value', models.CharField(blank=True, help_text='Enter the field value', max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='SupplementalLedger',
            fields=[
                ('composite_ledger_transmission_date', models.DateTimeField(blank=True, null=True)),
                ('composite_ledger_transmission_status', models.CharField(blank=True, choices=[('Successful', 'S'), ('Failed', 'F'), ('Pending', 'P'), ('Ready', 'R'), ('Cancelled', 'C')], default='Ready', max_length=10)),
                ('date_deleted', models.DateTimeField(blank=True, null=True)),
                ('date_inserted', models.DateTimeField(blank=True, null=True)),
                ('metadata', models.JSONField(blank=True, null=True, validators=[django.core.validators.RegexValidator(message='Wrong Format Entered', regex='(?!(\\A( \\x09\\x0A\\x0D\\x20-\\x7E # ASCII | \\xC2-\\xDF # non-overlong 2-byte | \\xE0\\xA0-\\xBF # excluding overlongs | \\xE1-\\xEC\\xEE\\xEF{2} # straight 3-byte | \\xED\\x80-\\x9F # excluding surrogates | \\xF0\\x90-\\xBF{2} # planes 1-3 | \\xF1-\\xF3{3} # planes 4-15 | \\xF4\\x80-\\x8F{2} # plane 16 )*\\Z))')])),
                ('metadata_hash', models.TextField(max_length=200)),
                ('metadata_key', models.TextField(max_length=200)),
                ('metadata_key_hash', models.CharField(max_length=200)),
                ('provider_name', models.CharField(blank=True, max_length=255)),
                ('record_status', models.CharField(blank=True, choices=[('Active', 'A'), ('Inactive', 'I')], max_length=10)),
                ('unique_record_identifier', models.CharField(max_length=250, primary_key=True, serialize=False)),
                ('updated_by', models.CharField(blank=True, default='System', max_length=10)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='created_supplemental_data', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='MetadataLedger',
            fields=[
                ('composite_ledger_transmission_date', models.DateTimeField(blank=True, null=True)),
                ('composite_ledger_transmission_status', models.CharField(blank=True, choices=[('Successful', 'S'), ('Failed', 'F'), ('Pending', 'P'), ('Ready', 'R'), ('Cancelled', 'C')], default='Ready', max_length=10)),
                ('date_deleted', models.DateTimeField(blank=True, null=True)),
                ('date_inserted', models.DateTimeField(blank=True, null=True)),
                ('date_validated', models.DateTimeField(blank=True, null=True)),
                ('metadata', models.JSONField(blank=True, validators=[django.core.validators.RegexValidator(message='Wrong Format Entered', regex='(?!(\\A( \\x09\\x0A\\x0D\\x20-\\x7E # ASCII | \\xC2-\\xDF # non-overlong 2-byte | \\xE0\\xA0-\\xBF # excluding overlongs | \\xE1-\\xEC\\xEE\\xEF{2} # straight 3-byte | \\xED\\x80-\\x9F # excluding surrogates | \\xF0\\x90-\\xBF{2} # planes 1-3 | \\xF1-\\xF3{3} # planes 4-15 | \\xF4\\x80-\\x8F{2} # plane 16 )*\\Z))')])),
                ('metadata_hash', models.CharField(max_length=200)),
                ('metadata_key', models.CharField(max_length=200)),
                ('metadata_key_hash', models.CharField(max_length=200)),
                ('metadata_validation_status', models.CharField(blank=True, choices=[('Y', 'Yes'), ('N', 'No')], max_length=10)),
                ('provider_name', models.CharField(blank=True, max_length=255)),
                ('record_status', models.CharField(blank=True, choices=[('Active', 'A'), ('Inactive', 'I')], max_length=10)),
                ('unique_record_identifier', models.CharField(max_length=250, primary_key=True, serialize=False)),
                ('updated_by', models.CharField(blank=True, default='System', max_length=10)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='created_metadata', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='CCVUpstream',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ccv_api_endpoint', models.CharField(help_text='Enter the CCV Instance API endpoint', max_length=200, null=True)),
                ('ccv_api_endpoint_status', models.CharField(choices=[('ACTIVE', 'Active'), ('INACTIVE', 'Inactive')], max_length=200)),
                ('ccv_api_username', encrypted_model_fields.fields.EncryptedCharField(help_text='Enter the API username', null=True)),
                ('ccv_api_password', encrypted_model_fields.fields.EncryptedCharField(help_text='Enter the API password', null=True)),
                ('ccv_api_key', encrypted_model_fields.fields.EncryptedCharField(help_text='Enter the API key', null=True)),
                ('metadata_experiences', models.ManyToManyField(blank=True, related_name='ccv_source', to='uid.MetadataLedger')),
                ('supplemental_experiences', models.ManyToManyField(blank=True, related_name='ccv_source', to='uid.SupplementalLedger')),
            ],
        ),
        migrations.CreateModel(
            name='CCVDownstream',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ccv_api_endpoint', models.CharField(help_text='Enter the CCV Instance API endpoint', max_length=200)),
                ('ccv_api_endpoint_status', models.CharField(choices=[('ACTIVE', 'Active'), ('INACTIVE', 'Inactive')], max_length=200)),
                ('ccv_api_key', models.CharField(help_text='Enter the CCV API Key', max_length=128)),
                ('source_name', models.CharField(help_text='Enter the name to send data as', max_length=200)),
                ('composite_experiences', models.ManyToManyField(blank=True, related_name='ccv_destination', to='uid.CompositeLedger')),
                ('filter_metadata', models.ManyToManyField(blank=True, related_name='ccv_downstream', to='uid.FilterMetadata')),
                ('filter_records', models.ManyToManyField(blank=True, related_name='ccv_downstream', to='uid.FilterRecord')),
            ],
        ),
    ]
