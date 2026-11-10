FROM python:3.11-slim

# system deps some ML wheels need
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# run as an unprivileged user that owns the app directory
RUN useradd -m -u 1000 appuser && mkdir -p /app && chown appuser:appuser /app
ENV HOME=/home/appuser \
    HF_HOME=/home/appuser/.cache/huggingface \
    PATH=/home/appuser/.local/bin:$PATH \
    PORT=8080

WORKDIR /app
COPY --chown=appuser:appuser requirements.txt .

USER appuser
# CPU-only torch, pinned to the version the benchmarks ran on
RUN pip install --no-cache-dir torch==2.15.0 --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=appuser:appuser . .

EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]