from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from app.forms import CustomAuthenticationForm


@method_decorator(login_required, name='dispatch')
class IndexView(TemplateView):
    template_name = 'accounts/index.html'


class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    form_class = CustomAuthenticationForm
