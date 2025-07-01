FROM python:3.11

RUN apt-get update && apt-get install -y \
  libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
  libdbus-1-3 libdrm2 libxkbcommon0 libxcomposite1 \
  libxdamage1 libxrandr2 libgbm1 libasound2 libxshmfence1 \
  libnspr4 libatspi2.0-0 libx11-xcb1 libxcb-dri3-0 wget curl xvfb

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

# Make sure playwright is installed
RUN playwright install

COPY . .

EXPOSE 8000

CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8000"]
