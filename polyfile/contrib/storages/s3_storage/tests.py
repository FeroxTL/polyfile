import datetime
import tempfile
from unittest import mock

from PIL import Image
from django.core.files.uploadedfile import UploadedFile
from django.test import TestCase

from accounts.factories import UserFactory
from contrib.storages.s3_storage.provider import S3StorageProvider
from storage.factories import DataLibraryFactory, FileFactory, ImageFactory, AltNodeFactory


class FileSystemStorageProviderTests(TestCase):
    """FileStorage tests."""
    def setUp(self) -> None:
        self.user = UserFactory()
        self.client.force_login(self.user)

    def test_node_lifecycle(self):
        """Ensure we can manage files to storage."""
        options = {
            'endpoint_url': 'localhost',
            'access_key': 'foo',
            'secret_key': 'bar',
        }
        data_library = DataLibraryFactory(
            owner=self.user,
            data_source__data_provider_id=S3StorageProvider.provider_id,
            data_source__options=options
        )

        # init library
        with mock.patch('botocore.client.BaseClient._make_api_call') as request:
            S3StorageProvider(options=options).init_library(data_library)
            self.assertEqual(request.call_count, 2)
            request.assert_any_call('ListBuckets', {})
            request.assert_any_call('CreateBucket', {'Bucket': str(data_library.pk)})

        # reinit library
        with mock.patch('botocore.client.BaseClient._make_api_call') as request:
            def side_effect(action, *args, **kwargs):  # noqa
                if action == 'ListBuckets':
                    return {'Buckets': [{'Name': str(data_library.pk), 'CreationDate': datetime.datetime.now()}]}
            request.side_effect = side_effect

            S3StorageProvider(options=options).init_library(data_library)
            self.assertEqual(request.call_count, 1, request.call_args_list)
            request.assert_any_call('ListBuckets', {})

        # upload file
        with tempfile.NamedTemporaryFile(suffix='.jpg') as temp_file:
            temp_file.write(b'foobar')

            with mock.patch('botocore.client.BaseClient._make_api_call') as request:
                FileFactory(
                    data_library=data_library,
                    file=UploadedFile(temp_file),
                )
                request.assert_called_once()

        # thumbnail
        with tempfile.NamedTemporaryFile(suffix='.jpg') as temp_file:
            with mock.patch('botocore.client.BaseClient._make_api_call') as request:
                image = Image.new("RGB", size=(50, 50), color=(255, 0, 0))
                image.save(temp_file)
                temp_file.seek(0)
                file_node = ImageFactory(
                    data_library=data_library,
                    file=UploadedFile(temp_file),
                    mimetype__name='image/jpeg',
                )
        request.assert_called_once()

        with tempfile.NamedTemporaryFile(suffix='.jpg') as temp_file:
            with mock.patch('botocore.client.BaseClient._make_api_call') as request:
                image = Image.new("RGB", size=(50, 50), color=(255, 0, 0))
                image.save(temp_file)
                temp_file.seek(0)
                AltNodeFactory(node=file_node, data_library=data_library, file=UploadedFile(temp_file))
        request.assert_called_once()
