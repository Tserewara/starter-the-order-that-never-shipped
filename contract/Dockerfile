FROM python:3.12.8-slim
RUN pip install --no-cache-dir httpx==0.28.1 "psycopg[binary]==3.2.3"
WORKDIR /contract
COPY . .
CMD ["python3", "-m", "unittest", "-v", "test_contract"]
