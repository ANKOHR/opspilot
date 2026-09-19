FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml .
COPY apps ./apps
COPY packages ./packages
RUN pip install --no-cache-dir .
ENV PYTHONPATH=/app/apps/api
# Keep the default worker footprint bounded on small hosted instances.
CMD ["dramatiq", "--processes", "2", "--threads", "4", "opspilot_api.jobs"]
