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

# GCS Bucket for Curated Policy Documents (RAG Source)
resource "google_storage_bucket" "policy_docs_bucket" {
  name                        = "${var.project_id}-${var.project_name}-policies"
  location                    = var.region
  project                     = var.project_id
  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  depends_on = [
    google_project_service.services
  ]
}

# Grant the agent service account read access to policy documents
resource "google_storage_bucket_iam_member" "agent_policy_reader" {
  bucket = google_storage_bucket.policy_docs_bucket.name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.app_sa.email}"
}
