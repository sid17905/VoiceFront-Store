resource "aws_s3_bucket" "storefronts" {
  bucket = var.bucket_name
}

resource "aws_s3_bucket_public_access_block" "storefronts_public_block" {
  bucket = aws_s3_bucket.storefronts.id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket_policy" "storefronts_policy" {
  bucket = aws_s3_bucket.storefronts.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "PublicReadStorefrontsPrefix"
        Effect    = "Allow"
        Principal = "*"
        Action    = "s3:GetObject"
        Resource  = "${aws_s3_bucket.storefronts.arn}/storefronts/*"
      }
    ]
  })

  depends_on = [aws_s3_bucket_public_access_block.storefronts_public_block]
}

output "bucket_name" {
  value = aws_s3_bucket.storefronts.bucket
}
