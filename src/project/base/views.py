# views.py
from datetime import datetime
import json
from django.shortcuts import render
from pathlib import Path
from .json_processor import process_json_data
from django.views.generic.edit import UpdateView
from django.views.generic.list import ListView
from django.urls import reverse_lazy, reverse
from  .models import Idata
from django.core.management import call_command

def index(request):
    if request.method == 'POST':
        Idata.objects.all().delete()
        selected_directory = request.POST.get('selected_directory')
        if selected_directory:
            root = Path(selected_directory)
            directory_structure = build_directory_tree(root)
            return render(request, 'base/index.html', {'directory_structure': directory_structure})
    else:
        Idata.objects.all().delete()  # Clear previous data
    return render(request, 'base/index.html')

def build_directory_tree(directory, level=0):
    tree = []

    for item in directory.iterdir():
        modification_time = item.stat().st_mtime
        modification_date = datetime.fromtimestamp(modification_time).strftime("%Y-%m-%d %H:%M:%S")

        if item.is_dir():
            directory_data = Idata(
                name=item.name,
                level=level,
                path=str(item.resolve()),
                pathRoot=str(item.parent.resolve()),
                description='',
                isDirectory=True,
                modification_date=None
            )
            directory_data.save()
            subdirectory_tree = build_directory_tree(item, level + 1)
            tree.append(directory_data)
            tree.extend(subdirectory_tree)
        else:

            file_data = Idata(
                name=item.name,
                level=level,
                path=str(item.resolve()),
                pathRoot=str(item.parent.resolve()),
                description='',
                isDirectory=False,
                modification_date = modification_date
            )
            file_data.save()
            tree.append(file_data)

    return tree

class SendDirectoryListView(ListView):
    model = Idata
    context_object_name = 'directory_structure'
    template_name = 'base/idata_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def get_object(self, queryset=None):
        # Devuelve un objeto dummy, ya que get_context_data se encargará de obtener los datos reales.
        return Idata.objects.first()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        path = self.kwargs.get('path')
        if path:
            directory_structure = Idata.objects.filter(pathRoot=path)
            context['directory_structure'] = directory_structure

            first_item = directory_structure[0]
            path_root = Path(first_item.pathRoot)
            context['parent_root'] = str(path_root.parent)
        else:
            context['directory_structure'] = None
            context['parent_root'] = None
        return context

class Edit_Data(UpdateView):
    model = Idata
    fields = ['description', 'Exclude']

    def get_success_url(self):
        print(self.object.pathRoot)
        path_root = self.object.pathRoot
        return reverse('idata_list', kwargs={'path': path_root})

def Process_JSON(request):
    idatas = Idata.objects.all()
    json_data = process_json_data(idatas)
    return render(request, 'base/process.html', {'json_data': json.dumps(json_data, indent=4)})