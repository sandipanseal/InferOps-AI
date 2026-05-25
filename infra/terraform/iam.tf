# Lambda execution role — used by both the API and worker Lambdas.
resource "aws_iam_role" "lambda_exec" {
  name = "${var.project_name}-lambda-exec-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

# CloudWatch Logs (basic Lambda execution).
resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# SQS — the API Lambda sends, the worker Lambda receives & deletes.
# Both Lambdas share this role for simplicity (tiny privilege difference,
# no realistic blast-radius gain from splitting).
resource "aws_iam_role_policy" "lambda_sqs" {
  name = "${var.project_name}-lambda-sqs-${var.environment}"
  role = aws_iam_role.lambda_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid    = "SQSAccess"
      Effect = "Allow"
      Action = [
        "sqs:SendMessage",
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage",
        "sqs:GetQueueAttributes",
        "sqs:GetQueueUrl",
        "sqs:ChangeMessageVisibility"
      ]
      Resource = [
        aws_sqs_queue.jobs.arn,
        aws_sqs_queue.dlq.arn
      ]
    }]
  })
}
