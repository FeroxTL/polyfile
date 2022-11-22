from functools import partial

from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.forms import ChoiceField
from django_cte import With

from storage.base_data_provider import provider_registry
from storage.models import DataLibrary, DataSource, Node, Mimetype, AltNode
from storage.utils import get_node_queryset, make_node_cte

admin.site.register(Mimetype)


class MySONField(forms.JSONField):
    def bound_data(self, data, initial):
        if data in self.empty_values and self.required:
            return self.empty_value
        return super().bound_data(data=data, initial=initial)


class DataSourceAdminForm(forms.ModelForm):
    data_provider_id = ChoiceField(
        choices=[],  # filled later in __init__
        label='Data provider',
    )
    options = MySONField(
        required=True,
    )

    class Meta:
        model = DataSource
        fields = forms.ALL_FIELDS

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['data_provider_id'].choices = [
            (p.provider_id, p.verbose_name)
            for p in provider_registry.providers
        ]
        if self.instance.pk is not None:
            self.fields['data_provider_id'].disabled = True

    def clean(self):
        data_provider_id = self.cleaned_data.get('data_provider_id')
        options = self.cleaned_data.get('options', {})
        if not data_provider_id:
            return super().clean()

        data_provider = provider_registry.get_provider(data_provider_id)
        try:
            data_provider.transform_options(options=options)
        except ValidationError as e:
            message_list = [
                f'{key}: {error}'
                for key, error_list in e.message_dict.items()
                for error in error_list
            ]
            raise ValidationError({'options': message_list})

        return super().clean()


@admin.register(DataSource)
class DataSourceAdmin(admin.ModelAdmin):
    readonly_fields = ['id']
    list_display = ['name', 'data_provider_id']
    form = DataSourceAdminForm


@admin.register(DataLibrary)
class DataLibraryAdmin(admin.ModelAdmin):
    readonly_fields = ['id']
    list_display = ['name', 'owner', 'data_source']
    raw_id_fields = ['owner']
    list_filter = ['data_source']

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not change:
            provider = obj.data_source.get_provider()
            provider.init_library(library=obj)


class NodeAdminForm(forms.ModelForm):
    class Meta:
        model = Node
        fields = forms.ALL_FIELDS

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['parent'].required = False


@admin.register(Node)
class NodeAdmin(admin.ModelAdmin):
    raw_id_fields = ['parent']
    list_display = ['name', 'file_type']
    form = NodeAdminForm

    list_filter = [
        ('parent', admin.EmptyFieldListFilter),
    ]

    def get_queryset(self, request):
        return get_node_queryset().select_related('data_library')

    def delete_queryset(self, request, queryset):
        for instance in queryset:
            instance.file.delete()
        super().delete_queryset(request, queryset)


@admin.register(AltNode)
class AltNodeAdmin(admin.ModelAdmin):
    raw_id_fields = ['node', 'data_library', 'mimetype']
    list_display = ['node_id', 'version', 'data_library', 'file']

    @staticmethod
    def get_node_path(node: Node):
        cte = With.recursive(partial(
            make_node_cte,
            base_queryset=Node.cte_objects.filter(data_library_id=node.data_library_id)
        ))
        return get_node_queryset(cte=cte).get(pk=node.pk).path

    def get_object(self, request, object_id, from_field=None):
        instance = super().get_object(request, object_id, from_field)
        instance.path = self.get_node_path(instance.node)
        return instance

    def delete_queryset(self, request, queryset):
        for instance in queryset:
            instance.file.delete()
        super().delete_queryset(request, queryset)
