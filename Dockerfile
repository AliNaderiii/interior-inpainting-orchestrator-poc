# Pin this tag to a verified digest during the release phase.
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN addgroup --system app && adduser --system --ingroup app app
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN python -m pip install --upgrade pip && python -m pip install .
USER app
EXPOSE 8000
CMD ["uvicorn", "inpainting_poc.api:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
