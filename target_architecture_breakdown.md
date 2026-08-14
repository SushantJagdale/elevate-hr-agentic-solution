# 🏛️ Enterprise HR Virtual Assistant - Target Architecture Specification & Diagram Breakdown

> **Slide Deck & Technical Reference Guide**
> This document provides an executive summary and deep-dive architecture diagrams for each component of the production system on Google Cloud Platform (GCP).

---

## 📌 Section 1: Executive Overview & High-Level Architecture

### 1.1 Overview Slide: End-to-End Enterprise Architecture

The target architecture is a serverless, multi-agent enterprise HR assistant deployed on GCP. It combines WAF security, serverless container hosting on Cloud Run, Google Agent Development Kit (ADK) orchestration, dual-tier persistence (Firebase Firestore & Memorystore Redis), and enterprise tool connectors (WorkWeek HCM & ServiceImmediately ITSM).

```mermaid
flowchart TD
    %% Ingress & Security Boundary
    subgraph IngressSecurity ["1. Ingress & Security Layer"]
        UserBrowser["👤 User Browser / Mobile App"]
        CloudArmor["🛡️ Google Cloud Armor WAF\n(DDoS Protection, OWASP Top 10)"]
        IAP["🔑 Cloud Identity / IAP\n(OIDC SSO & Identity Propagation)"]
    end

    %% Application Layer
    subgraph ApplicationLayer ["2. Cloud Run Application Layer"]
        CloudRunUI["💻 Cloud Run: Frontend SPA\n(FastAPI + Tailwind CSS)"]
        
        subgraph ADKCore ["Google ADK Multi-Agent Core"]
            Orchestrator["🧠 Central Orchestrator Agent\n(root_agent)"]
            WorkWeekAgent["💼 WorkWeek Sub-Agent\n(workweek_agent)"]
            ServiceNowAgent["🎫 ServiceImmediately Sub-Agent\n(service_immediately_agent)"]
            PolicyAgent["📜 Policy RAG Agent\n(search_hr_policies)"]
        end

        Guardrails["🛡️ Guardrail Engine\n(SPII Redaction & Policy Rules)"]
    end

    %% Persistence Layer
    subgraph DataLayer ["3. Database & Memory Persistence"]
        RedisMemory[("⚡ Memorystore for Redis\n(Context Cache & Rate Limiting)")]
        FirestoreDB[("🔥 Firebase Firestore\n(Session History & Vector Search)")]
    end

    %% Integration Layer
    subgraph Integrations ["4. Integration Layer (MCP)"]
        SecretMgr["🔑 Secret Manager\n(MCP Tokens & Service Keys)"]
        WorkWeekMCP["💼 WorkWeek MCP Server\n(HCM & Leave Management)"]
        ServiceNowMCP["🎫 ServiceImmediately MCP\n(ITSM & HRSD Tickets)"]
    end

    %% Observability Layer
    subgraph Observability ["5. Audit & Observability"]
        CloudDLP["🔍 Cloud DLP Filter\n(SPII Redaction)"]
        CloudLogging["📊 Cloud Logging & Cloud Trace\n(Distributed Tracing)"]
        BigQueryVault[("🏛️ BigQuery WORM Audit Vault\n(Compliance Logs)")]
    end

    %% Data Connections
    UserBrowser -->|HTTPS / TLS 1.3| CloudArmor
    CloudArmor --> IAP
    IAP --> CloudRunUI
    CloudRunUI -->|REST / API| Orchestrator

    Orchestrator -->|Delegates HCM| WorkWeekAgent
    Orchestrator -->|Delegates ITSM| ServiceNowAgent
    Orchestrator -->|Queries Policies| PolicyAgent

    Orchestrator --> Guardrails
    WorkWeekAgent --> Guardrails
    ServiceNowAgent --> Guardrails

    Orchestrator <-->|Sub-ms Session State| RedisMemory
    Orchestrator <-->|Durable History & Vectors| FirestoreDB

    SecretMgr -.->|Fetch Token| WorkWeekAgent
    SecretMgr -.->|Fetch Token| ServiceNowAgent

    WorkWeekAgent -->|HTTP / SSE MCP| WorkWeekMCP
    ServiceNowAgent -->|HTTP / SSE MCP| ServiceNowMCP

    Guardrails --> CloudDLP
    CloudDLP --> CloudLogging
    CloudDLP --> BigQueryVault
```

