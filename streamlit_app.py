import os
import tempfile
from datetime import datetime
import sys
from pathlib import Path
from PIL import Image
import streamlit as st
import requests
from urllib.parse import urlparse
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

# Session state initialization
if 'video_path' not in st.session_state:
    st.session_state.video_path = None
if 'local_video_path' not in st.session_state:
    st.session_state.local_video_path = None
if 'video_history' not in st.session_state:
    st.session_state.video_history = []

# Clean up old video files
def cleanup(keep_history=True):
    try:
        current_video = st.session_state.get('video_path')
        local_path = st.session_state.get('local_video_path')

        if local_path and os.path.exists(local_path):
            os.remove(local_path)

        if current_video and os.path.exists(current_video):
            os.remove(current_video)

        st.session_state.video_path = None
        st.session_state.local_video_path = None

        if keep_history and current_video and current_video.startswith('http'):
            if current_video not in [item['url'] for item in st.session_state.video_history]:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
                st.session_state.video_history.append({
                    'url': current_video,
                    'timestamp': timestamp,
                    'prompt': st.session_state.get('last_prompt', 'Unknown prompt')
                })
                if len(st.session_state.video_history) > 5:
                    st.session_state.video_history.pop(0)

    except Exception as e:
        logger.warning(f"Cleanup failed: {e}")
        st.warning("Could not clean up temporary files.")

# API endpoint
BACKEND_URL = os.getenv('BACKEND_URL', 'http://localhost:8000')
API_URL = f"{BACKEND_URL.rstrip('/')}/render"

# Sidebar
with st.sidebar:
    st.markdown("### 💡 Sample Prompts")
    st.code("Animate a circle growing and shrinking", language="markdown")
    st.code("Show the sine wave animation", language="markdown")
    st.code("Display the Pythagorean theorem visually", language="markdown")

    if st.session_state.video_history:
        st.markdown("---")
        st.markdown("### 📚 Your Video History")
        for i, video in enumerate(reversed(st.session_state.video_history)):
            with st.expander(f"Video {i+1}: {video['timestamp']}"):
                st.markdown(f"**Prompt:** {video['prompt']}")
                if st.button(f"Load Video {i+1}", key=f"load_{i}"):
                    st.session_state.video_path = video['url']
                    st.rerun()

# Show video if available
if st.session_state.video_path:
    try:
        if st.session_state.video_path.startswith('http'):
            temp_dir = Path(tempfile.gettempdir()) / 'manim_videos'
            temp_dir.mkdir(parents=True, exist_ok=True)
            filename = os.path.basename(urlparse(st.session_state.video_path).path)
            local_path = temp_dir / filename

            response = requests.get(st.session_state.video_path, stream=True)
            response.raise_for_status()

            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            st.session_state.local_video_path = str(local_path)
            st.video(str(local_path))

            with open(local_path, "rb") as f:
                st.download_button("📥 Download Video", f, file_name=filename, mime="video/mp4")

        elif os.path.exists(st.session_state.video_path):
            st.video(st.session_state.video_path)
            with open(st.session_state.video_path, "rb") as f:
                st.download_button("📥 Download Video", f, file_name="output.mp4", mime="video/mp4", on_click=cleanup)

    except Exception as e:
        logger.error(f"Failed to load video: {e}")
        st.error(f"Error loading video: {e}")

    if st.button("Clear Video"):
        cleanup()
        st.rerun()

# Input form
with st.form("video_form"):
    prompt = st.text_area("Enter your animation prompt:", height=100)
    with st.expander("Advanced Options"):
        output_format = st.selectbox("Output Format", options=["mp4", "mov"], index=0)
    submit_button = st.form_submit_button("Generate Video")

# Handle submission
if submit_button and prompt:
    st.session_state.last_prompt = prompt
    progress_bar = st.progress(0)
    status_text = st.empty()

    with st.spinner("Generating your animation..."):
        try:
            cleanup()
            status_text.text("Sending request...")
            progress_bar.progress(20)

            response = requests.post(
                API_URL,
                json={"prompt": prompt, "output_format": output_format},
                timeout=300
            )
            progress_bar.progress(60)

            if response.status_code == 200:
                data = response.json()
                video_url = data.get("video_url")
                metadata = data.get("metadata", {})

                if video_url:
                    progress_bar.progress(100)
                    status_text.text("Video generated!")
                    st.success(f"Generated using model: {metadata.get('model', 'Unknown')}")
                    st.session_state.video_path = video_url
                    st.rerun()
                else:
                    st.error("No video URL returned.")
            else:
                try:
                    error_data = response.json()
                    error_msg = error_data.get("detail", "Unknown error")
                except Exception:
                    error_msg = response.text or "Unknown error"
                st.error(f"Error: {error_msg}")
                logger.error(f"API Error: {error_msg}")
            progress_bar.empty()
            status_text.empty()

        except requests.exceptions.RequestException as e:
            st.error(f"Failed to connect to server: {e}")
            logger.error(f"Request failed: {e}")
            cleanup()
        except Exception as e:
            st.error(f"Unexpected error: {e}")
            logger.error(f"Unexpected error: {e}", exc_info=True)
            cleanup()
