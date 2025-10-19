terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {}

variable "catalog_bucket" {
  description = "Name of the existing S3 bucket to use for the Ice catalog (set via TF_VAR_catalog_bucket or CATALOG_BUCKET)"
  type        = string
}

locals {
  sqs_queue_prefix = "ice-s3watch"
}

data "aws_s3_bucket" "this" {
  bucket = var.catalog_bucket
}

resource "aws_sqs_queue" "this" {
  name_prefix = local.sqs_queue_prefix
}

resource "aws_sqs_queue_policy" "this" {
  queue_url = aws_sqs_queue.this.id
  policy    = data.aws_iam_policy_document.queue.json
}

data "aws_iam_policy_document" "queue" {
  statement {
    effect = "Allow"

    principals {
      type = "*"
      identifiers = ["*"]
    }

    actions = ["sqs:SendMessage"]
    resources = [aws_sqs_queue.this.arn]

    condition {
      test     = "ArnEquals"
      variable = "aws:SourceArn"
      values = [data.aws_s3_bucket.this.arn]
    }
  }
}

resource "aws_s3_bucket_notification" "this" {
  bucket = data.aws_s3_bucket.this.id

  queue {
    queue_arn     = aws_sqs_queue.this.arn
    events = ["s3:ObjectCreated:*"]
    filter_suffix = ".parquet"
  }
}

output "s3_bucket_name" {
  value = data.aws_s3_bucket.this.id
}

output "sqs_queue_url" {
  value = aws_sqs_queue.this.id
}
