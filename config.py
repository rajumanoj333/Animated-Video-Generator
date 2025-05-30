from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    # GCP Configuration
    GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
    GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")
    GCS_CREDENTIALS_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    
    # Local storage (temporary)
    TEMP_DIR = Path("/tmp/manim_output")
    
    # Validation
    @classmethod
    def validate(cls):
        required_vars = [
            ("OPENAI_API_KEY", cls.OPENAI_API_KEY),
            ("GCP_PROJECT_ID", cls.GCP_PROJECT_ID),
            ("GCS_BUCKET_NAME", cls.GCS_BUCKET_NAME),
            ("GOOGLE_APPLICATION_CREDENTIALS", cls.GCS_CREDENTIALS_PATH)
        ]
        
        missing = [name for name, value in required_vars if not value]
        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}. "
                "Please check your .env file."
            )
        
        # Ensure temp directory exists
        cls.TEMP_DIR.mkdir(parents=True, exist_ok=True)

# Initialize and validate config
config = Config()
config.validate()
