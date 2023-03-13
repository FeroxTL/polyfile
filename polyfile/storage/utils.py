# todo: write :exception in class/method descriptions
import typing
from functools import partial

from django.db.models import F, Value, TextField
from django.db.models.functions import Concat
from django_cte import With
from polyfile.storage.models import Node, DataLibrary, Mimetype


def get_mimetype(mtype: str, default='application/octet-stream') -> Mimetype:
    """Get or create mimetype."""
    mimetype, _ = Mimetype.objects.get_or_create(name=mtype or default)
    return mimetype


def adapt_path(path: str) -> str:
    """
    Adapts path to CTE queryset appropriate.

    "" -> ""
    "/" -> ""
    "/foo/" -> "foo"
    "foo/" -> "foo"
    "foo/bar" -> "foo/bar"
    "/foo/bar" -> "foo/bar"
    "/foo/bar/" -> "foo/bar"
    "/foo/bar.jpg" -> "foo/bar.jpg"

    :param path: input path
    :return: filtered path with slashes only between elements
    """
    path_list = filter(None, path.split('/'))

    return '/'.join(path_list)


def make_node_cte(cte, base_queryset):
    """Queryset for instance of recursive CTE."""
    # non-recursive: get root nodes
    return base_queryset.filter(
        parent__isnull=True,
    ).values(
        'pk',
        'name',
        path=F('name'),
    ).union(
        # recursive union: get descendants
        cte.join(Node, parent=cte.col.pk).values(
            'pk',
            'name',
            path=Concat(
                cte.col.path, Value('/'), F('name'),
                output_field=TextField(),
            ),
        ),
        all=True,
    )


def get_node_queryset(cte=None, order_by='path'):
    """Node queryset with CTE."""
    cte = cte or With.recursive(partial(make_node_cte, base_queryset=Node.cte_objects))

    node_cte_qs = (
        cte.join(Node.cte_objects.all(), pk=cte.col.pk)
        .with_cte(cte)
        .annotate(path=cte.col.path)
        .order_by(order_by)
    )

    return node_cte_qs


def get_node_by_path(
        # todo: replace to library id? some kwargs?
        library: DataLibrary,
        path: str,
        last_node_type: typing.Optional[str] = None,
        strict: bool = False,
) -> typing.Optional[Node]:
    """
    Get node by path in root directory.

    :param library: DataLibrary of node
    :param path: path relative to root directory ("/foo/bar.jpg")
    :param last_node_type: optional, asserts last node (bar.jpg) has specified file_type
    :param strict: raise exception or return None if path is empty
    :return: Node in requested path, None if path is root directory

    Exceptions:
         Node.DoesNotExist if node is not found.
    """
    cte = With.recursive(partial(make_node_cte, base_queryset=Node.cte_objects.filter(data_library=library)))

    path = adapt_path(path)

    if not path:
        if strict:
            raise Node.DoesNotExist('Node matching query does not exist.')
        return None

    node_cte_qs = get_node_queryset(cte=cte).filter(path=path)
    node = node_cte_qs.get()
    node.data_library = library

    if last_node_type is not None and last_node_type != node.file_type:
        raise Node.DoesNotExist('Incorrect node type')

    return node
