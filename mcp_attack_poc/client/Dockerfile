FROM python:3.11-slim
WORKDIR /app
RUN pip install mcp psutil
COPY client.py .
CMD ["python", "client.py"]
