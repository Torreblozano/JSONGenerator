# views.py
import json
from pathlib import Path

# Django libraries
from django.shortcuts import render
from django.views.generic.edit import UpdateView
from django.views.generic.list import ListView
from django.urls import reverse
from django.http import HttpResponse

# Own libraries
from .json_processor import build_directory_tree, process_json_data, find_root_file, create_idata_instances
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
    fields = ['description']

    def get_success_url(self):
        print(self.object.pathRoot)
        path_root = self.object.pathRoot
        return reverse('idata_list', kwargs={'path': path_root})

#New JSON
def new_json(request):
    if request.method == 'POST':
        Idata.objects.all().delete()
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

#Update Existing JSON
def update_json(request):
    if request.method == 'POST':
        Idata.objects.all().delete()
        form = UploadedFile(request.POST, request.FILES)

        if form.is_valid():
            uploaded_file = form.cleaned_data['file']
            try:
                data = json.load(uploaded_file)
                json_structure = create_idata_instances(data)
                directory_structure = []

                root = find_root_file(json_structure)
                if root:
                    directory_structure = build_directory_tree(root)
                else:
                    return HttpResponse('No se encotró la carpeta raiz.', status=400)

                if directory_structure and json_structure:
                    make_comparison(directory_structure , json_structure)

                return render(request, 'base/update_json.html', {'json_form': form, 'directory_root': root})

            except json.JSONDecodeError:
                return HttpResponse('El archivo no es un JSON válido.', status=400)
    else:
        form = UploadedFile()

    return render(request, 'base/update_json.html', {'json_form': form})

def make_comparison(directory_structure, json_structure):
    json_dict = {}

    for dt in json_structure:
        json_dict[dt.path.replace('\\', '').replace('/', '').lower()] = dt

    for data in directory_structure:
        json_data = json_dict.get(data.path.replace('\\', '').replace('/', '').lower())
        if json_data and json_data.last_update.replace(microsecond=0) < data.last_update.replace(microsecond=0):
            data.needUpdate = True
            if isinstance(data, Idata):
                data.save()


#Process Result
def Process_JSON(request):
    idatas = Idata.objects.all()
    json_data = process_json_data(idatas)
    return render(request, 'base/process.html', {'json_data': json.dumps(json_data, indent=4)})