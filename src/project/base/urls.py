from django.urls import path
from .views import index, new_json,update_json, SendDirectoryListView, Edit_Data, Process_JSON, Login, SignUp
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('', index, name = 'index'),
    path('login', Login.as_view(), name = 'login'),
    path('logout', LogoutView.as_view(next_page = 'login'), name = 'logout'),
    path('signup', SignUp.as_view(), name = 'signup'),
    path('new_json', new_json, name='new_json'),
    path('update_json', update_json, name='update_json'),
    path('idata_list/<path:path>/', SendDirectoryListView.as_view(), name='idata_list'),
    path('idata_form/<int:pk>', Edit_Data.as_view(), name='idata_form'),
    path('process', Process_JSON, name='process'),
    # otras rutas
]
