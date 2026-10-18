FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app:/app/packages
ENV PYTHONDONTWRITEBYTECODE=1

COPY services/layout-service/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY packages /app/packages
COPY data /app/data
COPY services/layout-service /app/services/layout-service

RUN useradd --create-home --uid 10001 appuser && chown -R appuser /app
USER appuser

WORKDIR /app/services/layout-service

EXPOSE 8003

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8003/health', timeout=3).status == 200 else 1)"

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003"]
