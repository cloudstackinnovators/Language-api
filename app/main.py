from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.auth.auth_routes import router as auth_router
from app.routes.protected_routes import router as protected_router
from app.routes.ai_prompt_routes import router as ai_prompt_router
from app.routes.file_upload_routes import router as file_upload_router
from app.routes.decks_routes import router as decks_router
from app.routes.dashboad_routes import router as dashboad_routes
from app.database import Base, engine
from dotenv import load_dotenv
import os


load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
print("Loaded environment variables from .env file")
print(os.getenv("OPENAI_API_KEY"))
app = FastAPI()

# Add this block before including routers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specify your frontend URL(s) instead of ["*"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

app.include_router(auth_router, prefix="/auth")
app.include_router(protected_router, prefix="/protected")
app.include_router(ai_prompt_router, prefix="/ai-prompt")
app.include_router(file_upload_router, prefix="/files")
app.include_router(decks_router, prefix="/decks")
app.include_router(dashboad_routes, prefix="/dashboard")
