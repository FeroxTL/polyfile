from unittest import mock

from django.core.exceptions import ValidationError
from django.core.files.temp import NamedTemporaryFile
from django.core.files.uploadedfile import UploadedFile
from django.test import TestCase
from django.urls import reverse

from accounts.factories import SuperuserFactory
from app.utils.tests import TestProvider, with_tempdir, AdminTestCase
from storage.factories import DirectoryFactory, DataLibraryFactory, FileFactory, DataSourceFactory
from storage.models import Node, DataSource
from storage.utils import get_node_by_path, get_node_queryset


class StorageTests(TestCase):
    @with_tempdir
    def test_get_node_by_path(self, temp_dir):
        """Test getting node by its path."""
        data_library = DataLibraryFactory(data_source__options={'location': temp_dir})
        root_path = '/'
        directory = DirectoryFactory(data_library=data_library)
        directory_path = f'/{directory.name}/'
        file = FileFactory(parent=directory)
        file_path = f'{directory_path}{file.name}'

        # root
        node = get_node_by_path(data_library, root_path)
        self.assertIsNone(node)

        # relative root
        node = get_node_by_path(data_library, '')
        self.assertIsNone(node)

        # directory
        node = get_node_by_path(data_library, directory_path)
        self.assertEqual(node, directory)

        # relative directory
        node = get_node_by_path(data_library, directory_path[1:])
        self.assertEqual(node, directory)

        # file
        node = get_node_by_path(data_library, file_path)
        self.assertEqual(node, file)

        # relative file
        node = get_node_by_path(data_library, file_path[1:])
        self.assertEqual(node, file)

        # does not exist
        with self.assertRaises(Node.DoesNotExist):
            get_node_by_path(data_library, '/does-not-exist/')


