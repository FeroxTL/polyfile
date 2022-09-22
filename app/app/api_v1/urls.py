from django.urls import path, include

from app.api_v1.data_libraries import views as dl_views
from app.api_v1.data_sources import views as ds_views
from app.api_v1.data_providers import views as dp_views
from app.api_v1.system import views as sys_views
from app.api_auth import urls as api_urls

urlpatterns = [
    path('', sys_views.ApiIndex.as_view(), name='index'),
    path('auth/', include(api_urls)),
    path('sys/current_user', sys_views.CurrentUserView.as_view(), name='sys-cuser'),
    path('dp', dp_views.DataProviderList.as_view(), name='dp-list'),
    path('ds', ds_views.DataSourceListCreateView.as_view(), name='ds-list'),
    path('ds/<int:pk>', ds_views.DataSourceDetailView.as_view(), name='ds-detail'),
    path('lib', dl_views.DataLibraryListCreateView.as_view(), name='lib-list'),
    path('lib/<uuid:lib_id>', dl_views.DataLibraryDetailUpdateView.as_view(), name='lib-detail'),
    path('lib/<uuid:lib_id>/files<path:path>', dl_views.DataLibraryNodeListView.as_view(), name='lib-files'),
    path('lib/<uuid:lib_id>/move<path:path>', dl_views.DataLibraryNodeMoveView.as_view(), name='lib-move'),
    path('lib/<uuid:lib_id>/rename<path:path>', dl_views.DataLibraryNodeRenameView.as_view(), name='lib-rename'),
    path('lib/<uuid:lib_id>/upload<path:path>', dl_views.NodeUploadFileView.as_view(), name='lib-upload'),
    path('lib/<uuid:lib_id>/mkdir<path:path>', dl_views.DataLibraryMkdirView.as_view(), name='lib-mkdir'),
    path('lib/<uuid:lib_id>/rm<path:path>', dl_views.DataLibraryDeleteNodeView.as_view(), name='lib-rm'),
    path('lib/<uuid:lib_id>/download<path:path>', dl_views.DataLibraryDownloadView.as_view(), name='lib-download'),
]
