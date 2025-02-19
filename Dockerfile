# Use an official Python runtime as the base image
FROM python:3.13-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

RUN playwright install --with-deps chromium

# Expose the port the app runs on
EXPOSE 3003

# Command to run the application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "3003"]