### 1.2 Subsystem Summary Matrix

| Subsystem | GCP Service | Enterprise Functionality | SLA / Target |
| :--- | :--- | :--- | :--- |
| **Ingress & WAF** | Cloud Armor + IAP | Web application firewall, DDoS protection, OIDC SSO authentication | 99.99% Availability |
| **Frontend UI** | Cloud Run | Hosts responsive HTML5/Tailwind SPA with real-time telemetry drawer | < 50ms TTFB |
| **Multi-Agent Core** | Cloud Run (Google ADK) | Central Orchestrator delegating to specialized domain sub-agents | < 1.5s Response Latency |
| **Session Cache** | Memorystore for Redis | Sub-millisecond conversation state caching and token rate-limiting | < 2ms Latency |
| **Database & Vectors** | Firebase Firestore | Durable chat history, user profiles, and vector similarity search | 99.999% Availability |
| **Tool Connectors** | Remote MCP Servers | Standardized Model Context Protocol toolsets over Private Service Connect | High Resiliency |
| **Observability** | Cloud Logging & Trace | Centralized logging, distributed tracing, and Cloud DLP SPII filtering | Immutable Audit |

---

## 🛡️ Section 2: Ingress, WAF & Security Layer Deep-Dive

### 2.1 Slide Topic: Ingress Architecture & Zero-Trust Boundary

The Security Layer guarantees that all incoming HTTP traffic is filtered through Cloud Armor WAF rules before hitting identity-aware authentication proxy services.

```mermaid
sequenceDiagram
    autonumber
    actor Client as 👤 User Browser / App
    participant WAF as 🛡️ Cloud Armor WAF
    participant IAP as 🔑 Identity-Aware Proxy (Cloud Identity)
    participant UI as 💻 Cloud Run Frontend
    participant Core as 🧠 Cloud Run ADK Agent Core

    Client->>WAF: HTTPS Request (TLS 1.3)
    Note over WAF: 1. OWASP Top 10 Rules Check<br/>2. Rate Limit & IP Geofencing
    alt Malicious Request / SQLi / XSS
        WAF-->>Client: 403 Forbidden (Blocked by WAF)
    else Clean Traffic
        WAF->>IAP: Forward Validated Traffic
    end

    Note over IAP: Authenticate Session via OIDC / Google Workspace SSO
    alt Unauthenticated
        IAP-->>Client: Redirect to OAuth2 Login
    else Valid Token
        IAP->>UI: Forward Request + Authenticated User Claims (X-Goog-Authenticated-User-Email)
    end

    UI->>Core: Forward User Prompt + User Context Header
    Core-->>UI: Agent Response Payload
    UI-->>Client: Rendered UI & Response
```

### 2.2 Security Controls Summary
* **Cloud Armor WAF**: Filters layer 7 attacks, cross-site scripting (XSS), SQL injection (SQLi), and automated bot traffic.
* **Identity-Aware Proxy (IAP)**: Enforces Zero-Trust access based on user identity and context without requiring a traditional VPN.
* **Header Propagation**: Securely injects validated user identities (`X-Goog-Authenticated-User-Email`, `X-Goog-Authenticated-User-Id`) into the ADK runtime.

---

## 🤖 Section 3: Multi-Agent ADK Core & Guardrails Engine Deep-Dive

### 3.1 Slide Topic: Agentic Routing & Deterministic Guardrails

The application core utilizes the **Google Agent Development Kit (ADK)** to establish a hierarchical multi-agent structure. The Central Orchestrator evaluates user intent and routes requests to specialized domain sub-agents or policy RAG functions.

