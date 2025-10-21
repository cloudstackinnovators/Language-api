# LanguageApp Backend

A FastAPI backend for language learning, featuring authentication, AI prompt integration, and file upload support.

## Features

- User registration and login with JWT authentication
- Protected routes
- AI prompt endpoint (OpenAI integration)
- File upload endpoint

## Requirements

- Python 3.11+
- MySQL server
- [requirements.txt](languge_backend/requirements.txt) dependencies

## Setup Guide

1. **Clone the repository**

   ```sh
   git clone <your-repo-url>
   cd languge_backend
   ```

2. **Create and activate a virtual environment**

   ```sh
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies**

   ```sh
   pip install -r requirements.txt
   ```

4. **Configure environment variables**

   - Create a `.env` file in `languge_backend/app/` (see [.gitignore](../.gitignore)).
   - Add your OpenAI API key and any other secrets:
     ```
     OPENAI_API_KEY=your_openai_api_key
     ```

5. **Configure the database**

   - Update the MySQL connection string in [app/database.py](languge_backend/app/database.py) if needed.
   - Ensure your MySQL server is running and the database (`languageapp_db`) exists.

6. **Run the server**

   ```sh
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

7. **API Endpoints**

   - **Auth:** `/auth/register`, `/auth/login`
   - **Protected:** `/protected/`
   - **AI Prompt:** `/ai-prompt/`
   - **File Upload:** `/files/upload`

## Notes

- Uploaded files are saved in the `uploads/` directory.
- The OpenAI API key must be set in your environment or `.env` file.
- For development, use the `--reload` flag with `uvicorn`.

## License

MIT