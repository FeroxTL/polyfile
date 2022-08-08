from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.forms import ModelForm, ChoiceField

from storage.data_providers.base import provider_registry
from storage.data_providers.utils import get_data_provider, get_data_provider_class
from storage.models import DataLibrary, DataSource, DataSourceOption, Node, Mimetype


admin.site.register(Mimetype)


class DataSourceAdminForm(ModelForm):
    data_provider_id = ChoiceField(
        choices=[],  # filled later in __init__
        label='Data provider',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['data_provider_id'].choices = [
            (p.provider_id, p.verbose_name)
            for p in provider_registry.providers
        ]
        if self.instance.pk is not None:
            self.fields['data_provider_id'].disabled = True


class CompositionElementFormSet(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()

        if not hasattr(self, 'cleaned_data'):
            # invalid form data
            return

        data_provider_id = self.instance.data_provider_id
        options = {}
        for data in self.cleaned_data:
            if all(map(lambda x: x in data, ['DELETE', 'key', 'value', 'data_source'])):
                # skip deleting fields
                if data['DELETE']:
                    continue

                options[data['key']] = data['value']

        data_provider = get_data_provider_class(data_provider_id)
        try:
            data_provider.validate_options(options=options)
        except ValidationError as e:
            message_list = [
                f'{key}: {error}'
                for key, error_list in e.message_dict.items()
                for error in error_list
            ]
            raise ValidationError(message_list)


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
            library = DataLibrary(data_source=form.instance)
            provider = get_data_provider(library)
            provider.init_provider()


@admin.register(DataLibrary)
class DataLibraryAdmin(admin.ModelAdmin):
    readonly_fields = ['id']
    list_display = ['name', 'owner', 'data_source']
    raw_id_fields = ['owner', 'root_dir']
    list_filter = ['data_source']

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not change:
            provider = get_data_provider(obj)
            provider.init_library()


@admin.register(Node)
class NodeAdmin(admin.ModelAdmin):
    raw_id_fields = ['parent']
    list_display = ['name_str', 'file_type']

    list_filter = [
        ('parent', admin.EmptyFieldListFilter),
    ]

    @admin.display(description='Name')
    def name_str(self, instance):
        return instance.name or '<no name>'
