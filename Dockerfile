FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y build-essential

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

ENV STREAMLIT_SERVER_PORT=8080
CMD ["streamlit", "run", "fork-it.py", "--server.enableCORS=false"]
