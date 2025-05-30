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

# 🚀 Getting Started

## 1. Clone the Repository

```bash
git clone <repository-url>
cd Animated-Video-Generator
```

## 2. Set Up Python Environment

### Using Poetry (Recommended)

```bash
# Install poetry if you haven't
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install
# Activate the virtual environment
poetry shell
```

### Using pip
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 3. Set Up Google Cloud Storage

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

## 4. Configure Environment Variables

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
   
   # Google Cloud Storage
   GCP_PROJECT_ID=your_project_id
   GCS_BUCKET_NAME=your_bucket_name
   GOOGLE_APPLICATION_CREDENTIALS=path/to/your/service-account-key.json
   
   # Streamlit Configuration
   STREAMLIT_SERVER_PORT=8501
   STREAMLIT_SERVER_HEADLESS=true
   STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
   ```

## 5. Run the Application

### Start the Backend Server

```bash
# From the project root
uvicorn backend.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`

### Start the Streamlit Frontend

Open a new terminal and run:

```bash
# From the project root
streamlit run backend/streamlit_app.py
```

The Streamlit app will automatically open in your default web browser at `http://localhost:8501`

## 6. Verify the Setup

1. Visit the Streamlit app at `http://localhost:8501`
2. Enter a prompt (e.g., "Create an animation of a rotating square")
3. Click "Generate Animation"
4. The app will generate the animation using Manim and display it in the browser
5. You can download the generated video using the download button

## 🔧 Configuration

## Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
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

## Deployment

### Netlify

1. Push your code to a Git repository
2. Create a new site in Netlify and connect your repository
3. Set up the following build settings:
   - Build command: `cd frontend && npm run build`
   - Publish directory: `frontend/build`
   - Environment variables: Add all variables from your `.env` file


# 🚀 Deployment

## Local Development

```bash
# Start backend
uvicorn backend.main:app --reload --port 8000

# In a separate terminal, start frontend
streamlit run backend/streamlit_app.py
```

## Production Deployment

### 1. Set Environment to Production

```env
ENVIRONMENT=production
```

### 2. Use a Production Server

For the backend, use a production ASGI server like Uvicorn with Gunicorn:

```bash
pip install gunicorn

gunicorn backend.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### 3. Set Up a Reverse Proxy

Use Nginx or Apache as a reverse proxy:

```nginx
# Nginx configuration example
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://localhost:8501;  # Streamlit
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    location /api/ {
        proxy_pass http://localhost:8000/;  # FastAPI
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

### 4. Set Up HTTPS

Use Let's Encrypt for free SSL certificates:

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d yourdomain.com
```

## 🐳 Docker Deployment (Optional)

1. Build the Docker image:
   ```bash
   docker build -t animated-video-generator .
   ```

2. Run the container:
   ```bash
   docker run -p 8501:8501 -p 8000:8000 --env-file .env animated-video-generator
   ```

# 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

# 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

# 🙏 Acknowledgments

- [OpenAI](https://openai.com) for the powerful GPT models
- [Manim Community](https://www.manim.community/) for the amazing animation engine
- [FastAPI](https://fastapi.tiangolo.com/) for the high-performance backend
- [Streamlit](https://streamlit.io/) for the easy-to-use frontend
- All contributors who help improve this project

# 📞 Support

For support, please open an issue in the GitHub repository.
