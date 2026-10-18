variable "aws_region" {
  type    = string
  default = "ap-south-1"
}

variable "environment" {
  type    = string
  default = "production"
}

variable "bucket_name" {
  type    = string
  default = "voicefront-storefronts-prod"
}
