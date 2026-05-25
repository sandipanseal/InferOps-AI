output "ecr_repository_url" {
  description = "ECR URL — set as ECR_REPOSITORY in GitHub Actions secrets"
  value       = aws_ecr_repository.backend.repository_url
}

output "api_lambda_function_name" {
  description = "API Lambda function name — used by `aws lambda update-function-code`"
  value       = aws_lambda_function.api.function_name
}

output "worker_lambda_function_name" {
  description = "Worker Lambda function name — also updated on each deploy"
  value       = aws_lambda_function.worker.function_name
}

output "api_url" {
  description = "API Gateway invoke URL — set as NEXT_PUBLIC_API_BASE_URL for frontend build"
  value       = aws_apigatewayv2_stage.default.invoke_url
}

output "sqs_queue_url" {
  description = "SQS jobs queue URL — already wired into Lambda env vars"
  value       = aws_sqs_queue.jobs.url
}

output "sqs_dlq_url" {
  description = "Dead-letter queue URL — inspect here when worker jobs fail"
  value       = aws_sqs_queue.dlq.url
}

output "frontend_bucket" {
  description = "S3 bucket name for the frontend — `aws s3 sync` target"
  value       = aws_s3_bucket.frontend.id
}

output "frontend_cloudfront_id" {
  description = "CloudFront distribution ID — `aws cloudfront create-invalidation`"
  value       = aws_cloudfront_distribution.frontend.id
}

output "frontend_url" {
  description = "Public site URL — share this with recruiters"
  value       = "https://${aws_cloudfront_distribution.frontend.domain_name}"
}
