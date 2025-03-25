from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from pipeline import Pipeline
from typing import Optional
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

# FastAPI app
app = FastAPI(
    title="RAG Pipeline API",
    description="A Retrieval-Augmented Generation API for querying a PostgreSQL database with Ollama LLM.",
    version="1.0.0"
)
app.mount("/templates", StaticFiles(directory="templates"), name="templates")

DATABASE_URL = "postgresql+psycopg2://postgres:280598@localhost:5432/Ecommerce"
MODEL_NAME = "llama3.2"
MAX_RETRIES = 10

# Initialize pipeline
pipeline = Pipeline(DATABASE_URL, MODEL_NAME)

# Set up templates
templates = Jinja2Templates(directory="templates")

class QuestionRequest(BaseModel):
    question: str
    limit: Optional[int] = 5  # Optional parameter with default value

# Response model
class AnswerResponse(BaseModel):
    answer: str

@app.post("/query", response_model=AnswerResponse)
async def query_database(request: QuestionRequest):
    """
    Endpoint to process a natural language question and return a response.
    """
    try:
        response = pipeline.run(request.question, max_retries=MAX_RETRIES)
        if response.startswith("Error:"):
            raise HTTPException(status_code=500, detail=response)
        return {"answer": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.get("/health")
async def health_check():
    """
    Health check endpoint to verify the API is running.
    """
    return {"status": "healthy"}

@app.get("/", response_class=HTMLResponse)
async def chat_ui(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})