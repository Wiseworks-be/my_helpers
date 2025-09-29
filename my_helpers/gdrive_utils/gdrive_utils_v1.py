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


def get_file_bytes_from_drive(filename: str, folder_id: str) -> bytes:
    """
    Retrieves the content of a specific file from a Google Drive folder.

    Args:
        filename: The exact name of the file to retrieve (case-sensitive).
        folder_id: The ID of the Google Drive folder containing the file.

    Returns:
        The file content as bytes.

    Raises:
        FileNotFoundError: If the file is not found in the specified folder.
        Exception: For other Google Drive API errors during download.
    """
    service = authenticate_drive()

    # 1. Construct the search query for the specific file in the specific folder.
    # We need to ensure that the filename and folder_id are properly quoted
    # and that the 'in parents' clause is correctly structured.
    # Also, 'trashed = false' ensures we don't accidentally get a deleted file.
    query = f"'{folder_id}' in parents and name = '{filename}' and trashed = false"

    print(f"🔍 Searching for file with query: '{query}'")

    try:
        # 2. Execute the search to find the file.
        # We only need the file ID, name, and mimeType at this stage.
        results = (
            service.files()
            .list(
                q=query,
                spaces="drive",
                fields="files(id, name, mimeType)",
                pageSize=1,  # We expect at most one file with an exact name in a folder.
                # If duplicates are a concern, this would need adjustment.
            )
            .execute()
        )
        files = results.get("files", [])

        # 3. Check if the file was found.
        if not files:
            # Provide a more informative error message for debugging.
            print(f"❌ File '{filename}' not found in folder ID '{folder_id}'.")
            # Optionally, list files in the folder to help diagnose.
            # You can uncomment the following lines if needed:
            # print("Listing files in the folder for debugging:")
            # list_files_in_folder_debug(folder_id) # You'd need to implement this helper
            raise FileNotFoundError(
                f"No file named '{filename}' found in folder '{folder_id}'."
            )

        # Assuming only one file is returned due to pageSize=1 and exact name match.
        file_info = files[0]
        file_id = file_info["id"]
        print(f"✅ Found file: '{file_info['name']}' (ID: {file_id})")

        # 4. Download the file content as bytes.
        request = service.files().get_media(fileId=file_id)
        fh = BytesIO()  # Use BytesIO as an in-memory file-like object.
        downloader = MediaIoBaseDownload(fh, request)

        done = False
        while not done:
            try:
                status, done = downloader.next_chunk()
                # Optional: print progress if needed for large files
                # print(f"Download progress: {int(status.progress() * 100)}%")
            except Exception as e:
                print(f"❌ Error during download chunk: {e}")
                raise  # Re-raise the exception to be caught by the outer block

        # After download is complete, reset the BytesIO stream to the beginning.
        fh.seek(0)
        file_bytes = fh.read()

        print(
            f"✅ Successfully downloaded '{filename}' ({len(file_bytes)} bytes) into memory."
        )
        return file_bytes

    except FileNotFoundError as e:
        # Re-raise FileNotFoundError directly.
        raise e
    except Exception as e:
        # Catch any other Google Drive API errors or exceptions.
        print(f"❌ An error occurred while fetching or downloading the file: {e}")
        # It's good practice to re-raise the exception so the caller knows something went wrong.
        raise Exception(f"Google Drive API error: {e}")


# --- Helper function for debugging (Optional) ---
def list_files_in_folder_debug(folder_id):
    """Helper to list files in a folder for debugging purposes."""
    service = authenticate_drive()
    query = f"'{folder_id}' in parents and trashed = false"
    try:
        results = (
            service.files()
            .list(
                q=query,
                spaces="drive",
                fields="files(id, name)",
                pageSize=100,  # Get a reasonable number of files
            )
            .execute()
        )
        files = results.get("files", [])
        if not files:
            print(f"  - Folder '{folder_id}' is empty or could not be listed.")
        else:
            print(f"  - Found {len(files)} files:")
            for f in files:
                print(f"    - '{f['name']}' (ID: {f['id']})")
    except Exception as e:
        print(f"  - Error listing files in folder '{folder_id}': {e}")
