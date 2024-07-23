# views.py
from datetime import datetime
import json
from pathlib import Path
from django.shortcuts import render
from django.utils.dateparse import parse_datetime
from django.views.generic.edit import UpdateView
from django.views.generic.list import ListView
from django.urls import reverse_lazy, reverse
from django.http import HttpResponse
from django.utils.timezone import make_aware
from .json_processor import process_json_data
from  .models import Idata
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

# Update JSON
def update_json(request):
    if request.method == 'POST':
        Idata.objects.all().delete()
        form = UploadedFile(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = form.cleaned_data['file']
            try:
                data = json.load(uploaded_file)
                directory_structure = create_idata_instances(data)

                for data in directory_structure:
                    if data.level == 0:
                        directory_root = data.pathRoot

                return render(request, 'base/update_json.html', {'json_form': form, 'directory_root': directory_root})
            except json.JSONDecodeError:
                return HttpResponse('El archivo no es un JSON válido.', status=400)
    else:
        form = UploadedFile()

    return render(request, 'base/update_json.html', {'json_form': form})

def create_idata_instances(data):
    created_objects = []

    if isinstance(data, dict):
        last_update_str = data.get('created_at', None)
        last_update = None

        if last_update_str:
            parsed_updated_at = parse_datetime(last_update_str)
            if parsed_updated_at:
                last_update = make_aware(
                    parsed_updated_at) if parsed_updated_at.tzinfo is None else parsed_updated_at

        has_more_data = any(isinstance(value, (dict, list)) for value in data.values())
        save_path = data.get('savepath','')
        is_directoy = has_more_data and save_path == ""
        path = data.get('path','')

        modification_date = None
        if path:
            path_file = Path(path)
            modification_time_seconds = path_file.stat().st_mtime
            modification_date = datetime.fromtimestamp(modification_time_seconds)
            formatted_date  = modification_date.strftime("%Y-%m-%d %H:%M:%S")
            modification_date = formatted_date

        created_object = Idata.objects.create(
            name=data.get('name', ''),
            level=data.get('level', 0),
            path=path,
            pathRoot=data.get('pathroot', ''),
            description=data.get('description', ''),
            isDirectory=is_directoy,
            SavePath= save_path,
            last_update=last_update,
            modification_date=modification_date
        )

        created_objects.append(created_object)

        for key, value in data.items():
            if isinstance(value, (dict, list)):
                created_objects.extend(create_idata_instances(value))

    elif isinstance(data, list):
        for item in data:
            created_objects.extend(create_idata_instances(item))

    return created_objects

#New JSON
def new_json(request):
    if request.method == 'POST':
        Idata.objects.all().delete()
        selected_directory = request.POST.get('selected_directory')
        if selected_directory:
            root = Path(selected_directory)
            directory_structure = build_directory_tree(root)
            return render(request, 'base/new_json.html', {'directory_structure': directory_structure})
    else:
        Idata.objects.all().delete()
    return render(request, 'base/new_json.html')

#Create new directory
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
                modification_date=modification_date,
                last_update = modification_date
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
                modification_date = modification_date,
                last_update = modification_date,
            )
            file_data.save()
            tree.append(file_data)

    return tree

#Process Result
def Process_JSON(request):
    idatas = Idata.objects.all()
    json_data = process_json_data(idatas)
    return render(request, 'base/process.html', {'json_data': json.dumps(json_data, indent=4)})