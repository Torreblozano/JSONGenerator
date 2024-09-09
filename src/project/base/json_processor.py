import json
from pathlib import Path
from datetime import datetime, timedelta
from django.core.files.base import ContentFile
from .models import Idata, UploadedFile, SavedJSONS

# -----> Build DDBB based on directories
from datetime import datetime
import pytz

def build_directory_tree(directory, level=0):
    tree = []
    print(directory)
    print(level)

    if level == 0:
        # Processing the root directory
        modification_time = directory.stat().st_mtime
        modification_datetime_utc = datetime.fromtimestamp(modification_time, tz=pytz.utc)
        modification_datetime = modification_datetime_utc.astimezone()

        data = Idata(
            AssetName=Path(directory).name,
            AssetDescription='',
            updated_at=modification_datetime,
            level=level,
            path=str(directory),
            pathRoot='Root',  # Adjusted to match your needs
            isDirectory=True,
            needUpdate=False
        )
        data.save()
        tree.append(data)
        subdirectory_tree = build_directory_tree(directory, level + 1)
        tree.extend(subdirectory_tree)
    else:
        # Processing subdirectories and files
        for item in directory.iterdir():
            modification_time = item.stat().st_mtime
            modification_datetime_utc = datetime.fromtimestamp(modification_time, tz=pytz.utc)
            modification_datetime = modification_datetime_utc.astimezone()

            data = Idata(
                AssetName=item.name,
                AssetDescription='',
                updated_at=modification_datetime,
                level=level,
                path=str(item.resolve()),
                pathRoot=str(item.parent.resolve()),
                isDirectory=item.is_dir(),
                needUpdate=False
            )

            data.save()
            tree.append(data)

            if item.is_dir():
                subdirectory_tree = build_directory_tree(item, level + 1)
                tree.extend(subdirectory_tree)

    return tree

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
def CheckCurrentIdatas(idatas):
    objects_dic = {}
    for data in idatas:
        if not data.AssetDescription:
            data.AssetDescription = data.AssetName

        if not data.isDirectory and data.needUpdate:
            file_path = data.path
            data.SavePath = upload_file_view(file_path)

        if data.id not in objects_dic:
            objects_dic[data.id] = Create_Class(data)

    for key, value in objects_dic.items():
        Find_childs(key, value, objects_dic)

    return objects_dic

def GetRootObject(objects_dic):
    obj_root = None
    for obj_id, obj in objects_dic.items():
        if obj.level == 0:
            obj_root =  obj
            break

    return  obj_root



def process_json_data(idatas):
    objects_dic = CheckCurrentIdatas(idatas)
    obj_root = GetRootObject(objects_dic)

    if not obj_root:
        print("None root object")
        return None, None

    json_name = "MainJson"
    json_data = build_json_structure(obj_root)

    BASE_DIR = Path(__file__).resolve().parent.parent
    file_path = BASE_DIR / f"{json_name}.json"

    try:
        with open(file_path, 'w') as file:
            json.dump(json_data, file, indent=4)
        print(f"Archivo JSON guardado correctamente en '{file_path}'.")
    except Exception as e:
        print(f"Error al escribir el archivo JSON: {e}")
        return None, None

    return json_data, str(file_path)

def build_json_structure(obj):
    def remove_extension(name):
        return name.rsplit('.', 1)[0]

    def build_recursive_structure(current_obj):
        # Si el nombre del objeto es uno de los especificados, devolvemos un array de objetos JSON directamente
        if current_obj.AssetName in ["Stations", "blueprint", "Icon", "Video", "MiniMap", "Prefabs", "Pieces"]:
            if current_obj.childs:
                # Devolver una lista de los elementos hijos sin anidar
                return [build_recursive_structure(child) for child in current_obj.childs]
            else:
                return []

        # Construimos el objeto JSON normalmente
        result = {
            "AssetName": remove_extension(current_obj.AssetName),
            "AssetDescription": current_obj.AssetDescription,
            "SavePath": current_obj.SavePath,
            "updated_at": current_obj.updated_at
        }

        # Si el objeto tiene hijos, construimos la estructura recursivamente
        for child in current_obj.childs:
            child_json = build_recursive_structure(child)
            child_key = remove_extension(child.AssetName)

            if isinstance(child_json, list):
                # Si el resultado es una lista (es decir, no hay anidación), lo asignamos directamente
                result[child_key] = child_json
            else:
                # Si no es una lista, lo envolvemos en una lista
                result.setdefault(child_key, []).append(child_json)

        return result

    # Iniciamos la estructura JSON con "Machines" como el elemento principal
    machines_structure = {
        "AssetName": remove_extension(obj.AssetName),
        "AssetDescription": obj.AssetDescription,
        "SavePath": obj.SavePath,
        "updated_at": obj.updated_at,
        "Machines": []
    }

    # Añadimos todos los objetos principales bajo "Machines"
    for child in obj.childs:
        machines_structure["Machines"].append(build_recursive_structure(child))

    return machines_structure




def Create_Class(Idata):
    data = Idata
    strf_date = data.updated_at.strftime("%Y-%m-%d %H:%M:%S")
    my_object = My_Object(0, data.level, data.AssetName, data.AssetDescription, strf_date, data.path, data.pathRoot, data.SavePath, None)
    return my_object

def Find_childs(id, Obj, dic):
    childs = []
    for obj in dic.values():
        if obj.pathRoot == Obj.path:
            childs.append(obj)

    Obj.childs = childs
    dic[id] = Obj

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

class My_Object:
    def __init__(self, currentVersion, level, name, description, updated_at, path, pathRoot, savePath, childs):
        self.CurrentVersion = currentVersion
        self.level = level
        self.AssetName = name
        self.AssetDescription = description
        self.updated_at = updated_at
        self.path = path
        self.pathRoot = pathRoot
        self.SavePath = savePath
        self.childs = childs

    def __str__(self):
        return (f"Name: {self.AssetName}\n"
                f"Description: {self.AssetDescription}\n"
                f"Creation date: {self.updated_at}\n"
                f"Childs: {len(self.childs)}\n")
