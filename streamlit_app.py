import os
import tempfile
from datetime import datetime
import sys
import importlib
from PIL import Image

# Monkey patch for missing imghdr module in Python 3.13
class ImghdrMock:
    def what(self, file, h=None):
        try:
            with Image.open(file) as img:
                return img.format.lower() if img.format else None
        except Exception:
            return None

sys.modules['imghdr'] = ImghdrMock()

import streamlit as st
import requests
from urllib.parse import urlparse
from pathlib import Path
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Set page config
st.set_page_config(page_title="Animated Video Generator", layout="centered")
st.title("Animated Video Generator")

# Initialize session state variables
if 'video_path' not in st.session_state:
    st.session_state.video_path = None

# Initialize video history
if 'video_history' not in st.session_state:
    st.session_state.video_history = []

# Clean up old video files
def cleanup(keep_history=True):
    try:
        # Clean up video path if it's a local file
        if st.session_state.get('video_path') and os.path.exists(st.session_state.video_path):
            os.remove(st.session_state.video_path)
        
        # Clean up local video path if it exists
        if st.session_state.get('local_video_path') and os.path.exists(st.session_state.local_video_path):
            os.remove(st.session_state.local_video_path)
            
        # Clear session state
        current_video = st.session_state.video_path
        st.session_state.video_path = None
        st.session_state.local_video_path = None
        
        # If we're keeping history and the current video is a URL, add it to history
        if keep_history and current_video and current_video.startswith('http'):
            # Don't add duplicates
            if current_video not in [item['url'] for item in st.session_state.video_history]:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
                st.session_state.video_history.append({
                    'url': current_video,
                    'timestamp': timestamp,
                    'prompt': st.session_state.get('last_prompt', 'Unknown prompt')
                })
                # Keep only the last 5 videos
                if len(st.session_state.video_history) > 5:
                    st.session_state.video_history.pop(0)
        
    except Exception as e:
        logger.warning(f"Warning: Could not clean up temporary files: {e}")
        st.warning(f"Warning: Could not clean up temporary files: {e}")

# Get API URL from environment variable or use default
BACKEND_URL = os.getenv('BACKEND_URL', 'http://localhost:8000')
API_URL = f"{BACKEND_URL.rstrip('/')}/render"

with st.sidebar:
    st.markdown("### 💡 Sample Prompts")
    st.code("Animate a circle growing and shrinking", language="markdown")
    st.code("Show the sine wave animation", language="markdown")
    st.code("Display the Pythagorean theorem visually", language="markdown")
    
    # Display video history if available
    if st.session_state.video_history:
        st.markdown("---")
        st.markdown("### 📚 Your Video History")
        for i, video in enumerate(reversed(st.session_state.video_history)):
            with st.expander(f"Video {i+1}: {video['timestamp']}"):
                st.markdown(f"**Prompt:** {video['prompt']}")
                if st.button(f"Load Video {i+1}", key=f"load_{i}"):
                    st.session_state.video_path = video['url']
                    st.rerun()

# Display video if it exists
if st.session_state.video_path:
    if st.session_state.video_path.startswith('http'):
        # Handle GCS URL
        try:
            # Create a temporary file
            temp_dir = Path(tempfile.gettempdir()) / 'manim_videos'
            temp_dir.mkdir(exist_ok=True, parents=True)
            
            # Extract filename from URL
            parsed_url = urlparse(st.session_state.video_path)
            filename = os.path.basename(parsed_url.path)
            local_path = temp_dir / filename
            
            # Download the video
            response = requests.get(st.session_state.video_path, stream=True)
            response.raise_for_status()
            
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            st.session_state.local_video_path = str(local_path)
            
            # Display the video
            st.video(str(local_path))
            
            # Add download button
            with open(local_path, "rb") as f:
                st.download_button(
                    "📥 Download Video",
                    f,
                    file_name=filename,
                    mime="video/mp4"
                )
                
        except Exception as e:
            logger.error(f"Error loading video from URL: {e}")
            st.error(f"Error loading video: {str(e)}")
    elif os.path.exists(st.session_state.video_path):
        # Handle local file path
        st.video(st.session_state.video_path)
        with open(st.session_state.video_path, "rb") as f:
            st.download_button(
                "📥 Download Video",
                f,
                file_name="output.mp4",
                mime="video/mp4",
                on_click=cleanup
            )
    
    if st.button("Clear Video"):
        cleanup()
        st.rerun()

# Input form
with st.form("video_form"):
    prompt = st.text_area("Enter your animation prompt:", height=100)
    advanced_options = st.expander("Advanced Options")
    with advanced_options:
        output_format = st.selectbox(
            "Output Format",
            options=["mp4", "mov"],
            index=0,
            help="Select the output format for your video"
        )
    submit_button = st.form_submit_button("Generate Video")

# Handle form submission
if submit_button and prompt:
    # Save the current prompt to session state
    st.session_state.last_prompt = prompt
    
    # Create a progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    with st.spinner("Generating your animation..."):
        try:
            # Clean up any existing video
            cleanup()
            
            # Update progress
            status_text.text("Sending request to AI model...")
            progress_bar.progress(10)
            
            # Make the API request
            status_text.text("Sending request to animation service...")
            progress_bar.progress(25)
            
            response = requests.post(
                API_URL,
                json={
                    "prompt": prompt,
                    "output_format": output_format
                },
                timeout=300  # 5 minute timeout
            )
            
            # Update progress
            status_text.text("Processing API response...")
            progress_bar.progress(75)
            
            if response.status_code == 200:
                data = response.json()
                video_url = data.get("video_url")
                metadata = data.get("metadata", {})
                
                if video_url:
                    # Update progress
                    status_text.text("Video generated successfully!")
                    progress_bar.progress(100)
                    
                    # Show success message with details
                    st.success(f"Video generated successfully! Used model: {metadata.get('model', 'Unknown')}")
                    
                    # Store the GCS URL in session state
                    st.session_state.video_path = video_url
                    
                    # Force a rerun to display the video
                    st.rerun()
                else:
                    progress_bar.empty()
                    status_text.empty()
                    st.error("No video URL returned from the server.")
            else:
                try:
                    error_data = response.json()
                    error_msg = error_data.get("detail", "Unknown error occurred")
                    if "error" in error_data:
                        error_msg = f"{error_msg}: {error_data['error']}"
                except ValueError:
                    error_msg = response.text or "Unknown error occurred"
                
                # Clear progress indicators
                progress_bar.empty()
                status_text.empty()
                
                st.error(f"Error: {error_msg}")
                logger.error(f"API Error: {error_msg}")
                
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            
            # Clear progress indicators
            progress_bar.empty()
            status_text.empty()
            
            st.error(f"Failed to connect to the server: {error_msg}")
            logger.error(f"Request Exception: {error_msg}")
            cleanup()
        except Exception as e:
            error_msg = str(e)
            
            # Clear progress indicators
            progress_bar.empty()
            status_text.empty()
            
            st.error(f"An unexpected error occurred: {error_msg}")
            logger.error(f"Unexpected Error: {error_msg}", exc_info=True)
            cleanup()
