from django import forms
from django.contrib.auth.forms import AuthenticationForm, UsernameField
from django.utils.translation import gettext as _


class CustomAuthenticationForm(AuthenticationForm):
    username = UsernameField(
        widget=forms.TextInput(attrs={'autofocus': True, 'class': 'form-control', 'placeholder': 'username'}),
        label_suffix=''
    )
    password = forms.CharField(
        label=_('Password'),
        strip=False,
        label_suffix='',
        widget=forms.PasswordInput(attrs={
            'autocomplete': 'current-password',
            'class': 'form-control',
            'placeholder': _('Password')
        }),
    )
