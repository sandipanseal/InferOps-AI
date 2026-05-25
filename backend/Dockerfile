# InferOps AI — Lambda container image
# Used by both the API Lambda (Mangum + FastAPI) and the SQS worker Lambda.
# The worker overrides CMD via Terraform image_config.command.
#
# Build context: backend/  (paths below are relative to that directory)

FROM public.ecr.aws/lambda/python:3.11

WORKDIR ${LAMBDA_TASK_ROOT}

# Install build tools so any Python package that pip resolves to a source
# distribution (e.g. when a newer version drops cp311 manylinux wheels) can
# still compile. Without this the AWS Lambda base image has no `cc`/`gcc`
# and `pip install` will abort on the first sdist it encounters.
RUN yum install -y gcc gcc-c++ make python3-devel \
    && yum clean all \
    && rm -rf /var/cache/yum

COPY pyproject.toml ./
COPY app ./app
COPY evals ./evals
COPY configs ./configs
COPY lambda_handler.py ./
COPY sqs_worker_handler.py ./

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir . \
    && python -c "from sentence_transformers import SentenceTransformer; \
       SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

CMD ["lambda_handler.handler"]
