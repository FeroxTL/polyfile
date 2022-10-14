# todo: write :exception in class/method descriptions
import typing
from functools import partial

from django.db.models import F, Value, TextField
from django.db.models.functions import Concat
from django_cte import With

from storage.models import Node, DataLibrary


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


def _make_node_cte(cte, **params):
    # non-recursive: get root nodes
    return Node.cte_objects.filter(
        parent__isnull=True,
        **params,
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


def get_node_queryset(cte=None):
    cte = cte or With.recursive(_make_node_cte)

    node_cte_qs = (
        cte.join(Node.cte_objects.all(), pk=cte.col.pk)
        .with_cte(cte)
        .annotate(
            path=cte.col.path,
        )
        .order_by('path')
    )

    return node_cte_qs


def get_node_by_path(
        # todo: replace to library id? some kwargs?
        library: DataLibrary,
        path: str,
        last_node_type: typing.Optional[str] = None
) -> typing.Optional[Node]:
    # todo:
    #  typing.Optional[Node] -- maybe we should remove this option and always return Node
    """
    Get node by path in root directory.

    :param library: DataLibrary of node
    :param path: path relative to root directory ("/foo/bar.jpg")
    :param last_node_type: optional, asserts last node (bar.jpg) has specified file_type
    :return: Node in requested path, None if path is root directory

    Raises:
         Node.DoesNotExist if node is not found.
    """
    cte = With.recursive(partial(_make_node_cte, data_library=library))

    # todo: remove adapt_path by modifying urls.py?
    path = adapt_path(path)

    if not path:
        return None

    node_cte_qs = get_node_queryset(cte=cte).filter(path=path)
    node = node_cte_qs.get()

    if last_node_type is not None and last_node_type != node.file_type:
        raise Node.DoesNotExist('Incorrect node type')

    return node
