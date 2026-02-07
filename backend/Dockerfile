FROM python:3.12-slim

WORKDIR /app
COPY backend/pyproject.toml /app/pyproject.toml
COPY backend /app
RUN pip install --no-cache-dir -e ".[dev]"

EXPOSE 8080
CMD ["uvicorn", "ocg.main:app", "--host", "0.0.0.0", "--port", "8080"]

