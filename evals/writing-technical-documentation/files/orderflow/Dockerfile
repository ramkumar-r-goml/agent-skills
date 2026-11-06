FROM python:3.12-slim
WORKDIR /app
COPY src/ ./src/
ENV PYTHONPATH=/app/src
CMD ["python3", "-m", "orderflow.api"]
