import os
import shutil
from uuid import uuid4

def save_upload_file(upload_file, folder="uploads"):
    ext = os.path.splitext(upload_file.filename)[1]
    filename = f"{uuid4().hex}{ext}"
    file_path = os.path.join(folder, filename)
    os.makedirs(folder, exist_ok=True)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
    return file_path
