# Use an official lightweight Python image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

RUN apt-get update && apt-get install ffmpeg libsm6 libxext6  -y
RUN pip install nltk
RUN python -m nltk.downloader punkt

# Copy application files
COPY app/requirements.txt .
# Install dependencies
RUN --mount=type=cache,target=/root/.cache \
    pip install -r requirements.txt

COPY app/ app/

# Expose port
EXPOSE 5000

# Run the application
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app.main:app"]
