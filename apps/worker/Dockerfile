FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml .
COPY apps ./apps
COPY packages ./packages
RUN pip install --no-cache-dir .
ENV PYTHONPATH=/app/apps/api
CMD ["dramatiq", "opspilot_api.jobs"]
