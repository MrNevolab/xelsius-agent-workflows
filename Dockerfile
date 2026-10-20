FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir "mistralai>=1.0" "mistralai-workflows[mistralai]>=3.10" "pydantic>=2"

COPY src /app/src

ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

CMD ["python", "src/entrypoints/worker.py"]
