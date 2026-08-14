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

# VPC Network
resource "google_compute_network" "vpc" {
  name                    = "${var.project_name}-vpc"
  project                 = var.project_id
  auto_create_subnetworks = false

  depends_on = [google_project_service.services]
}

# Subnet with Private Google Access enabled
resource "google_compute_subnetwork" "subnet" {
  name                     = "${var.project_name}-subnet"
  project                  = var.project_id
  ip_cidr_range            = "10.0.0.0/24"
  region                   = var.region
  network                  = google_compute_network.vpc.id
  private_ip_google_access = true
}

# --------------------------------------------------------------------
# Private Service Connect (PSC) to Downstream Systems (Placeholders)
# --------------------------------------------------------------------

variable "workweek_service_attachment" {
  type        = string
  description = "Service Attachment URI for WorkWeek HCM"
  default     = "projects/migration-demo-429608/regions/us-east1/serviceAttachments/mock-workweek-sa"
}

variable "serviceimmediately_service_attachment" {
  type        = string
  description = "Service Attachment URI for ServiceImmediately ITSM"
  default     = "projects/migration-demo-429608/regions/us-east1/serviceAttachments/mock-serviceimmediately-sa"
}

# IP Address for WorkWeek PSC Endpoint
resource "google_compute_address" "workweek_psc_ip" {
  name         = "workweek-psc-ip"
  project      = var.project_id
  region       = var.region
  subnetwork   = google_compute_subnetwork.subnet.id
  address_type = "INTERNAL"
  purpose      = "GCE_ENDPOINT"
}

# Forwarding Rule for WorkWeek PSC Endpoint
# resource "google_compute_forwarding_rule" "workweek_psc" {
#   name                  = "workweek-psc-rule"
#   project               = var.project_id
#   region                = var.region
#   network               = google_compute_network.vpc.id
#   ip_address            = google_compute_address.workweek_psc_ip.id
#   target                = var.workweek_service_attachment
#   load_balancing_scheme = "" # Required for PSC
# }

# IP Address for ServiceImmediately PSC Endpoint
resource "google_compute_address" "serviceimmediately_psc_ip" {
  name         = "serviceimmediately-psc-ip"
  project      = var.project_id
  region       = var.region
  subnetwork   = google_compute_subnetwork.subnet.id
  address_type = "INTERNAL"
  purpose      = "GCE_ENDPOINT"
}

# Forwarding Rule for ServiceImmediately PSC Endpoint
# resource "google_compute_forwarding_rule" "serviceimmediately_psc" {
#   name                  = "serviceimmediately-psc-rule"
#   project               = var.project_id
#   region                = var.region
#   network               = google_compute_network.vpc.id
#   ip_address            = google_compute_address.serviceimmediately_psc_ip.id
#   target                = var.serviceimmediately_service_attachment
#   load_balancing_scheme = "" # Required for PSC
# }
