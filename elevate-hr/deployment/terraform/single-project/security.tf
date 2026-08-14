# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# --------------------------------------------------------------------
# Google Cloud Armor WAF Security Policy
# --------------------------------------------------------------------
resource "google_compute_security_policy" "waf" {
  name        = "${var.project_name}-waf"
  project     = var.project_id
  description = "Cloud Armor WAF policy for elevate-hr agent service"

  # Rule 1: Prevent SQL Injection (SQLi)
  rule {
    action   = "deny(403)"
    priority = "1000"
    match {
      expr {
        expression = "evaluatePreconfiguredExpr('sqli-v33-stable')"
      }
    }
    description = "Block SQL injection attacks"
  }

  # Rule 2: Prevent Cross-Site Scripting (XSS)
  rule {
    action   = "deny(403)"
    priority = "1001"
    match {
      expr {
        expression = "evaluatePreconfiguredExpr('xss-v33-stable')"
      }
    }
    description = "Block XSS attacks"
  }
  # Default rule: Allow all other traffic
  rule {
    action   = "allow"
    priority = "2147483647"
    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = ["*"]
      }
    }
    description = "default rule"
  }

  depends_on = [google_project_service.services]
}

# --------------------------------------------------------------------
# Global Load Balancer & Identity-Aware Proxy (IAP) Configuration
# --------------------------------------------------------------------

variable "iap_oauth_client_id" {
  type        = string
  description = "OAuth 2.0 Client ID for Identity-Aware Proxy (IAP)"
  default     = "placeholder-client-id"
}

variable "iap_oauth_client_secret" {
  type        = string
  description = "OAuth 2.0 Client Secret for Identity-Aware Proxy (IAP)"
  default     = "placeholder-client-secret"
  sensitive   = true
}

# Serverless NEG pointing to the Cloud Run service
resource "google_compute_region_network_endpoint_group" "run_neg" {
  name                  = "${var.project_name}-neg"
  project               = var.project_id
  region                = var.region
  network_endpoint_type = "SERVERLESS"
  
  cloud_run {
    service = google_cloud_run_v2_service.app.name
  }
}

# Backend Service for Load Balancer with IAP enabled
resource "google_compute_backend_service" "run_backend" {
  name        = "${var.project_name}-backend"
  project     = var.project_id
  port_name   = "http"
  protocol    = "HTTPS"
  timeout_sec = 30

  backend {
    group = google_compute_region_network_endpoint_group.run_neg.id
  }

  security_policy = google_compute_security_policy.waf.id

  iap {
    enabled              = true
    oauth2_client_id     = var.iap_oauth_client_id
    oauth2_client_secret = var.iap_oauth_client_secret
  }
}

# URL Map to route requests to backend service
resource "google_compute_url_map" "url_map" {
  name            = "${var.project_name}-url-map"
  project         = var.project_id
  default_service = google_compute_backend_service.run_backend.id
}

# HTTP proxy (for redirects or testing, but HTTPS is standard)
resource "google_compute_target_http_proxy" "http_proxy" {
  name    = "${var.project_name}-http-proxy"
  project = var.project_id
  url_map = google_compute_url_map.url_map.id
}

# Global Forwarding Rule to route incoming HTTP traffic
resource "google_compute_global_forwarding_rule" "http_forwarding_rule" {
  name                  = "${var.project_name}-http-rule"
  project               = var.project_id
  target                = google_compute_target_http_proxy.http_proxy.id
  port_range            = "80"
  load_balancing_scheme = "EXTERNAL"
}
