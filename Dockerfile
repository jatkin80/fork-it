# Base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y build-essential

# Copy files
COPY . /app

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Streamlit specific
ENV PORT=8501
EXPOSE 8501

# Entry point
CMD ["streamlit", "run", "fork_it.py", "--server.port=8501", "--server.enableCORS=false"]