```mermaid
flowchart TD
    subgraph RequestContext ["User Input & Context"]
        Prompt["Incoming User Prompt"]
    end

    subgraph GuardrailPre ["Pre-Execution Guardrail Engine"]
        SPIICheck{"🔍 SPII Redaction Check\n(SSN / Password / Credit Card)"}
        RedactAction["🚩 Redact Sensitive Data\nSet Context Warning"]
    end

    subgraph AgentRouter ["Google ADK Orchestration Engine"]
        OrchestratorAgent["🧠 Central Orchestrator Agent (root_agent)\nModel: Gemini 2.5 Flash"]
        IntentRouter{"🔀 Intent Router"}
    end

    subgraph SpecializedSubAgents ["Domain Sub-Agents"]
        WWSubAgent["💼 WorkWeek HCM Sub-Agent\n• Leave Balances\n• Time Off Submissions\n• Address Updates"]
        SISubAgent["🎫 ServiceImmediately Sub-Agent\n• IT Hardware Tickets\n• HRSD Inquiries\n• Ticket Status"]
        PolicySubAgent["📜 Policy RAG Engine\n• Handbook Search\n• Bereavement Policy\n• Parental Leave Rules"]
    end

    subgraph GuardrailPost ["Post-Execution Guardrail Engine"]
        OutputCheck{"🛡️ Output Safety & Citation Check"}
    end

    Prompt --> SPIICheck
    SPIICheck -- SPII Detected --> RedactAction --> OrchestratorAgent
    SPIICheck -- Clean --> OrchestratorAgent

    OrchestratorAgent --> IntentRouter
    IntentRouter -- WorkWeek / PTO --> WWSubAgent
    IntentRouter -- ServiceNow / IT --> SISubAgent
    IntentRouter -- Policy Question --> PolicySubAgent

    WWSubAgent --> OutputCheck
    SISubAgent --> OutputCheck
    PolicySubAgent --> OutputCheck

    OutputCheck --> FinalOutput["💬 Formatted Response + Citations + Telemetry"]
```

### 3.2 Key Multi-Agent Capabilities
* **Central Orchestrator (`root_agent`)**: Analyzes intent and delegates to sub-agents via ADK `sub_agents` mechanisms.
* **WorkWeek Sub-Agent (`workweek_agent`)**: Manages HCM operations, balance verifications, and profile address changes.
* **ServiceImmediately Sub-Agent (`service_immediately_agent`)**: Manages IT/HRSD ticket lifecycle, automatic assignment routing (e.g. `HR-Tier2-Ops`), and status checks.
* **Pre-Execution Guardrails (`spii_redaction_callback`)**: Guarantees sensitive data is scrubbed before LLM processing.

---

## 💾 Section 4: Database, RAG & Session Persistence Deep-Dive

### 4.1 Slide Topic: Dual-Tier Storage Architecture

To achieve sub-50ms session retrievals while supporting rich vector similarity searches, the architecture pairs **Memorystore for Redis** (fast cache) with **Firebase Firestore** (durable database and vector index).

```mermaid
flowchart LR
    subgraph ADKRuntime ["ADK Agent Runtime (Cloud Run)"]
        AgentSession["Agent Session Manager"]
        RAGRetriever["RAG Retrieval Engine"]
    end

    subgraph FastCache ["Tier 1: High-Speed Cache"]
        Redis[("⚡ Memorystore for Redis\n• Active Session Cache (<2ms)\n• Prompt-Response Cache\n• Rate-Limiting Counters")]
    end

    subgraph DurableStorage ["Tier 2: Durable Database & Vectors"]
        Firestore[("🔥 Firebase Firestore\n• Permanent Chat History\n• User Profiles & Preferences\n• Vector Search (HNSW Index)\n• HR Policy Text Chunks")]
    end

    subgraph IngestionPipeline ["Vector Ingestion Pipeline"]
        DocStorage["📄 GCS Policy Storage"]
        DocAI["📑 Vertex AI DocAI OCR"]
        EmbeddingsAPI["🔤 Embeddings API (text-embedding-004)"]
    end

    AgentSession <-->|Read / Write Fast State| Redis
    AgentSession <-->|Sync Durable Logs| Firestore

    DocStorage --> DocAI --> EmbeddingsAPI -->|768-dim Vectors| Firestore
    RAGRetriever <-->|Vector Similarity Query| Firestore
```

