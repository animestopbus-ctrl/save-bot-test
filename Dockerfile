FROM python:3.10-slim

# Install system dependencies (ffmpeg for media, git/curl for any cloning, etc.)
RUN apt-get update && apt-get install -y \
    git curl ffmpeg python3-pip wget bash \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy everything to /app
COPY . /app

# Set working directory to LastPerson07 (assuming this is where main.py and plugins/ are)
WORKDIR /app/LastPerson07

# Copy and install requirements (from repo root, but WORKDIR handles)
COPY ../requirements.txt /app/LastPerson07/

# Install Python dependencies
RUN pip3 install wheel
RUN pip3 install --no-cache-dir -U -r requirements.txt

# Expose the port (Render will use $PORT env var)
EXPOSE $PORT

# Run Flask on $PORT & main.py in background
CMD flask run -h 0.0.0.0 -p $PORT & python3 main.py
