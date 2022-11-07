from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm, SetPasswordForm
from django.forms import BaseForm, Widget
from django.utils.translation import gettext as _


class Bootstrap5ValidateClass(BaseForm):
    @staticmethod
    def _add_class(widget: Widget, cls):
        class_list = set(widget.attrs.get('class', '').split(' '))
        class_list.add(cls)
        widget.attrs['class'] = ' '.join(class_list)

    def is_valid(self):
        result = super().is_valid()
        for key in self.errors.keys():
            self._add_class(self.fields[key].widget, 'is-invalid')
        return result


class CustomAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': _('Username'),
            'autofocus': True,
        })
        self.fields['username'].label_suffix = ''
        self.fields['password'].widget.attrs.update({
            'class': 'form-control',
            'autocomplete': 'current-password',
            'placeholder': _('Password'),
        })
        self.fields['password'].label_suffix = ''


class CustomPasswordResetForm(Bootstrap5ValidateClass, PasswordResetForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].widget.attrs.update({
            'class': 'form-control',
            'autofocus': True,
            'placeholder': _('Email'),
        })
        self.fields['email'].label_suffix = ''


class CustomSetPasswordForm(Bootstrap5ValidateClass, SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['new_password1'].widget.attrs.update({
            'class': 'form-control',
            'autofocus': True,
            'placeholder': _('New password'),
        })
        self.fields['new_password1'].label_suffix = ''
        self.fields['new_password2'].widget.attrs.update({
            'class': 'form-control',
            'autofocus': True,
            'placeholder': _('New password confirmation'),
        })
        self.fields['new_password2'].label_suffix = ''