class DataSourceAdminTest(AdminTestCase):
    def test_datasource_create(self):
        """Ensure we can create DataSource."""
        url = reverse('admin:storage_datasource_add')
        response = self.client.post(url, {
            'name': 'FooBar',
            'data_provider_id': TestProvider.provider_id,
            **self.get_options({
                'foo': 'bar',
                'bar': 'baz',
                '': '',
            }, delete_list_keys=['bar']),
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(DataSource.objects.count(), 1)
        data_source = DataSource.objects.get()
        self.assertEqual(data_source.name, 'FooBar')
        self.assertEqual(data_source.data_provider_id, TestProvider.provider_id)
        self.assertDictEqual(data_source.options_dict, {'foo': 'bar'})

        url = reverse('admin:storage_datasource_changelist')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_datasource_update(self):
        """Ensure we can update DataSource."""
        datasource = DataSourceFactory()
        url = reverse('admin:storage_datasource_change', args=[datasource.pk])
        response = self.client.post(url, {
            'name': 'FooBar',
            'data_provider_id': TestProvider.provider_id,
            **self.get_options({}),
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(DataSource.objects.count(), 1)
        data_source = DataSource.objects.get()
        self.assertEqual(data_source.name, 'FooBar')

    def test_datasource_options_invalid(self):
        """Errors while creating DataSource."""
        url = reverse('admin:storage_datasource_add')
        data = {
            'name': '',
            'data_provider_id': TestProvider.provider_id,
            **self.get_options({
                'foo': 'bar',
            }),
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        form = response.context['adminform']
        self.assertTrue('name' in form.errors)

        # valid data, invalid options ("foo" value is blank)
        data = {
            'name': 'FooBar',
            'data_provider_id': TestProvider.provider_id,
            **self.get_options({'foo': ''}),
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)

        formset = response.context['inline_admin_formsets'][0]
        self.assertEqual(len(formset.forms), 1)
        form = formset.forms[0]
        self.assertEqual(len(form.errors), 1)
        self.assertTrue('value' in form.errors)

        # invalid value in options
        data = {
            'name': 'FooBar',
            'data_provider_id': TestProvider.provider_id,
            **self.get_options({'foo': 'bar'}),
        }
        with mock.patch.object(TestProvider, 'validate_options') as p:
            p.side_effect = ValidationError({'foo': 'foo is invalid'})
            response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)

        form = response.context['adminform']
        self.assertEqual(len(form.errors), 0)
        self.assertEqual(len(response.context['inline_admin_formsets']), 1)
        formset = response.context['inline_admin_formsets'][0]
        self.assertEqual(len(formset.forms), 1)
        self.assertListEqual(formset.non_form_errors(), ['foo: foo is invalid'])


class DataLibraryAdminTest(TestCase):
    def setUp(self) -> None:
        self.user = SuperuserFactory()
        self.client.force_login(self.user)

    @with_tempdir
    def test_init_library(self, temp_dir):
        """Ensure we can create DataLibrary and init them."""
        url = reverse('admin:storage_datalibrary_add')

        with mock.patch.object(TestProvider, 'init_library') as init_library:
            data_source = DataSourceFactory(options={'location': temp_dir})
            data = {
                'name': 'Test',
                'owner': self.user.pk,
                'data_source': data_source.pk,
            }
            response = self.client.post(url, data)
            self.assertEqual(response.status_code, 302)
            init_library.assert_called()

        url = reverse('admin:storage_datalibrary_changelist')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_change_library(self):
        """Ensure DataLibrary is not reinitialized on update."""
        data_library = DataLibraryFactory(owner=self.user)
        url = reverse('admin:storage_datalibrary_change', args=[str(data_library.pk)])

        with mock.patch.object(TestProvider, 'init_library') as init_library:
            data = {
                'name': 'Test',
                'owner': data_library.owner.pk,
                'data_source': data_library.data_source.pk,
                'data_library': data_library.pk,
            }
            response = self.client.post(url, data)
            self.assertEqual(response.status_code, 302)
            init_library.assert_not_called()


class NodeAdminTest(AdminTestCase):
    @with_tempdir
    def test_list_node(self, temp_dir):
        """Ensure we can list Nodes."""
        url = reverse('admin:storage_node_changelist')
        data_library = DataLibraryFactory(data_source__options={'location': temp_dir})
        directory = DirectoryFactory(data_library=data_library)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(directory.name.encode('utf-8') in response.content)

    @with_tempdir
    def test_change_widget(self, temp_dir):
        """Ensure url in admin widget is correct."""
        data_library = DataLibraryFactory(data_source__options={'location': temp_dir}, owner=self.user)
        with NamedTemporaryFile() as tmp_file:
            file_node = FileFactory(data_library=data_library, file=UploadedFile(tmp_file))
        url = reverse('admin:storage_node_change', args=[file_node.pk])
        response = self.client.get(url)
        file_node = get_node_queryset().get(pk=file_node.pk)
        self.assertTrue(file_node.file.url().encode('utf-8') in response.content)

        file_response = self.client.get(file_node.file.url())
        self.assertEqual(file_response.status_code, 200)

    @with_tempdir
    def test_node_create(self, temp_dir):
        """Ensure we can create node."""
        url = reverse('admin:storage_node_add')
        data_library = DataLibraryFactory(data_source__options={'location': temp_dir})
        directory = DirectoryFactory(data_library=data_library)

        # invalid data
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            set(response.context['adminform'].errors.keys()),
            {'name', 'size', 'data_library', 'file_type', 'parent'}
        )

        # valid data
        response = self.client.post(url, data={
            'name': 'foo',
            'size': 0,
            'data_library': data_library.pk,
            'file_type': Node.FileTypeChoices.DIRECTORY,
            'parent': directory.pk,
        })
        self.assertEqual(response.status_code, 302)
        qs = Node.objects.filter(name='foo')
        self.assertTrue(qs.exists())
        node = qs.get()
        self.assertEqual(node.parent, directory)
        self.assertEqual(node.data_library, data_library)