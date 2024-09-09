from django.urls import path
from .views import index, new_json, SendDirectoryListView, Edit_Data, Process_JSON
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('', index, name = 'index'),
    path('new_json', new_json, name='new_json'),
    path('idata_list/<path:path>/', SendDirectoryListView.as_view(), name='idata_list'),
    path('idata_form/<int:pk>', Edit_Data.as_view(), name='idata_form'),
    path('process', Process_JSON, name='process'),
    # otras rutas
]
