provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "voicefront-store"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Remote state is not configured yet. Add an S3 + DynamoDB backend before a
  # shared or production run, and record it in README.md.
  # backend "s3" {
  #   bucket         = "voicefront-tfstate"
  #   key            = "voicefront/terraform.tfstate"
  #   region         = "ap-south-1"
  #   dynamodb_table = "voicefront-tflock"
  #   encrypt        = true
  # }
}
