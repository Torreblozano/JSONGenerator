import json
from datetime import datetime
from django.conf import settings
from django.utils.timezone import make_aware
from .models import Idata, UploadedFile
from pathlib import Path
import pytz

### Build DDBB based on directories
def build_directory_tree(directory, level=0):
    tree = []
    for item in directory.iterdir():
        modification_time = item.stat().st_mtime
        modification_datetime = datetime.fromtimestamp(modification_time, tz=pytz.utc)

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

### Utils

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


def string_to_aware_datetime(date_string, timezone_str='UTC'):

    try:
        naive_datetime = datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
        timezone = pytz.timezone(timezone_str)
        aware_datetime = timezone.localize(naive_datetime)
        return aware_datetime
    except:
        return None

### Create a new JSON
def process_json_data(idatas):
    objects_dic = {}
    for data in idatas:

        if not data.description:
            data.description = data.name

        if  data.SavePath and data.needUpdate:
            file_path = data.path
            object_name = data.name
            last_update = datetime.strptime(data.last_update, "%Y-%m-%d %H:%M:%S")
            data.SavePath = upload_file_view(file_path)

        if not data.id in objects_dic:
            objects_dic[data.id] = Create_Class(data)

    for key, value in objects_dic.items():
        Find_childs(key, value, objects_dic)

    json_data = {}
    for obj_id, obj in objects_dic.items():
        if obj.level == 0:
            json_data[obj.name] = obj_to_dict(obj)

    json_str = json.dumps(json_data, indent=4)
    file_path = 'C:\\Users\\torre\\OneDrive\\Desktop\\Proyectos_Python\\Json_proyect\\mi_archivo.json'

    with open(file_path, 'w') as file:
        file.write(json_str)

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
    with open(local_file_path, 'rb') as f:
        file_path = Path(local_file_path)
        file_name = file_path.name

        with file_path.open('rb') as f:
            file = ContentFile(f.read(), name=file_name)
            uploaded_file = UploadedFile(file=file)
            uploaded_file.save()
            file_url = uploaded_file.file.url

        return file_url

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
