import uuid
from google.cloud import storage
from fastapi import UploadFile



def upload_file_to_gcs(file: UploadFile, bucket_name: str) -> str:
    print("Initialize a GCS client and upload the file...")
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    print(f"Current Unique filename: {unique_filename}")
    blob = bucket.blob(unique_filename)
    blob.upload_from_file(file.file, content_type=file.content_type)
    blob.make_public()
    print(f"Successfully! File uploaded to GCS bucket: {bucket_name} with public URL: {blob.public_url}")
    return blob.public_url
