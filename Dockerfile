FROM python:3.11-slim

# Install system build dependencies and Tesseract OCR for PDF parsing fallback
RUN apt-get update && apt-get install -y \
    build-essential \
    tesseract-ocr \
    libtesseract-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# Install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source folders
COPY app/ ./app/
COPY streamlit_app/ ./streamlit_app/
COPY data/ ./data/

# Expose backend (8000) and frontend (8501) ports
EXPOSE 8000
EXPOSE 8501

# Default runtime launches the FastAPI backend
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
