import json
from datetime import datetime
from .models import UploadedFile
from pathlib import Path
from django.core.files.base import ContentFile

def process_json_data(idatas):
    objects_dic = {}
    for data in idatas:
        if  data.Exclude:
            continue

        if not data.description:
            data.description = data.name

        if not data.isDirectory:
            file_path = data.path
            object_name = data.name
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
    date_now = datetime.now()
    strf_date = date_now.strftime("%Y-%m-%d %H:%M:%S")
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
        "created_at": obj.created_at,
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
class My_Object:
    def __init__(self,id, level, name, description, created_at, path, pathroot, savepath, childs):
        self.id = id
        self.level = level
        self.name = name
        self.description = description
        self.created_at = created_at
        self.path = path
        self.pathroot = pathroot
        self.savepath = savepath
        self.childs = childs

    def __str__(self):
        return (f"Name: {self.name}\n"
                f"Description: {self.description}\n"
                f"Creation date: {self.created_at}\n"
                f"Childs: {len(self.childs)}\n")
