FROM python:3.12-slim

WORKDIR /app

# Use Aliyun apt mirror for faster system deps in China
RUN sed -i 's|deb.debian.org|mirrors.aliyun.com|g; s|security.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || true; \
    apt-get update && apt-get install -y --no-install-recommends gcc libmariadb-dev && rm -rf /var/lib/apt/lists/*

# Install deps using Aliyun pip mirror
COPY requirements.txt .
RUN pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ -r requirements.txt

# Copy source
COPY backend/ ./backend/
COPY scripts/ ./scripts/

# Create upload dir
RUN mkdir -p /app/uploads

ENV PYTHONUNBUFFERED=1

EXPOSE 8082

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8082"]
