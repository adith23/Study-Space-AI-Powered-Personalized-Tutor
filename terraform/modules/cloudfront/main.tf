# CloudFront CDN — Always Free: 1 TB transfer + 10M requests/month
#
# Routes traffic to two Lambda Function URL origins:
#   /api/*  → API Lambda Function URL
#   /*      → Frontend Lambda Function URL

locals {
  # Strip https:// and trailing slash from Function URLs
  api_origin_domain      = replace(replace(var.api_function_url, "https://", ""), "/", "")
  frontend_origin_domain = replace(replace(var.frontend_function_url, "https://", ""), "/", "")
}



resource "aws_cloudfront_distribution" "main" {
  enabled             = true
  is_ipv6_enabled     = true
  comment             = "${var.project} — ${var.environment}"
  default_root_object = ""
  price_class         = "PriceClass_100" # US + EU only (cheapest, stays free)

  # ── Frontend Origin (default) ─────────────────────────────
  origin {
    domain_name = local.frontend_origin_domain
    origin_id   = "frontend"

    custom_header {
      name  = "x-forwarded-host"
      value = "dlre2fiteh59k.cloudfront.net"
    }

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  # ── API Origin ────────────────────────────────────────────
  origin {
    domain_name = local.api_origin_domain
    origin_id   = "api"

    custom_origin_config {
      http_port                = 80
      https_port               = 443
      origin_protocol_policy   = "https-only"
      origin_ssl_protocols     = ["TLSv1.2"]
      origin_read_timeout      = 60
      origin_keepalive_timeout = 5
    }
  }

  # ── Default behavior → Frontend ───────────────────────────
  default_cache_behavior {
    target_origin_id           = "frontend"
    viewer_protocol_policy     = "redirect-to-https"
    allowed_methods            = ["GET", "HEAD", "OPTIONS", "PUT", "PATCH", "POST", "DELETE"]
    cached_methods             = ["GET", "HEAD"]
    compress                   = true
    response_headers_policy_id = aws_cloudfront_response_headers_policy.security.id

    forwarded_values {
      query_string = true
      headers      = ["Origin", "Authorization", "Content-Type", "Accept", "Next-Action", "Next-Router-State-Tree", "Next-Url"]
      cookies {
        forward = "all"
      }
    }

    min_ttl     = 0
    default_ttl = 300   # 5 min cache for SSR pages
    max_ttl     = 86400 # 1 day max
  }

  # ── /api/* → API Lambda (no caching) ──────────────────────
  ordered_cache_behavior {
    path_pattern               = "/api/*"
    target_origin_id           = "api"
    viewer_protocol_policy     = "redirect-to-https"
    allowed_methods            = ["GET", "HEAD", "OPTIONS", "PUT", "PATCH", "POST", "DELETE"]
    cached_methods             = ["GET", "HEAD"]
    compress                   = true
    response_headers_policy_id = aws_cloudfront_response_headers_policy.security.id
    
    forwarded_values {
      query_string = true
      headers      = ["Authorization", "Content-Type", "Origin", "Accept"]
      cookies {
        forward = "all"
      }
    }

    min_ttl     = 0
    default_ttl = 0 # No caching for API
    max_ttl     = 0
  }

  # ── /health → API Lambda (for monitoring) ─────────────────
  ordered_cache_behavior {
    path_pattern               = "/health"
    target_origin_id           = "api"
    viewer_protocol_policy     = "redirect-to-https"
    allowed_methods            = ["GET", "HEAD"]
    cached_methods             = ["GET", "HEAD"]
    response_headers_policy_id = aws_cloudfront_response_headers_policy.security.id
    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    min_ttl     = 0
    default_ttl = 10
    max_ttl     = 30
  }

  # ── Static assets (/_next/static/*) — aggressive caching ──
  ordered_cache_behavior {
    path_pattern               = "/_next/static/*"
    target_origin_id           = "frontend"
    viewer_protocol_policy     = "redirect-to-https"
    allowed_methods            = ["GET", "HEAD"]
    cached_methods             = ["GET", "HEAD"]
    compress                   = true
    response_headers_policy_id = aws_cloudfront_response_headers_policy.security.id
    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    min_ttl     = 86400    # 1 day
    default_ttl = 2592000  # 30 days (hashed filenames)
    max_ttl     = 31536000 # 1 year
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true # *.cloudfront.net SSL (free)
    # For custom domain:
    # acm_certificate_arn      = var.acm_cert_arn
    # ssl_support_method       = "sni-only"
    # minimum_protocol_version = "TLSv1.2_2021"
  }

  tags = { Name = "${var.project}-${var.environment}" }
}

# ── Security Headers Policy ──────────────────────────────────
# Applied to all responses via CloudFront (OWASP best practices).
resource "aws_cloudfront_response_headers_policy" "security" {
  name = "${var.project}-${var.environment}-security-headers"

  security_headers_config {
    content_type_options {
      override = true # X-Content-Type-Options: nosniff
    }
    frame_options {
      frame_option = "SAMEORIGIN" # X-Frame-Options: SAMEORIGIN
      override     = true
    }
    xss_protection {
      mode_block = true # X-XSS-Protection: 1; mode=block
      protection = true
      override   = true
    }
    strict_transport_security {
      access_control_max_age_sec = 31536000 # 1 year HSTS
      include_subdomains         = true
      override                   = true
    }
    referrer_policy {
      referrer_policy = "strict-origin-when-cross-origin"
      override        = true
    }
    content_security_policy {
      content_security_policy = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' blob:; worker-src 'self' blob:; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob: https:; font-src 'self' https://fonts.gstatic.com; connect-src 'self' https:"
      override                = true
    }
  }
}
