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
from django.contrib.auth.views import LoginView
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect

# Own libraries
from .json_processor import build_directory_tree, process_json_data, find_root_file, create_idata_instances,make_comparison
from .models import Idata, SavedJSONS
from .forms import UploadedFile

#Views

class Login(LoginView):
    template_name = "base/login.html"
    field = '__all__'
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('index')

class SignUp(FormView):
    template_name = 'base/signup.html'
    form_class = UserCreationForm
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('index')

def index(request):
    user = request.user
    saved_jsons = SavedJSONS.objects.filter(usuario=user)
    context = {
        'saved_jsons': saved_jsons
    }
    return render(request, 'base/index.html', context)

class SendDirectoryListView(LoginRequiredMixin, ListView):
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

class Edit_Data(LoginRequiredMixin,UpdateView):
    model = Idata
    fields = ['description']

    def get_success_url(self):
        print(self.object.pathRoot)
        path_root = self.object.pathRoot
        return reverse('idata_list', kwargs={'path': path_root})

#New JSON
def new_json(request):
    if not request.user.is_authenticated:
        return redirect('login')

    if request.method == 'POST':
        Idata.objects.all().delete()
        selected_directory = request.POST.get('selected_directory')
        if selected_directory:
            root = Path(selected_directory)
            print(root)

            if SavedJSONS.objects.filter(path=str(root)).exists():
                print('AAAAAAAA')

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
    if not request.user.is_authenticated:
        return redirect('login')

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

#Process Result
def Process_JSON(request):
    idatas = Idata.objects.all()
    json_data = process_json_data(idatas, request.user)
    return render(request, 'base/process.html', {'json_data': json.dumps(json_data, indent=4)})