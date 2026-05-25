# InferOps AI — local-development backend image.
# Used by infra/docker-compose.yml and the regression-test CI.
#
# For AWS Lambda deployment see backend/Dockerfile.lambda.

FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
COPY app ./app
COPY evals ./evals
COPY configs ./configs

RUN pip install --no-cache-dir .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host=0.0.0.0", "--port=8000"]
