from google.cloud import storage
from google.auth import default
from pathlib import Path
import os
import uuid
from datetime import datetime, timedelta
from config import config

class GCSStorage:
    def __init__(self):
        # This will automatically use Application Default Credentials (ADC)
        credentials, project = default()
        self.client = storage.Client(credentials=credentials, project=config.GCP_PROJECT_ID)
        self.bucket = self.client.bucket(config.GCS_BUCKET_NAME)
    
    def upload_file(self, local_path: str, remote_path: str = None) -> str:
        """Upload a file to GCS and return its public URL."""
        if not remote_path:
            # Generate a unique filename
            ext = Path(local_path).suffix
            remote_path = f"videos/{uuid.uuid4()}{ext}"
        
        blob = self.bucket.blob(remote_path)
        blob.upload_from_filename(local_path)
        
        # Make the blob publicly viewable
        blob.make_public()
        return blob.public_url
    
    def generate_signed_url(self, blob_name: str, expiration_hours: int = 24) -> str:
        """Generate a signed URL for a GCS object."""
        blob = self.bucket.blob(blob_name)
        url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(hours=expiration_hours),
            method="GET"
        )
        return url
        
    def download_file(self, blob_name: str, destination_path: str) -> str:
        """Download a file from GCS to a local path."""
        try:
            # Ensure the destination directory exists
            os.makedirs(os.path.dirname(destination_path), exist_ok=True)
            
            # Download the file
            blob = self.bucket.blob(blob_name)
            blob.download_to_filename(destination_path)
            
            return destination_path
        except Exception as e:
            logger.error(f"Error downloading file from GCS: {str(e)}")
            raise

# Initialize storage client
gcs_client = GCSStorage()
