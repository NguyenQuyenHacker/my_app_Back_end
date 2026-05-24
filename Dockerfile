# =========================================
# Dockerfile cho FastAPI Backend
# =========================================

# Base image: Python 3.11 slim (~150MB)
FROM python:3.11-slim

# Tối ưu Python runtime
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Working directory trong container
WORKDIR /app

# Copy requirements.txt TRƯỚC (tận dụng Docker layer cache)
# Nếu code đổi mà deps không đổi, Docker dùng lại layer cài deps
COPY requirements.txt .

# Cài Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy application code (sau khi cài deps)
COPY app/ ./app/
COPY scripts/ ./scripts/

# Port informational (Render inject $PORT động lúc run)
EXPOSE 8000

# Start command — bind 0.0.0.0 (không phải localhost) + dùng $PORT từ env
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
