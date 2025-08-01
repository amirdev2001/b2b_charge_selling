# --- Stage 1: Build stage ---
# Use an official Python runtime as a parent image
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /usr/src/app

# Install dependencies
# We use a virtual environment to keep dependencies isolated
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies for postgresql
RUN apt-get update && apt-get install -y libpq-dev gcc

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# --- Stage 2: Final stage ---
FROM python:3.11-slim

# Set work directory
WORKDIR /usr/src/app

# Copy the virtual environment from the builder stage
COPY --from=builder /opt/venv /opt/venv

# Set the path to include the venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy the application code
COPY . .

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application using Uvicorn ASGI server
CMD ["uvicorn", "b2b_project.asgi:application", "--host", "0.0.0.0", "--port", "8000"]