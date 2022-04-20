from django.urls import path, include
from app.api_auth import urls as api_urls

from . import views

urlpatterns = [
    path('', views.ApiItemList.as_view(), name='index'),
    path('auth/', include(api_urls)),
    path('libraries', views.DataLibraryListCreateView.as_view(), name='lib-list'),
    path('libraries/<uuid:lib_id>', views.DataLibraryDetailUpdateView.as_view(), name='lib-detail'),
    path('libraries/<uuid:lib_id>/files<path:path>', views.DataLibraryNodeListView.as_view(), name='lib-files'),
    path('libraries/<uuid:lib_id>/move<path:path>', views.DataLibraryNodeMoveView.as_view(), name='lib-move'),
    path('libraries/<uuid:lib_id>/rename<path:path>', views.DataLibraryNodeRenameView.as_view(), name='lib-rename'),
    path('libraries/<uuid:lib_id>/upload<path:path>', views.NodeUploadFileView.as_view(), name='lib-upload'),
    path('libraries/<uuid:lib_id>/mkdir<path:path>', views.DataLibraryMkdirView.as_view(), name='lib-mkdir'),
    path('libraries/<uuid:lib_id>/rm<path:path>', views.DataLibraryRmFileView.as_view(), name='lib-rm'),
    path('libraries/<uuid:lib_id>/download<path:path>', views.DataLibraryDownloadView.as_view(), name='lib-download'),
]
