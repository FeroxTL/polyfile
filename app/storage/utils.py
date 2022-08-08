# todo: write :exception in class/method descriptions
import typing
from functools import partial

from django.db import transaction
from django.db.models import F, Value, TextField
from django.db.models.functions import Concat
from django_cte import With

from storage.data_providers.exceptions import ProviderException
from storage.data_providers.utils import get_data_provider
from storage.models import Node, DataLibrary


def adapt_path(path: str) -> str:
    """
    Adapts path to CTE queryset appropriate.

    "" -> ""
    "/" -> ""
    "/foo/" -> "/foo"
    "foo/" -> "/foo"
    "/foo/bar.jpg" -> "/foo/bar.jpg"

    :param path: input path
    :return: filtered path with slashes only between elements
    """
    path_list = filter(None, path.split('/'))

    return '/'.join(['', *path_list])


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


def get_node_by_path(root_node_id: int, path: str, last_node_type: typing.Optional[str] = None) -> Node:
    """
    Get node by path in root directory.

    Raises:
         Node.DoesNotExist if node is not found.
    """
    cte = With.recursive(partial(_make_node_cte, pk=root_node_id))
    path = adapt_path(path)
    node_cte_qs = (
        cte.join(Node.cte_objects.all(), pk=cte.col.pk)
        .with_cte(cte)
        .annotate(
            path=cte.col.path,
        )
        .filter(path=path)
        .order_by('path')
    )

    node = node_cte_qs.get()

    if last_node_type is not None and last_node_type != node.file_type:
        raise Node.DoesNotExist('Incorrect node type')

    return node


def remove_node(library: DataLibrary, path: str):
    """
    Removes Node by its path.

    :param library: DataLibrary, that contains Node
    :param path: path in library
    :return:
    :exception Node.DoesNotExist -- can not get Node by path
    :exception ProviderException -- can not remove Node
    """
    data_provider = get_data_provider(library=library)
    current_node = get_node_by_path(root_node_id=library.root_dir_id, path=path)

    if current_node == library.root_dir:
        raise ProviderException('Can not remove root directory')

    if current_node.is_directory and current_node.get_children_count():
        raise ProviderException(
            f'Can not remove "{current_node.name}": is not empty'
        )

    with transaction.atomic():
        current_node.delete()
        data_provider.rm(path=path)
