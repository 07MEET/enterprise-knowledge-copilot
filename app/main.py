from fastapi import FastAPI

app = FastAPI(
    title="Enterprise Knowledge Copilot",
    description="Enterprise RAG API",
    version="1.0.0"
)


@app.get("/")
def root():
    return {
        "status": "running",
        "message": "Enterprise Knowledge Copilot API",
        "version": "1.0.0"
    }
    
@app.get("/health")
def health():
    return {
        "status": "healthy"
    }

