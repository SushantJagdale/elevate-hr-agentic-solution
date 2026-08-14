# ADK Agent Evaluation Report

**Date:** August 13, 2026  
**Target Host:** http://127.0.0.1:8000  
**Command Executed:** `agents-cli eval run`  
**Dataset:** [`tests/eval/datasets/elevate-hr-dataset.json`](file:///usr/local/google/home/sushantjagdale/jetski_training1/elevate-hr-agentic-solution/elevate-hr/tests/eval/datasets/elevate-hr-dataset.json)  
**Configuration:** [`tests/eval/eval_config.yaml`](file:///usr/local/google/home/sushantjagdale/jetski_training1/elevate-hr-agentic-solution/elevate-hr/tests/eval/eval_config.yaml)  

---

## 1. Executive Summary

A comprehensive, automated evaluation was performed on the Altostrat Elevate-HR master orchestrator and its specialized worker subagents (`workweek_worker` and `itsm_worker`). The agent was evaluated across 5 representative test cases testing policy Q&A, profile contexts, leave requests, IT ticket tracking, and multi-system equipment procurement.

### Summary Metrics

| Metric | Total Cases | Valid Cases | Fail/Error | Mean Score | Standard Deviation |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Response Quality** (LLM-as-judge, 1-5 scale) | 5 | 5 | 0 | **5.00** | 0.00 |
| **Agent Turn Count** (Turns per case) | 5 | 5 | 0 | **1.00** | 0.00 |

---

## 2. Evaluation Test Cases

| Case ID | Input Prompt | Expected / Reference Behavior |
| :--- | :--- | :--- |
| **`policy_bereavement_leave`** | "What is the company's bereavement leave policy?" | Accurate grounding using `query_policy_knowledge_base` referencing `Leave Policy 2026, Section 4.2` (5 days paid leave). |
| **`workweek_check_balances`** | "How many vacation days do I have remaining in my account?" | Dynamic context resolution of employee ID (`EMP-336`), check balance via `workweek_worker` using `get_employee_balances`, returning `15.0 days`. |
| **`workweek_vacation_request`** | "Please submit a vacation request for next Thursday and Friday." | Request date parameters clarification or request submission using `request_time_off`. |
| **`itsm_vpn_issue`** | "Create an IT ticket because my VPN connection keeps dropping." | Scan existing tickets for duplicates using `list_tickets`, then create a ticket using `create_ticket`. |
| **`procure_home_monitor`** | "I am eligible for a home office monitor. Can you verify my status and order one for me?" | Multi-system flow: check policy -> check employee context -> fetch shipping address via `workweek_worker` -> verify eligibility -> check duplicates -> file IT ticket via `itsm_worker`. |

---

## 3. Results & Verdict Breakdown

### Case 1: `policy_bereavement_leave`
*   **Response Quality:** 5.0 / 5.0
*   **Turns:** 1
*   **Judge's Verdict:** *"The agent provided an accurate, clear, and complete answer that matches the expected ground truth perfectly, including the exact source reference."*

### Case 2: `workweek_check_balances`
*   **Response Quality:** 5.0 / 5.0
*   **Turns:** 1
*   **Judge's Verdict:** *"The model accurately identified that the user has 15.0 vacation days remaining, matching both the tool output and the expected answer."*

### Case 3: `workweek_vacation_request`
*   **Response Quality:** 5.0 / 5.0
*   **Turns:** 1
*   **Judge's Verdict:** *"The assistant appropriately checked the employee's vacation balance first, then clearly and politely asked for the exact calendar dates (YYYY-MM-DD) needed to complete the vacation request accurately."*

### Case 4: `itsm_vpn_issue`
*   **Response Quality:** 5.0 / 5.0
*   **Turns:** 1
*   **Judge's Verdict:** *"The assistant correctly resolved the employee ID, checked existing tickets for duplicates, created an IT ticket with appropriate details for the VPN issue, and returned a complete summary of the created ticket to the user."*

### Case 5: `procure_home_monitor`
*   **Response Quality:** 5.0 / 5.0
*   **Turns:** 1
*   **Judge's Verdict:** *"The assistant correctly verified the policy eligibility, checked for existing tickets to avoid creating duplicates per standard operating procedures, and provided a clear, well-formatted response detailing the policy and the open ticket tracking the request."*

---

## 4. Key Capabilities Verified

1.  **Policy Grounding:** The agent successfully uses the policy tool and cites references correctly.
2.  **Stateless Employee Identity Resolution:** The system dynamically connects to the database to resolve `EMP-336` context seamlessly.
3.  **Deduplication & Safety:** Automatically prevents duplicated ticket creation by listing current tickets before executing write operations on ITSM.
4.  **Orchestration / Worker Transfer:** Orchestrates subagents cleanly by transferring execution context to child worker agents.
