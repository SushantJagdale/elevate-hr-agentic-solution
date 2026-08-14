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

# Secret for WorkWeek API Token
resource "google_secret_manager_secret" "workweek_token" {
  secret_id = "workweek-api-token"
  project   = var.project_id

  replication {
    auto {}
  }

  depends_on = [google_project_service.services]
}

# Mock version for WorkWeek token
resource "google_secret_manager_secret_version" "workweek_token_version" {
  secret      = google_secret_manager_secret.workweek_token.id
  secret_data = "mock-workweek-token-value"
}

# Secret for ServiceImmediately API Token
resource "google_secret_manager_secret" "serviceimmediately_token" {
  secret_id = "serviceimmediately-api-token"
  project   = var.project_id

  replication {
    auto {}
  }

  depends_on = [google_project_service.services]
}

# Mock version for ServiceImmediately token
resource "google_secret_manager_secret_version" "serviceimmediately_token_version" {
  secret      = google_secret_manager_secret.serviceimmediately_token.id
  secret_data = "mock-serviceimmediately-token-value"
}

# Grant the agent service account permission to read WorkWeek secret
resource "google_secret_manager_secret_iam_member" "workweek_accessor" {
  secret_id = google_secret_manager_secret.workweek_token.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.app_sa.email}"
}

# Grant the agent service account permission to read ServiceImmediately secret
resource "google_secret_manager_secret_iam_member" "serviceimmediately_accessor" {
  secret_id = google_secret_manager_secret.serviceimmediately_token.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.app_sa.email}"
}
