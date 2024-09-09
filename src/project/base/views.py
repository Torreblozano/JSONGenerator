# views.py
import json
import os
from pathlib import Path

# Django libraries
from django.shortcuts import render
from django.views.generic.edit import UpdateView, FormView
from django.views.generic.list import ListView
from django.urls import reverse, reverse_lazy
from django.http import HttpResponse
from django.shortcuts import redirect
from django.db import connection
# Own libraries
from .json_processor import build_directory_tree, process_json_data, find_root_file, create_idata_instances,make_comparison
from .models import Idata, SavedJSONS
from .forms import UploadedFile

#Views
def index(request):
    return render(request, 'base/index.html')

class SendDirectoryListView(ListView):
    model = Idata
    context_object_name = 'directory_structure'
    template_name = 'base/idata_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def get_object(self, queryset=None):
        return Idata.objects.first()

    class EmptyData:
        def __init__(self, path_root):
            self.AssetName = "None"
            self.AssetDescription = "None"
            self.updated_at = None
            self.level = 500
            self.path = path_root
            self.pathRoot = path_root
            self.isDirectory = True
            self.needUpdate = False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        path = self.kwargs.get('path')
        path_obj = Path(path)

        if path:
            directory_structure = Idata.objects.filter(pathRoot=path)

            if directory_structure:
                context['directory_structure'] = directory_structure
                first_item = directory_structure[0]
                path_root = Path(first_item.pathRoot)

                if first_item.level > 0:
                    context['parent_root'] = str(path_root.parent)
                else:
                    context['parent_root'] = None
            else:
                context['directory_structure'] = None
                context['parent_root'] = path_obj.parent
        else:
            context['directory_structure'] = None
            context['parent_root'] = None
        return context

class Edit_Data(UpdateView):
    model = Idata
    fields = ['AssetDescription']

    def get_success_url(self):
        print(self.object.pathRoot)
        path_root = self.object.pathRoot
        return reverse('idata_list', kwargs={'path': path_root})

#New JSON
def new_json(request):
    if request.method == 'POST':
        Idata.objects.all().delete()

        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='base_idata'")

        selected_directory = request.POST.get('selected_directory')

        if selected_directory:
            root = Path(selected_directory)
            directory_structure = build_directory_tree(root)

            for data in directory_structure:
                data.needUpdate = True
                if isinstance(data, Idata):
                    data.save()
                
            return render(request, 'base/new_json.html', {'directory_structure': directory_structure})
    else:
        Idata.objects.all().delete()
    return render(request, 'base/new_json.html')

#Process Result
def Process_JSON(request):
    idatas = Idata.objects.all()
    json_data, file_path  = process_json_data(idatas)
    return render(request, 'base/process.html', {'json_data': None  ,  'file_path': file_path})