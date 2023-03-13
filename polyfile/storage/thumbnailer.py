import typing
from collections import namedtuple
from io import BytesIO

from PIL import Image, ImageOps, UnidentifiedImageError

from polyfile.storage.models import Node
from polyfile.storage.utils import get_mimetype


class ThumbnailException(Exception):
    """Basic exception for thumbnail generation."""
    pass


ThumbnailResult = namedtuple('ThumbnailResult', ['file', 'mimetype'])


class Thumbnailer:
    """Thumbnail generator."""
    def __init__(self):
        self._default_formats = []
        self.default_formats = ['JPEG', 'PNG']
        self.available_mimetypes = set()

    @property
    def default_formats(self) -> list:
        """List of formats to use for thumbnail generation."""
        return self._default_formats

    @default_formats.setter
    def default_formats(self, value: typing.Iterable[str]):
        self._default_formats = list(map(lambda x: x.upper(), value))

    def setup(self):
        """Set up thumbnailer instance."""
        extensions = Image.registered_extensions()
        for extension in extensions.values():
            if extension in Image.MIME:
                mimetype = get_mimetype(Image.MIME[extension])
                self.available_mimetypes.add(mimetype.name)

        for image_format in self.default_formats.copy():
            if image_format not in Image.MIME:
                self.default_formats.remove(image_format)

    def can_get_thumbnail(self, mimetype: str):
        """Check thumbnail is available from mimetype."""
        return mimetype in self.available_mimetypes

    def get_thumbnail(self, node: Node, thumb_size: typing.Tuple[int, int]) -> ThumbnailResult:
        """Get thumbnail from Node."""
        if not self.can_get_thumbnail(node.mimetype_id) or not self.default_formats:
            raise ThumbnailException('Can not create thumbnail')

        file_io = BytesIO()
        try:
            node_image = Image.open(node.file)
        except UnidentifiedImageError:
            raise ThumbnailException('Can not open thumbnail')

        if node_image.format and node_image.format.upper() in self.default_formats:
            thumbnail_format = node_image.format.upper()
        else:
            thumbnail_format = self.default_formats[0]

        image = ImageOps.fit(image=node_image, size=thumb_size, method=Image.ANTIALIAS)
        image.save(file_io, format=thumbnail_format)
        mimetype = Image.MIME.get(thumbnail_format)
        return ThumbnailResult(file_io, mimetype)


thumbnailer = Thumbnailer()
