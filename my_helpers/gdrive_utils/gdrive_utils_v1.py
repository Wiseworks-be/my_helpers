# gdrive_oauth_uploader.py
import os
from io import BytesIO
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload

SCOPES = ["https://www.googleapis.com/auth/drive.file"]


def authenticate_drive():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return build("drive", "v3", credentials=creds)


def upload_doc_from_memory(file_content, filename, mime_type, folder_id):
    service = authenticate_drive()
    file_metadata = {"name": filename, "parents": [folder_id]}
    media = MediaIoBaseUpload(BytesIO(file_content), mimetype=mime_type, resumable=True)
    uploaded_file = (
        service.files()
        .create(body=file_metadata, media_body=media, fields="id, name, webViewLink")
        .execute()
    )
    print(f"✅ Uploaded '{uploaded_file['name']}' → {uploaded_file['webViewLink']}")
    return uploaded_file


def search_file_in_folder(filename, folder_id):
    service = authenticate_drive()
    query = f"'{folder_id}' in parents and name = '{filename}' and trashed = false"

    results = (
        service.files()
        .list(
            q=query,
            spaces="drive",
            fields="files(id, name, mimeType, webViewLink)",
            pageSize=10,
        )
        .execute()
    )
    files = results.get("files", [])

    if not files:
        print(f"❌ No file named '{filename}' found in folder {folder_id}.")
        return None

    print(f"✅ Found {len(files)} file(s):")
    for f in files:
        print(f"  - {f['name']} ({f['id']}) → {f['webViewLink']}")

    return files


def get_file_bytes_from_drive(filename, folder_id):
    service = authenticate_drive()

    # 🔍 Step 1: Search file in folder
    query = f"'{folder_id}' in parents and name = '{filename}' and trashed = false"
    results = (
        service.files()
        .list(
            q=query,
            spaces="drive",
            fields="files(id, name, mimeType)",
            pageSize=1,
        )
        .execute()
    )
    files = results.get("files", [])

    if not files:
        raise FileNotFoundError(f"No file named '{filename}' in folder {folder_id}")

    file_id = files[0]["id"]

    # 📥 Step 2: Download as bytes
    request = service.files().get_media(fileId=file_id)
    fh = BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()

    fh.seek(0)
    file_bytes = fh.read()

    print(f"✅ Downloaded '{filename}' ({len(file_bytes)} bytes) into memory")
    return file_bytes


def list_files_in_folder(folder_id):
    service = authenticate_drive()
    results = (
        service.files()
        .list(
            q=f"'{folder_id}' in parents and trashed = false",
            spaces="drive",
            fields="files(id, name, mimeType, webViewLink)",
            pageSize=100,
        )
        .execute()
    )
    files = results.get("files", [])
    for f in files:
        print(f"📄 {f['name']} ({f['id']})")
    return files


def debug_list_root():
    service = authenticate_drive()
    results = (
        service.files()
        .list(
            q="mimeType = 'application/vnd.google-apps.folder' and trashed = false",
            fields="files(id, name)",
            pageSize=50,
        )
        .execute()
    )
    folders = results.get("files", [])
    for f in folders:
        print(f"📁 {f['name']} ({f['id']})")
    return folders
