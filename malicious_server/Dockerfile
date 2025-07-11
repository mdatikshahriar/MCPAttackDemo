FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY malicious_calculator.py malicious_server.py
CMD ["python", "malicious_server.py"]