### 4.2 Storage Strategy
* **Memorystore for Redis**: Stores active session state, immediate context turns, and rate-limiting keys with sub-2ms latency.
* **Firebase Firestore**: Stores long-term chat history, user metadata, and policy vector embeddings using native Firestore Vector Search (HNSW index).

---

## 🔌 Section 5: Integration & Remote MCP Layer Deep-Dive

### 5.1 Slide Topic: Model Context Protocol (MCP) Integration Sequence

Integration with downstream enterprise SaaS applications (WorkWeek HCM and ServiceImmediately ITSM) is standardizing on the **Model Context Protocol (MCP)** using Streamable HTTP/SSE transports.

```mermaid
sequenceDiagram
    autonumber
    participant SubAgent as 🤖 Domain Sub-Agent
    participant SecMgr as 🔑 Secret Manager
    participant MCPToolset as 🛠️ ADK MCP Toolset
    participant PSC as 🌐 Private Service Connect (PSC)
    participant ExternalSaaS as 🏢 External SaaS (WorkWeek / ServiceImmediately)

    SubAgent->>SecMgr: Fetch MCP Authentication Token
    SecMgr-->>SubAgent: Return `X-MCP-Token` Secret
    
    SubAgent->>MCPToolset: Execute Tool Action (e.g. `get_personal_info`)
    
    Note over MCPToolset: Inject Headers:<br/>1. X-MCP-Token<br/>2. X-Origin-Agent: HR-Agentic-System<br/>3. X-User-Identity: EMP-94820

    MCPToolset->>PSC: Streamable HTTP / SSE Request
    PSC->>ExternalSaaS: Forward Secure REST/MCP Call
    
    ExternalSaaS-->>PSC: JSON Response Payload
    PSC-->>MCPToolset: Stream SSE Response Event
    MCPToolset-->>SubAgent: Structured Python Dictionary
```

### 5.2 MCP Architectural Benefits
* **Standardized Protocol**: Decouples agent logic from API client implementations.
* **Secret Management**: Credentials are stored in Google Cloud Secret Manager and injected at execution time.
* **Network Isolation**: Encapsulated via GCP Private Service Connect (PSC) to keep API traffic off the public internet.

---

## 📊 Section 6: Observability, Cloud Logging & Audit Telemetry Deep-Dive

### 6.1 Slide Topic: End-to-End Telemetry & Immutable Audit Vault

All prompt transactions, sub-agent handoffs, tool calls, and model outputs are streamed to **Cloud Logging** and **Cloud Trace**, with SPII filtered via **Cloud DLP**, before being archived into a **BigQuery WORM (Write Once Read Many) Audit Vault**.

```mermaid
flowchart TD
    subgraph ExecutionEvents ["Agent Runtime Execution Events"]
        PromptEvt["User Prompt Event"]
        TransferEvt["Agent Handoff Event"]
        ToolEvt["MCP Tool Call & Response"]
        OutputEvt["Final Model Response"]
    end

    subgraph TelemetryPipeline ["Telemetry Processing Pipeline"]
        DLPScanner["🔍 Google Cloud DLP Engine\n(Real-Time SPII Masking & Redaction)"]
        CloudLogging["📊 Google Cloud Logging\n(Centralized Log Streaming)"]
        CloudTrace["⏱️ Google Cloud Trace\n(Per-Turn Latency Tracking)"]
    end

    subgraph LongTermAudit ["Compliance & Analytics Storage"]
        BigQueryVault[("🏛️ BigQuery WORM Audit Vault\n• Immutable Compliance Records\n• Historical Security Analytics\n• Agent Performance Evaluation")]
    end

    ExecutionEvents --> DLPScanner
    DLPScanner --> CloudLogging
    DLPScanner --> CloudTrace
    CloudLogging -->|Log Sink Streaming| BigQueryVault
```

### 6.2 Compliance & Observability Features
* **Cloud DLP Redaction**: Scans all log streams to redact Social Security Numbers (SSNs), passwords, and credit card details before writing to disk.
* **Cloud Trace**: Tracks multi-agent delegation latencies, tool execution times, and LLM generation durations.
* **BigQuery WORM Vault**: Ensures immutable, audit-ready storage for enterprise compliance and security analysis.
