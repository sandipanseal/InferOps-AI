# ── API Lambda (FastAPI + Mangum) ─────────────────────────────────────────────
#
# 2048MB is required, not just nice-to-have:
#   - Lambda allocates vCPU proportional to memory. At 1024MB (~0.5 vCPU)
#     the heavy imports (langchain + ragas + sentence-transformers + sqlalchemy)
#     blow past Lambda's hard 10s init-phase ceiling. 2048MB gives ~1 vCPU
#     and roughly halves init time.
#   - SentenceTransformers MiniLM needs ~600-700MB peak; 1024MB also leaves
#     no headroom for inflight RAG queries.
# 30s timeout covers slow LLM responses + pgvector retrieval.
# Architecture stays at default x86_64 — every wheel we depend on ships
# manylinux_2_28 cp312 binaries.
resource "aws_lambda_function" "api" {
  function_name = "${var.project_name}-api-${var.environment}"
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.backend.repository_url}:latest"

  role        = aws_iam_role.lambda_exec.arn
  memory_size = 2048
  # 120s ceiling for the *function* timeout. Lambda's init phase is capped
  # at 10s and we already keep it under 2s (torch is NOT imported at module
  # load). The first chat / RAG request on a freshly-spun warm container
  # then has to: load torch (~5s), load the SentenceTransformer model from
  # the pre-baked image cache (~3s), run first inference / graph compile
  # (~5-10s), pgvector connect (~1s), LLM provider call (1-30s depending on
  # the route). 60s was too tight when all of those compound; 120s comfortably
  # covers the worst case. Warm requests still finish in <500ms.
  timeout     = 120

  environment {
    variables = {
      DATABASE_URL          = var.database_url
      REDIS_URL             = var.redis_url
      OPENAI_API_KEY        = var.openai_api_key
      OLLAMA_CLOUD_API_KEY  = var.ollama_cloud_api_key
      OLLAMA_CLOUD_BASE_URL = var.ollama_cloud_base_url
      OLLAMA_CLOUD_MODEL    = var.ollama_cloud_model
      LANGFUSE_PUBLIC_KEY   = var.langfuse_public_key
      LANGFUSE_SECRET_KEY   = var.langfuse_secret_key
      LANGFUSE_HOST         = var.langfuse_host
      SQS_QUEUE_URL         = aws_sqs_queue.jobs.url
      AWS_REGION_NAME       = var.aws_region
      ENVIRONMENT           = var.environment
      LOG_LEVEL             = "INFO"
    }
  }

  depends_on = [aws_iam_role_policy_attachment.lambda_basic_execution]
}

# ── SQS Worker Lambda ─────────────────────────────────────────────────────────
#
# Same Docker image as the API Lambda — image_config.command swaps the entry
# point to sqs_worker_handler.handler. Avoids maintaining a second build.
resource "aws_lambda_function" "worker" {
  function_name = "${var.project_name}-worker-${var.environment}"
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.backend.repository_url}:latest"

  role        = aws_iam_role.lambda_exec.arn
  memory_size = 512
  timeout     = 60

  image_config {
    command = ["sqs_worker_handler.handler"]
  }

  environment {
    variables = {
      DATABASE_URL        = var.database_url
      LANGFUSE_PUBLIC_KEY = var.langfuse_public_key
      LANGFUSE_SECRET_KEY = var.langfuse_secret_key
      LANGFUSE_HOST       = var.langfuse_host
      ENVIRONMENT         = var.environment
      LOG_LEVEL           = "INFO"
      # Worker doesn't run init_db itself — the API Lambda owns schema bootstrap.
      INFEROPS_SKIP_INIT_DB = "1"
    }
  }

  depends_on = [aws_iam_role_policy_attachment.lambda_basic_execution]
}

# SQS → Worker Lambda event source mapping.
# ReportBatchItemFailures lets the worker mark individual messages as failed
# (the rest of the batch is still acked).
resource "aws_lambda_event_source_mapping" "sqs_trigger" {
  event_source_arn                   = aws_sqs_queue.jobs.arn
  function_name                      = aws_lambda_function.worker.arn
  batch_size                         = 10
  maximum_batching_window_in_seconds = 5
  function_response_types            = ["ReportBatchItemFailures"]
}

# Allow API Gateway to invoke the API Lambda.
resource "aws_lambda_permission" "api_gateway_invoke" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
}
