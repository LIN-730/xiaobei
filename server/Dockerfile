FROM python:3.11-slim

WORKDIR /app

# Create celery user for worker/beat processes
RUN addgroup --system celery \
    && adduser --system --ingroup celery celery

COPY requirements.txt .
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

# Install Playwright system dependencies (Trixie-compatible)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 libnspr4 libatk-bridge2.0-0t64 libdrm2 libxkbcommon0 \
    libgbm1 libasound2t64 libxcomposite1 libxdamage1 libxrandr2 \
    libpango-1.0-0 libcairo2 libcups2t64 libatspi2.0-0t64 \
    fonts-unifont fonts-freefont-ttf && \
    rm -rf /var/lib/apt/lists/*

# Install Playwright Chromium browser only (deps already installed above)
RUN playwright install chromium

COPY app/ ./app/

RUN chown -R celery:celery /app

EXPOSE 8000

# Default: start API service
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Celery Worker (override CMD at runtime):
#   docker run --rm <image> celery -A app.sync.celery_app worker --loglevel=info --concurrency=4
#
# Celery Beat (override CMD at runtime):
#   docker run --rm <image> celery -A app.sync.celery_app beat --loglevel=info
