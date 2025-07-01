# Use official Python image
FROM python:3.11

# Install system dependencies needed for Playwright headless browsers
RUN apt-get update && apt-get install -y \
    wget curl ca-certificates xvfb \
    fonts-liberation libappindicator3-1 libasound2 libatk-bridge2.0-0 \
    libatk1.0-0 libcups2 libdbus-1-3 libgdk-pixbuf2.0-0 \
    libnspr4 libnss3 libx11-xcb1 libxcomposite1 libxdamage1 \
    libxrandr2 xdg-utils libxkbcommon0 libxshmfence1 libgbm1 \
    libgtk-3-0 libxss1 libxcursor1 libgdk-3-0

# Set working directory
WORKDIR /app

# Copy requirements and install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers with dependencies
RUN playwright install --with-deps

# Copy rest of your project
COPY . .

# Expose port
EXPOSE 8000

# Start Xvfb then run Gunicorn
CMD ["sh", "-c", "Xvfb :99 & export DISPLAY=:99 && gunicorn app:app --bind 0.0.0.0:8000"]
