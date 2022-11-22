from django.forms import forms, fields


class S3ValidationForm(forms.Form):
    """S3 options validation form."""
    endpoint_url = fields.URLField(
        label='Endpoint',
        required=True,
        help_text="Address to server with port. Example: http://localhost:9000",
    )
    access_key = fields.CharField(
        label='Access key',
        required=True,
    )
    secret_key = fields.CharField(
        label='Secret key',
        required=True,
    )
