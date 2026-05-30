# Stage 1: Build dependencies
FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Final minimal GxP reproducible image
FROM python:3.11-slim AS runner

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed python packages from builder stage
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy codebase
COPY . .

# Environment variables for reproducibility
ENV PYTHONUNBUFFERED=1
ENV GXP_COMPLIANCE_MODE=1

# Expose Streamlit default port
EXPOSE 8501

# Execute E2E test pipeline run by default
CMD ["python", "tests/test_pipeline.py"]
