# S3 + CloudFront for published storefronts.
#
# The bucket is PRIVATE. Public access is served only through CloudFront using
# an Origin Access Control (OAC). This replaces the previous configuration,
# which disabled all four public-access blocks and granted `Principal: "*"`
# directly on the bucket — a public bucket despite the filename.

resource "aws_s3_bucket" "storefronts" {
  bucket = var.bucket_name

  tags = {
    Project     = "voicefront-store"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

resource "aws_s3_bucket_public_access_block" "storefronts" {
  bucket = aws_s3_bucket.storefronts.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "storefronts" {
  bucket = aws_s3_bucket.storefronts.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "storefronts" {
  bucket = aws_s3_bucket.storefronts.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "storefronts" {
  bucket = aws_s3_bucket.storefronts.id

  rule {
    id     = "expire-old-versions"
    status = "Enabled"

    filter {}

    noncurrent_version_expiration {
      noncurrent_days = 30
    }
  }
}

# ---------------------------------------------------------------------------
# CloudFront with Origin Access Control
# ---------------------------------------------------------------------------

resource "aws_cloudfront_origin_access_control" "storefronts" {
  name                              = "${var.bucket_name}-oac"
  description                       = "OAC for VoiceFront published storefronts"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

resource "aws_cloudfront_distribution" "storefronts" {
  enabled             = true
  is_ipv6_enabled     = true
  comment             = "VoiceFront storefront CDN"
  default_root_object = "index.html"
  price_class         = "PriceClass_200"

  origin {
    domain_name              = aws_s3_bucket.storefronts.bucket_regional_domain_name
    origin_id                = "s3-storefronts"
    origin_access_control_id = aws_cloudfront_origin_access_control.storefronts.id
  }

  default_cache_behavior {
    target_origin_id       = "s3-storefronts"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]
    compress               = true

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    min_ttl     = 0
    default_ttl = 3600
    max_ttl     = 86400
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    # Swap to acm_certificate_arn + ssl_support_method once a custom domain is
    # configured. An ACM certificate for CloudFront must live in us-east-1.
    cloudfront_default_certificate = true
  }

  tags = {
    Project     = "voicefront-store"
    Environment = var.environment
  }
}

data "aws_iam_policy_document" "storefronts_cloudfront" {
  statement {
    sid    = "AllowCloudFrontServicePrincipalReadOnly"
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["cloudfront.amazonaws.com"]
    }

    actions   = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.storefronts.arn}/storefronts/*"]

    condition {
      test     = "StringEquals"
      variable = "AWS:SourceArn"
      values   = [aws_cloudfront_distribution.storefronts.arn]
    }
  }
}

resource "aws_s3_bucket_policy" "storefronts" {
  bucket = aws_s3_bucket.storefronts.id
  policy = data.aws_iam_policy_document.storefronts_cloudfront.json
}

output "bucket_name" {
  value = aws_s3_bucket.storefronts.bucket
}

output "cloudfront_domain_name" {
  value = aws_cloudfront_distribution.storefronts.domain_name
}

output "cloudfront_distribution_id" {
  value = aws_cloudfront_distribution.storefronts.id
}
