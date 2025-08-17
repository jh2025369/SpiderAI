FROM python:3.12.7

WORKDIR /app

RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# RUN sudo apt-get install -y libgbm-dev libnss3 libatk-bridge2.0-0 libdrm-dev libxkbcommon-dev libgtk-3-0 libasound2
# python -m playwright install chromium

COPY . .

EXPOSE 8080

# CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]