import json
from django.conf import settings
from datetime import datetime, timedelta
from django.core.files.base import ContentFile
from django.contrib.auth import get_user_model
from .models import Idata, UploadedFile, SavedJSONS
from pathlib import Path
import pytz

# -----> Build DDBB based on directories
def build_directory_tree(directory, level=0):
    tree = []
    for item in directory.iterdir():
        modification_time = item.stat().st_mtime
        modification_datetime_utc  = datetime.fromtimestamp(modification_time, tz=pytz.utc)
        modification_datetime = modification_datetime_utc.astimezone()

        if item.is_dir():
            directory_data = Idata(
                name=item.name,
                level=level,
                path=str(item.resolve()),
                pathRoot=str(item.parent.resolve()),
                description='',
                isDirectory=True,
                last_update = modification_datetime,
                needUpdate = False
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
                last_update = modification_datetime,
                needUpdate = False
            )
            file_data.save()
            tree.append(file_data)

    return tree

# -----> Utils

#Receive a structure (or directories) and return de root file
def find_root_file(structure):
    root = ''

    for data in structure:
        if data.level == 0 and data.pathRoot and root == '':
            directory_root = data.pathRoot
            root = Path(directory_root)

    return  root

# Builds objects based on directories but withouth saving in a DDBB
def create_idata_instances(data):
    created_objects = []

    if isinstance(data, dict):
        update = data.get('last_update', '')

        has_more_data = any(isinstance(value, (dict, list)) for value in data.values())
        save_path = data.get('savepath','')
        is_directoy = has_more_data and save_path == ""

        last_update = string_to_aware_datetime(update)

        created_object = Idata(
            name=data.get('name', ''),
            level=data.get('level', 0),
            path=data.get('path','') ,
            pathRoot=data.get('pathroot', ''),
            description=data.get('description', ''),
            isDirectory=is_directoy,
            SavePath= save_path,
            last_update=last_update,
        )

        created_objects.append(created_object)

        for key, value in data.items():
            if isinstance(value, (dict, list)):
                created_objects.extend(create_idata_instances(value))

    elif isinstance(data, list):
        for item in data:
            created_objects.extend(create_idata_instances(item))

    return created_objects

def string_to_aware_datetime(date_string):

    try:
        naive_datetime = datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
        naive_datetime = naive_datetime + timedelta(hours=2)
        aware_datetime = naive_datetime.astimezone()
        return aware_datetime
    except:
        return datetime.now()

# Make a comparison betwwen local files and an exising json datas
def make_comparison(directory_structure, json_structure):
    json_dict = {}

    for dt in json_structure:
        json_dict[dt.path.replace('\\', '').replace('/', '').lower()] = dt

    for data in directory_structure:
        json_data = json_dict.get(data.path.replace('\\', '').replace('/', '').lower())

        if json_data:
            if json_data.last_update.replace(microsecond=0) < data.last_update.replace(microsecond=0):
                data.needUpdate = True
                if isinstance(data, Idata):
                    data.save()
        else:
            data.needUpdate = True
            if isinstance(data, Idata):
                data.save()

# -----> Create a new JSON
def process_json_data(idatas, user):
    json_name = ''
    json_main_path = ''
    objects_dic = {}
    for data in idatas:

        if not data.description:
            data.description = data.name

        if not data.isDirectory and data.needUpdate:
            file_path = data.path
            data.SavePath = upload_file_view(file_path)

        if not data.id in objects_dic:
            objects_dic[data.id] = Create_Class(data)

    for key, value in objects_dic.items():
        Find_childs(key, value, objects_dic)

    json_data = {}
    for obj_id, obj in objects_dic.items():
        if obj.level == 0:
            json_data[obj.name] = obj_to_dict(obj)
            if not  json_name:
                json_name = Path(obj.pathroot).name
            if not json_main_path:
                json_main_path = obj.pathroot

    if not json_name:
        json_name = "my_json"

    json_str = json.dumps(json_data, indent=4)
    BASE_DIR =  Path(__file__).resolve().parent.parent
    file_path = BASE_DIR / f"{json_name}.json"

    try:
        with open(file_path, 'w') as file:
            file.write(json_str)
        if file_path.exists():
            saved_json = save_or_update_json(user,json_name,json_main_path)
        else:
            print(f"Error: No se pudo crear el archivo JSON '{file_path}'.")
    except Exception as e:
        print(f"Error al escribir el archivo JSON: {e}")
        return None

    return json_data

def Create_Class(Idata):
    data = Idata
    strf_date = data.last_update.strftime("%Y-%m-%d %H:%M:%S")
    my_object = My_Object(data.id, data.level, data.name, data.description, strf_date, data.path, data.pathRoot, data.SavePath, None)
    return my_object

def Find_childs(id, Obj, dic):
    childs = []
    for obj in dic.values():
        if obj.pathroot == Obj.path:
            childs.append(obj)

    Obj.childs = childs
    dic[id] = Obj

def obj_to_dict(obj):
    return {
        "id": obj.id,
        "level": obj.level,
        "name": obj.name,
        "description": obj.description,
        "last_update": obj.last_update,
        "path": obj.path,
        "pathroot": obj.pathroot,
        "savepath": obj.savepath,
        "childs": [obj_to_dict(child) for child in obj.childs] if obj.childs else []
    }

def upload_file_view(local_file_path):
    file_path = Path(local_file_path)
    print(Path(local_file_path))
    file_name = file_path.parent.name + "-" + file_path.name

    uploads_dir = Path(__file__).resolve().parent.parent / 'uploads' / file_name

    if uploads_dir.exists():
        uploads_dir.unlink()

    with file_path.open('rb') as f:
        file = ContentFile(f.read(), name=file_name)
        uploaded_file = UploadedFile(file=file)
        uploaded_file.save()
        file_url = uploaded_file.file.url

    return file_url

def save_or_update_json(usuario, name, path):
    # Verificar si ya existe un SavedJSONS para el usuario con el mismo nombre
    saved_json = SavedJSONS.objects.update_or_create(
        usuario=usuario,
        name=name,
        defaults={'path': path}
    )


# Base object <<NEVER TOCUH!>>
class My_Object:
    def __init__(self,id, level, name, description, last_update, path, pathroot, savepath, childs):
        self.id = id
        self.level = level
        self.name = name
        self.description = description
        self.last_update = last_update
        self.path = path
        self.pathroot = pathroot
        self.savepath = savepath
        self.childs = childs

    def __str__(self):
        return (f"Name: {self.name}\n"
                f"Description: {self.description}\n"
                f"Creation date: {self.created_at}\n"
                f"Childs: {len(self.childs)}\n")
