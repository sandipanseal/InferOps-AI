# ECR repository for the InferOps Lambda Docker image.
# The same image is used by both the API Lambda and the SQS worker Lambda;
# the worker overrides CMD via aws_lambda_function.image_config.command.
resource "aws_ecr_repository" "backend" {
  name                 = "${var.project_name}-backend-${var.environment}"
  image_tag_mutability = "MUTABLE"
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = true
  }
}

# Keep only the 5 most recent images to bound storage costs.
resource "aws_ecr_lifecycle_policy" "backend" {
  repository = aws_ecr_repository.backend.name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep last 5 images"
      selection = {
        tagStatus   = "any"
        countType   = "imageCountMoreThan"
        countNumber = 5
      }
      action = { type = "expire" }
    }]
  })
}
