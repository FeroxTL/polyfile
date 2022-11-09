import tempfile
from pathlib import Path

from django.test import TestCase
from django.core.files.uploadedfile import UploadedFile
from django.urls import reverse
from rest_framework import status

from accounts.factories import UserFactory
from app.utils.tests import with_tempdir, AdminTestCase
from contrib.storages.filesystem_storage.provider import FileSystemStorageProvider
from storage.factories import DataLibraryFactory, FileFactory


class FileSystemStorageAdminTests(AdminTestCase):
    """File storage admin tests"""
    @with_tempdir
    def test_create_storage(self, temp_dir):
        url = reverse('admin:storage_datasource_add')

        # invalid data
        response = self.client.post(url)
        form = response.context['adminform']
        self.assertTrue('name' in form.errors)
        self.assertTrue('data_provider_id' in form.errors)
        formset = response.context['inline_admin_formsets'][0]
        self.assertEqual(len(formset.forms), 0)

        # invalid options
        response = self.client.post(url, {
            'name': 'FooBar',
            'data_provider_id': FileSystemStorageProvider.provider_id,
            **self.get_options({
                'foo': 'bar',
            }),
        })

        form = response.context['adminform']
        self.assertEqual(form.errors, {})
        formset = response.context['inline_admin_formsets'][0]
        self.assertEqual(len(formset.forms), 1)
        self.assertListEqual(formset.non_form_errors(), ['root_directory: This field is required.'])

        # valid options
        response = self.client.post(url, {
            'name': 'FooBar',
            'data_provider_id': FileSystemStorageProvider.provider_id,
            **self.get_options({
                'root_directory': temp_dir,
            }),
        })
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response.headers['Location'], reverse('admin:storage_datasource_changelist'))

        # invalid directory
        dne_path = Path(temp_dir) / 'does-not-exists'
        response = self.client.post(url, {
            'name': 'FooBar',
            'data_provider_id': FileSystemStorageProvider.provider_id,
            **self.get_options({
                'root_directory': dne_path,
            }),
        })

        form = response.context['adminform']
        self.assertEqual(form.errors, {})
        formset = response.context['inline_admin_formsets'][0]
        self.assertEqual(len(formset.forms), 1)
        self.assertListEqual(formset.non_form_errors(), [
            f'root_directory: "{dne_path}" is not directory or does not exist'
        ])


class FileSystemStorageProviderTests(TestCase):
    """FileStorage tests."""
    def setUp(self) -> None:
        self.user = UserFactory()
        self.client.force_login(self.user, backend='django.contrib.auth.backends.ModelBackend')

    @with_tempdir
    def test_node_lifecycle(self, temp_dir):
        """Ensure we can manage files to storage."""
        data_library = DataLibraryFactory(
            owner=self.user,
            data_source__data_provider_id=FileSystemStorageProvider.provider_id,
            data_source__options={'root_directory': temp_dir}
        )

        with tempfile.NamedTemporaryFile(suffix='.jpg') as temp_file:
            temp_file.write(b'foobar')

            file_node = FileFactory(
                data_library=data_library,
                file=UploadedFile(temp_file),
            )

        file = Path(file_node.file.file.file.name)
        self.assertTrue(file.exists())
        self.assertEqual(file.read_bytes(), b'foobar')
        self.assertTrue(file.is_relative_to(Path(temp_dir)))

        # delete
        file_node.file.delete()
        self.assertFalse(file.exists())
