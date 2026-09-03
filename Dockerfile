FROM python:3.12.8-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --require-hashes -r requirements.txt || pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python3", "api.py"]
