# Dead-letter queue: receives messages that fail processing 3 times.
# 14-day retention gives time to investigate before AWS purges.
resource "aws_sqs_queue" "dlq" {
  name                      = "${var.project_name}-jobs-dlq-${var.environment}"
  message_retention_seconds = 1209600
}

# Main job queue — API Lambda → Worker Lambda.
# visibility_timeout_seconds must be >= worker Lambda timeout (60s below).
resource "aws_sqs_queue" "jobs" {
  name                       = "${var.project_name}-jobs-${var.environment}"
  visibility_timeout_seconds = 60
  message_retention_seconds  = 86400

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = 3
  })
}
