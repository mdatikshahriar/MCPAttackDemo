FROM python:3.11-slim
WORKDIR /app
RUN pip install mcp
COPY server.py legit_server.py
CMD ["python", "legit_server.py"]
