from datetime import datetime
from pathlib import Path
import os
import re
import shutil
import subprocess
import tempfile
import logging
import uuid
from typing import Optional, Dict, Any, List

import openai
from fastapi import FastAPI, HTTPException, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from openai.error import APIError, AuthenticationError, InvalidRequestError, RateLimitError
from pydantic import BaseModel

from config import config
from storage import gcs_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configure OpenAI API
openai.api_key = config.OPENAI_API_KEY
openai.api_type = "open_ai"
openai.api_base = "https://api.openai.com/v1"

# Initialize FastAPI app
app = FastAPI(title="Manim Animation Generator")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class VideoResponse(BaseModel):
    """Response model for video generation."""
    video_url: str
    message: str = "Video generated successfully"
    metadata: Dict[str, Any] = {}

class PromptRequest(BaseModel):
    """Request model for the render endpoint."""
    prompt: str
    output_format: str = "mp4"

def extract_code(text: str) -> str:
    """Extract Python code from triple backticks in the text."""
    try:
        blocks = re.findall(r"```(?:python)?\n(.*?)```", text, re.DOTALL)
        code = "\n".join(blocks).strip() if blocks else text.strip()
        logger.info(f"Extracted code length: {len(code)} characters")
        return code
    except Exception as e:
        logger.error(f"Error extracting code: {str(e)}")
        raise

def is_manim_code(code: str) -> bool:
    """Check if the code appears to be a valid Manim scene."""
    try:
        is_valid = all(keyword in code for keyword in ["Scene", "construct", "class"])
        logger.info(f"Code validation result: {is_valid}")
        return is_valid
    except Exception as e:
        logger.error(f"Error validating code: {str(e)}")
        raise

def find_video_file(search_dir: Path) -> Optional[Path]:
    """Search for a video file in the given directory."""
    try:
        for ext in ('*.mp4', '*.mov'):
            for video_file in search_dir.rglob(ext):
                if 'partial' not in str(video_file):
                    logger.info(f"Found video file: {video_file}")
                    return video_file
        logger.warning(f"No video file found in {search_dir}")
        return None
    except Exception as e:
        logger.error(f"Error finding video file: {str(e)}")
        raise

def run_manim(code: str, output_format: str = "mp4") -> str:
    """
    Run Manim with the given code and return the GCS URL of the output video.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        output_dir = tmp_path / "output"
        output_dir.mkdir(exist_ok=True)
        
        scene_file = tmp_path / "scene.py"
        
        # Write the code to a temporary file
        scene_file.write_text(code, encoding='utf-8')
        logger.info(f"Wrote code to temporary file: {scene_file}")
        
        # Run Manim
        cmd = [
            "manim",
            "--media_dir", str(output_dir),
            "-ql",  # Medium quality, 480p15
            "--output_file", "output",
            "--format", output_format,
            str(scene_file),
            "Scene"
        ]
        
        logger.info(f"Running Manim command: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                cwd=str(tmp_path),
                capture_output=True,
                text=True,
                check=True
            )
            logger.info("Manim execution successful")
            
            # Look for the output video file in the standard Manim output directory structure
            video_dir = output_dir / "videos" / "scene" / "480p15"
            video_file = video_dir / f"output.{output_format}"
            
            if not video_file.exists():
                # Try alternative location
                video_file = output_dir / f"output.{output_format}"
                if not video_file.exists():
                    logger.error("Could not find output video file")
                    logger.error(f"Manim stdout: {result.stdout}")
                    logger.error(f"Manim stderr: {result.stderr}")
                    raise FileNotFoundError(
                        "Could not find the output video file. "
                        "Please check Manim's output for errors."
                    )
            
            # Upload the video to GCS and return the public URL
            gcs_path = f"videos/{uuid.uuid4()}.{output_format}"
            video_url = gcs_client.upload_file(str(video_file), gcs_path)
            logger.info(f"Video uploaded to GCS: {video_url}")
            
            return video_url
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Manim execution failed with code {e.returncode}")
            logger.error(f"Manim stdout: {e.stdout}")
            logger.error(f"Manim stderr: {e.stderr}")
            raise RuntimeError(f"Manim failed with error: {e.stderr}")
        except Exception as e:
            logger.error(f"Error in run_manim: {str(e)}")
            raise

@app.post("/render", response_model=VideoResponse, status_code=status.HTTP_200_OK)
async def render_video(prompt_request: PromptRequest) -> Dict[str, Any]:
    """Generate a Manim animation from a text prompt and return the video URL."""
    try:
        logger.info(f"Received render request with prompt: {prompt_request.prompt[:100]}...")
        
        # Generate code using OpenAI
        try:
            response = openai.ChatCompletion.create(
                model=config.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that generates Manim code. "
                                 "Only respond with the complete Python code for a Manim animation, "
                                 "enclosed in triple backticks (```python ... ```)."
                    },
                    {
                        "role": "user",
                        "content": f"Create a Manim animation that: {prompt_request.prompt}"
                    }
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            generated_code = response.choices[0].message.content
            logger.info("Generated code from GPT-4")
            
            # Extract code from markdown code blocks
            code = extract_code(generated_code)
            
            if not is_manim_code(code):
                logger.warning("Generated code doesn't appear to be valid Manim code")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="The generated code doesn't appear to be valid Manim code."
                )
            
            # Run Manim to generate the video and upload to GCS
            video_url = run_manim(code, prompt_request.output_format)
            
            return {
                "video_url": video_url,
                "message": "Video generated and uploaded successfully",
                "metadata": {
                    "prompt": prompt_request.prompt,
                    "model": config.OPENAI_MODEL,
                    "timestamp": datetime.utcnow().isoformat(),
                    "format": prompt_request.output_format
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating video: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate video: {str(e)}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later."
        )
