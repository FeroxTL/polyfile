# todo: write :exception in class/method descriptions
from django.db import transaction

from storage.data_providers.exceptions import ProviderException
from storage.data_providers.utils import get_data_provider
from storage.models import Node, DataLibrary


# def get_parent_path(path: str):
#     path_list = path.rsplit('/', 2)
#     if len(path_list) >= 2:
#         last_is_directory = path_list[-1] == ''
#         # path[-2]!='' means path_list=['', '']
#         if last_is_directory and path_list[-2] != '':
#             path_list.pop(-2)
#         else:
#             path_list[-1] = ''
#     elif len(path_list) == 1:
#         path_list.append('')
#     return '/'.join(path_list)


def get_node_by_path(root_node: Node, path: str) -> Node:
    """
    Get node by path in root directory.

    Raises:
         Node.DoesNotExist if node is not found.
    """
    path_list = path.split('/')

    if path_list[0] == '':
        path_list.pop(0)

    if not path_list:
        return root_node

    list_last_directory = path_list[-1] == ''

    if list_last_directory:
        path_list.pop(-1)

    current_node = root_node

    for i, path_item in enumerate(path_list):
        if i == len(path_list) - 1 and not list_last_directory:
            extra_params = {'file_type': Node.FileTypeChoices.FILE}
        else:
            extra_params = {'file_type': Node.FileTypeChoices.DIRECTORY}
        current_node = current_node.get_children().get(name=path_item, **extra_params)

    return current_node


def remove_node(library: DataLibrary, path: str):
    """
    Removes Node by its path.

    :param library: DataLibrary, that contains Node
    :param path: path in library
    :return:
    :exception Node.DoesNotExist -- can not get Node by path
    :exception ProviderException -- can not remove Node
    """
    data_provider = get_data_provider(data_source=library.data_source)
    current_node = get_node_by_path(root_node=library.root_dir, path=path)

    if current_node == library.root_dir:
        raise ProviderException('Can not remove root directory')

    if current_node.is_directory and current_node.get_children_count():
        raise ProviderException(
            f'Can not remove "{current_node.name}": is not empty'
        )

    with transaction.atomic():
        current_node.delete()
        data_provider.rm(library=library, path=path)
