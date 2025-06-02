# Animated Video Generator

A powerful web application that generates animated videos using OpenAI's GPT models and Manim. The application features a FastAPI backend for processing and a Streamlit frontend for an intuitive user interface, with Google Cloud Storage for video storage.

## ✨ Features

- 🎥 Generate animations from natural language prompts
- 🤖 Powered by OpenAI's GPT models for code generation
- 🎨 Renders animations using Manim (Mathematical Animation Engine)
- ☁️ Stores generated videos in Google Cloud Storage
- 🚀 FastAPI backend for high-performance processing
- 💻 Streamlit-based web interface
- 📱 Responsive design that works on desktop and tablet

## 🛠 Prerequisites

Before you begin, ensure you have the following:

- Python 3.8 or higher
- [Git](https://git-scm.com/)
- [Poetry](https://python-poetry.org/) (recommended) or pip
- [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) (for GCP setup)
- An [OpenAI API key](https://platform.openai.com/account/api-keys)
- A [Google Cloud Platform](https://console.cloud.google.com/) account with:
  - Google Cloud Storage API enabled
  - A storage bucket created
  - Service account credentials with appropriate permissions

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Animated-Video-Generator
```

### 2. Set Up Python Environment

#### Using Poetry (Recommended)

```bash
# Install poetry if you haven't
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install
# Activate the virtual environment
poetry shell
```

#### Using pip
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt
```

### 3. Set Up Google Cloud Storage

1. **Create a GCP Project**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project and note the Project ID

2. **Enable Required APIs**
   - Enable the Google Cloud Storage API
   - Enable the Cloud Storage JSON API

3. **Create a Storage Bucket**
   ```bash
   gsutil mb -p YOUR_PROJECT_ID gs://YOUR_BUCKET_NAME/
   ```

4. **Create a Service Account**
   - Go to IAM & Admin > Service Accounts
   - Click "Create Service Account"
   - Add the "Storage Object Admin" role
   - Create and download the JSON key file

### 4. Configure Environment Variables

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file with your configuration:
   ```env
   # OpenAI Configuration
   OPENAI_API_KEY=your_openai_api_key_here
   OPENAI_MODEL=gpt-4  # or your preferred model
   
   # Server Configuration
   PORT=8000
   ENVIRONMENT=development
   BACKEND_URL=http://localhost:8000  # Update in production
   
   # Google Cloud Storage
   GCP_PROJECT_ID=your_project_id
   GCS_BUCKET_NAME=your_bucket_name
   GOOGLE_APPLICATION_CREDENTIALS=path/to/your/service-account-key.json
   
   # Streamlit Configuration
   STREAMLIT_SERVER_PORT=8501
   STREAMLIT_SERVER_HEADLESS=true
   STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
   ```

### 5. Run the Application Locally

#### Start the Backend Server

```bash
# From the project root
uvicorn backend.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`

#### Start the Streamlit Frontend

Open a new terminal and run:

```bash
# From the project root
streamlit run backend/streamlit_app.py
```

The Streamlit app will automatically open in your default web browser at `http://localhost:8501`

### 6. Verify the Setup

1. Visit the Streamlit app at `http://localhost:8501`
2. Enter a prompt (e.g., "Create an animation of a rotating square")
3. Click "Generate Animation"
4. The app will generate the animation using Manim and display it in the browser
5. You can download the generated video using the download button

## 🚀 Deployment on Render.com

### 1. Create a Render Account

Sign up for a free account at [Render.com](https://render.com/).

### 2. Create a Web Service for the Backend

1. From your Render dashboard, click **New** and select **Web Service**.
2. Connect your GitHub repository.
3. Configure the service:
   - **Name**: `animated-video-generator-api`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r backend/requirements.txt && pip install manim`
   - **Start Command**: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Choose an appropriate plan (Free tier works for testing)

4. Add the following environment variables:
   - `OPENAI_API_KEY`
   - `OPENAI_MODEL`
   - `GCP_PROJECT_ID`
   - `GCS_BUCKET_NAME`
   - `ENVIRONMENT=production`

5. For the Google Cloud credentials, you have two options:
   
   **Option 1**: Base64 encode your JSON credentials file and add it as an environment variable:
   ```bash
   # On Windows PowerShell
   [System.Convert]::ToBase64String([System.IO.File]::ReadAllBytes("path\to\your\credentials.json"))
   
   # On Linux/Mac
   base64 -w 0 path/to/your/credentials.json
   ```
   
   Add this as an environment variable named `GOOGLE_CREDENTIALS_BASE64` and add the following to your build command:
   ```bash
   pip install -r backend/requirements.txt && pip install manim && echo $GOOGLE_CREDENTIALS_BASE64 | base64 -d > /opt/render/project/google-credentials.json && export GOOGLE_APPLICATION_CREDENTIALS=/opt/render/project/google-credentials.json
   ```

   **Option 2**: Use Render's secret files feature to upload your credentials JSON file directly.

6. Click **Create Web Service**

### 3. Create a Web Service for the Frontend

1. From your Render dashboard, click **New** and select **Web Service** again.
2. Connect your GitHub repository.
3. Configure the service:
   - **Name**: `animated-video-generator-ui`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r backend/requirements.txt`
   - **Start Command**: `cd backend && streamlit run streamlit_app.py --server.port $PORT --server.address 0.0.0.0`
   - **Plan**: Choose an appropriate plan (Free tier works for testing)

4. Add the following environment variables:
   - `BACKEND_URL` (set to the URL of your backend service, e.g., `https://animated-video-generator-api.onrender.com`)
   - `STREAMLIT_SERVER_HEADLESS=true`
   - `STREAMLIT_BROWSER_GATHER_USAGE_STATS=false`

5. Click **Create Web Service**

### 4. Update CORS Settings

If you encounter CORS issues, update your backend code in `main.py` to allow requests from your Streamlit frontend domain:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-streamlit-app-url.onrender.com", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 5. Access Your Deployed Application

Once deployment is complete, you can access your application at the URL provided by Render for your frontend service.

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|----------|
| `OPENAI_API_KEY` | Your OpenAI API key | Yes | - |
| `OPENAI_MODEL` | OpenAI model to use | No | `gpt-4` |
| `PORT` | Backend server port | No | `8000` |
| `ENVIRONMENT` | Application environment | No | `development` |
| `GCP_PROJECT_ID` | Google Cloud Project ID | Yes | - |
| `GCS_BUCKET_NAME` | Google Cloud Storage bucket name | Yes | - |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to GCP service account key | Yes | - |
| `STREAMLIT_SERVER_PORT` | Streamlit server port | No | `8501` |
| `STREAMLIT_SERVER_HEADLESS` | Run Streamlit in headless mode | No | `true` |
| `LOG_LEVEL` | Logging level | No | `INFO` |

## Google Cloud Storage Setup

1. **Bucket Permissions**
   - Ensure your service account has the `storage.objects.create` and `storage.objects.get` permissions
   - For public access, set the bucket's IAM policy to include `roles/storage.objectViewer` for `allUsers`

2. **CORS Configuration**
   Create a `cors.json` file:
   ```json
   [
     {
       "origin": ["*"],
       "method": ["GET", "HEAD", "DELETE", "POST", "PUT"],
       "responseHeader": ["Content-Type", "Access-Control-Allow-Origin"],
       "maxAgeSeconds": 3600
     }
   ]
   ```
   Then apply it:
   ```bash
   gsutil cors set cors.json gs://YOUR_BUCKET_NAME
   ```

### Local Development

For local development, you can use `uvicorn` with `--reload` for automatic code reloading:

```bash
uvicorn backend.main:app --reload --port 8000
```

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature/your-feature-name`).
3. Make your changes.
4. Commit your changes (`git commit -m 'Add new feature'`).
5. Push to the branch (`git push origin feature/your-feature-name`).
6. Create a new Pull Request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [OpenAI](https://openai.com/) for their powerful language models.
- [Manim Community](https://www.manim.community/) for the amazing animation engine.
- [FastAPI](https://fastapi.tiangolo.com/) for the fast and easy-to-use web framework.
- [Streamlit](https://streamlit.io/) for the intuitive web application framework.

## 📞 Support

If you have any questions or encounter issues, please open an issue on the GitHub repository.
