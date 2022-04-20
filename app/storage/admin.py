from django import forms
from django.contrib import admin
from django.forms import ModelForm, ChoiceField
from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory

from storage.data_providers.base import provider_register
from storage.data_providers.utils import get_data_provider
from storage.models import DataLibrary, DataSource, DataSourceOption, Node


class DataSourceAdminForm(ModelForm):
    data_provider_id = ChoiceField(
        choices=[],  # filled later in __init__
        label='Data provider',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['data_provider_id'].choices = [
            (p.provider_id, p.verbose_name)
            for p in provider_register.providers
        ]
        if self.instance.pk is not None:
            self.fields['data_provider_id'].disabled = True


class CompositionElementFormSet(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()

        if not hasattr(self, 'cleaned_data'):
            # invalid form data
            return

        options = {}
        for data in self.cleaned_data:
            if all(map(lambda x: x in data, ['DELETE', 'key', 'value'])):
                if data['DELETE']:
                    continue

                options[data['key']] = data['value']

        # todo validate options by its data provider
        print(options)


class DataSourceOptionAdmin(admin.TabularInline):
    model = DataSourceOption
    formset = CompositionElementFormSet
    extra = 1


@admin.register(DataSource)
class DataSourceAdmin(admin.ModelAdmin):
    readonly_fields = ['id']
    list_display = ['name', 'data_provider_id']
    form = DataSourceAdminForm
    inlines = [DataSourceOptionAdmin]

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        if not change:
            provider = get_data_provider(form.instance)
            provider.init_provider()


@admin.register(DataLibrary)
class LibraryAdmin(admin.ModelAdmin):
    readonly_fields = ['id']
    list_display = ['name', 'owner', 'data_source']
    raw_id_fields = ['owner']
    list_filter = ['data_source']

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not change:
            provider = get_data_provider(obj.data_source)
            provider.init_library(library=obj)


@admin.register(Node)
class NodeAdmin(TreeAdmin):
    form = movenodeform_factory(Node)
