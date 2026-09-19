FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml .
COPY apps/api ./apps/api
COPY packages ./packages
RUN pip install --no-cache-dir .
ENV PYTHONPATH=/app/apps/api
CMD ["sh", "-c", "uvicorn opspilot_api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
