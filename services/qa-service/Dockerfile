FROM mcr.microsoft.com/playwright/python:v1.47.0-jammy

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && apt-get install -y --no-install-recommends nodejs npm && \
    npm install -g axe-core && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

COPY services/qa-service/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY packages /app/packages
COPY data /app/data
COPY services/qa-service /app/services/qa-service

RUN mkdir -p /app/services/qa-service/node_modules && \
    ln -sf /usr/local/lib/node_modules/axe-core /app/services/qa-service/node_modules/axe-core

WORKDIR /app/services/qa-service

EXPOSE 8004

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8004/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8004"]
