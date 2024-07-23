from django.urls import path
from .views import index, new_json,update_json, SendDirectoryListView, Edit_Data, Process_JSON

urlpatterns = [
    path('', index, name = 'index'),
    path('new_json', new_json, name='new_json'),
    path('update_json', update_json, name='update_json'),
    path('idata_list/<path:path>/', SendDirectoryListView.as_view(), name='idata_list'),
    path('idata_form/<int:pk>', Edit_Data.as_view(), name='idata_form'),
    path('process', Process_JSON, name='process'),
    # otras rutas
]
