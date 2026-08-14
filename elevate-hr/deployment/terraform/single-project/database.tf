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

# Firestore Database in Native Mode (for RAG index and session states)
resource "google_firestore_database" "database" {
  project                     = var.project_id
  name                        = "(default)"
  location_id                 = "us-central1"
  type                        = "FIRESTORE_NATIVE"
  concurrency_mode            = "OPTIMISTIC"
  app_engine_integration_mode = "DISABLED"

  depends_on = [
    google_project_service.services
  ]
}

import {
  id = "projects/migration-demo-429608/databases/(default)"
  to = google_firestore_database.database
}
