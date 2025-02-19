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

RUN wget https://github.com/JohannesKaufmann/html-to-markdown/releases/download/v2.2.2/html2markdown_2.2.2_linux_amd64.deb
RUN apt install ./html2markdown_2.2.2_linux_amd64.deb 

# Copy the rest of the application code
COPY . .

RUN playwright install --with-deps chromium

# Expose the port the app runs on
EXPOSE 3003

# Command to run the application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "3003"]