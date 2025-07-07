FROM python:3.11-slim
WORKDIR /app
RUN pip install mcp psutil
COPY server.py malicious_server.py
CMD ["python", "malicious_server.py"]
