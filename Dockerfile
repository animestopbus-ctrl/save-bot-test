FROM python:3.10-slim

# Install system dependencies (ffmpeg for media, git/curl for any cloning, etc.)
RUN apt-get update && apt-get install -y \
    git curl ffmpeg python3-pip wget bash \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy everything to /app (root files + LastPerson07/)
COPY . /app

# Set working directory to /app/LastPerson07
WORKDIR /app/LastPerson07

# Install Python dependencies (requirements.txt is at /app/requirements.txt)
RUN pip3 install wheel
RUN pip3 install --no-cache-dir -U -r /app/requirements.txt

# Expose the port (Render will use $PORT env var)
EXPOSE $PORT

# Run Flask on $PORT & main.py in background
CMD flask run -h 0.0.0.0 -p $PORT & python3 main.py
