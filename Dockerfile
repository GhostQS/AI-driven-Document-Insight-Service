# Use an official slim image
FROM python:3.11-slim

# System deps for PyMuPDF, OpenCV, fonts
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    poppler-utils \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Pre-copy requirements to leverage Docker layer cache
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY app ./app
COPY streamlit_app.py ./

# Default envs
ENV ENABLE_RAG=true \
    ENABLE_NER=false \
    EASYOCR_LANGS=en \
    EASYOCR_GPU=false

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
