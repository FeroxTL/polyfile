from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import (
    LoginView, PasswordResetView, PasswordResetConfirmView, PasswordResetDoneView, PasswordResetCompleteView
)
from django.template.response import TemplateResponse
from django.utils.decorators import method_decorator
from django.utils.timezone import now
from django.views.generic import TemplateView
from django.utils.translation import gettext as _

from accounts.models import ResetPasswordAttempt
from app.forms import CustomAuthenticationForm, CustomPasswordResetForm, CustomSetPasswordForm


@method_decorator(login_required, name='dispatch')
class IndexView(TemplateView):
    template_name = 'accounts/index.html'


class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    form_class = CustomAuthenticationForm
    title = _('Log in')
    action_title = _('Log in')

    def get_context_data(self, **kwargs):
        if self.request.user.is_authenticated:
            kwargs['username'] = self.request.user.username
        kwargs['title'] = 'Please sign in'
        return super().get_context_data(**kwargs)


class CustomPasswordResetView(PasswordResetView):
    template_name = 'accounts/password_reset/password_reset_form.html'
    form_class = CustomPasswordResetForm
    action_title = _('Reset my password')

    def form_valid(self, form: CustomPasswordResetForm):
        users = form.get_users(form.cleaned_data['email'])
        for user in users:
            attempt, created = ResetPasswordAttempt.objects.get_or_create(user=user, expire_date__gt=now())
            if not created:
                return TemplateResponse(
                    request=self.request,
                    template='accounts/errors/account_already_emailed.html',
                    status=403,
                    context=self.get_context_data(),
                )
        return super().form_valid(form)


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'accounts/password_reset/password_reset_confirm.html'
    form_class = CustomSetPasswordForm
    action_title = _('Change my password')


class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'accounts/password_reset/password_reset_done.html'


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'accounts/password_reset/password_reset_complete.html'
