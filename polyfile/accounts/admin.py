from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from accounts.models import User, ResetPasswordAttempt

admin.site.register(User, UserAdmin)


@admin.register(ResetPasswordAttempt)
class ResetPasswordAttemptAdmin(admin.ModelAdmin):
    list_display = ['user', 'attempt_date', 'expire_date']
