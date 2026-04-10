from django.urls import path
from .views import (
    EndpointListCreateView,
    DynamicCRUDView,
    reset_endpoint_data,
    trash_endpoint,
    get_trashed_endpoints,
    recover_endpoint,
    delete_endpoint,
    trash_all_endpoints,
    social_register,
    get_users,
    UserProfile,
    UploadImageView
)

dynamic_list = DynamicCRUDView.as_view({
    'get': 'list',
    'post': 'create',
})

dynamic_detail = DynamicCRUDView.as_view({
    'get': 'retrieve',
    'put': 'update',
    'patch': 'partial_update',
    'delete': 'destroy',
})
urlpatterns = [
    path('auth/social-register/', social_register, name='social_register'),
    path('auth/user/', UserProfile.as_view(), name='get_user'),
    path('auth/users/', get_users, name='get_users'),
    path('create/', EndpointListCreateView.as_view(), name='create-endpoint'),
    path('create/<int:id>/reset/', reset_endpoint_data, name='reset-endpoint'),
    path('create/<int:id>/trash/', trash_endpoint, name='trash-endpoint'),
    path('create/trashed/', get_trashed_endpoints, name='trashed-endpoints'),
    path('create/<int:id>/recover/', recover_endpoint, name='recover-endpoint'),
    path('create/<int:id>/delete/', delete_endpoint, name='delete-endpoint'),
    path('create/trash-all/', trash_all_endpoints, name='trash-all-endpoints'),

    path('v1/<str:token>/<str:resource>/', dynamic_list, name='dynamic-list'),
    path('v1/<str:token>/<str:resource>/<int:id>/', dynamic_detail, name='dynamic-detail'),

    path('file/', UploadImageView.as_view({'post': 'upload_single'}), name='upload-single'),
    path('files/', UploadImageView.as_view({'post': 'upload_multiple'}), name='upload-multiple'),
]