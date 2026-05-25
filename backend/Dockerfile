# InferOps AI — Lambda container image
# Used by both the API Lambda (Mangum + FastAPI) and the SQS worker Lambda.
# The worker overrides CMD via Terraform image_config.command.
#
# Build context: backend/  (paths below are relative to that directory)

FROM public.ecr.aws/lambda/python:3.11

WORKDIR ${LAMBDA_TASK_ROOT}

COPY pyproject.toml ./
COPY app ./app
COPY evals ./evals
COPY configs ./configs
COPY lambda_handler.py ./
COPY sqs_worker_handler.py ./

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

# Pre-download the embedding model so cold starts don't pay a 300MB download.
RUN python -c "from sentence_transformers import SentenceTransformer; \
    SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

CMD ["lambda_handler.handler"]
