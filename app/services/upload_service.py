from pathlib import Path
from uuid import uuid4
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def save_upload(file, upload_folder):
    if not file or file.filename == "":
        return None

    if not allowed_file(file.filename):
        raise ValueError("Formato inválido. Use PNG, JPG, JPEG ou WEBP.")

    original = secure_filename(file.filename)
    ext = original.rsplit(".", 1)[1].lower()
    filename = f"{uuid4().hex}.{ext}"

    folder = Path(upload_folder)
    folder.mkdir(parents=True, exist_ok=True)

    file.save(folder / filename)
    return filename
