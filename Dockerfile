# Use official Python image
FROM python:3.11

# Install system dependencies needed for Playwright headless browsers
RUN apt-get update && apt-get install -y \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libgtk-3-0 \
    libgtk-4-1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    libgdk-pixbuf2.0-0 \
    libwoff1 \
    libwoff2-1.0-2 \
    libvpx7 \
    libopus0 \
    libgstreamer1.0-0 \
    libgstbase-1.0-0 \
    libgstapp-1.0-0 \
    libgstvideo-1.0-0 \
    libgstpbutils-1.0-0 \
    libgsttag-1.0-0 \
    libgraphene-1.0-0 \
    libsecret-1-0 \
    libx264-155

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install

# Copy rest of the application
COPY . .

# Expose port
EXPOSE 8000

# Start Xvfb then run Gunicorn
CMD ["sh", "-c", "Xvfb :99 & export DISPLAY=:99 && gunicorn app:app --bind 0.0.0.0:8000"]
