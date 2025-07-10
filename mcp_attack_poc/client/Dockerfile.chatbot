FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY chatbot_client.py .
CMD ["streamlit", "run", "chatbot_client.py"]
