from django.forms import forms, fields

from app.utils.models import get_field
from storage.models import DataSourceOption


class S3ValidationForm(forms.Form):
    endpoint_url = fields.URLField(
        label='Endpoint',
        required=True,
        max_length=get_field(DataSourceOption, 'value').max_length,
        help_text="Address to server with port. Example: http://localhost:9000",
    )
    access_key = fields.CharField(
        label='Access key',
        required=True,
        max_length=get_field(DataSourceOption, 'value').max_length
    )
    secret_key = fields.CharField(
        label='Secret key',
        required=True,
        max_length=get_field(DataSourceOption, 'value').max_length
    )
