# Evaluation Datasets

This directory contains evaluation datasets for testing the Elevate-HR agent behavior following the [Google Agents CLI (`agents-cli`)](https://github.com/google/agents-cli) evaluation format.

## Available Datasets

| Dataset File | Type | Description | Cases |
| :--- | :--- | :--- | :--- |
| [`eval-data.json`](file:///Users/gopikasiva/elevate-hr-agentic-solution/elevate-hr/tests/eval/datasets/eval-data.json) | Single-Turn | Primary single-turn benchmark covering Policy Q&A, WorkWeek HCM, ServiceImmediately ITSM, and Multi-System Procurement. | 16 |
| [`eval-multi-turn.json`](file:///Users/gopikasiva/elevate-hr-agentic-solution/elevate-hr/tests/eval/datasets/eval-multi-turn.json) | Multi-Turn | Conversational multi-turn scenarios testing clarification, date correction, follow-up comments, and multi-step workflows. | 6 |
| [`elevate-hr-dataset.json`](file:///Users/gopikasiva/elevate-hr-agentic-solution/elevate-hr/tests/eval/datasets/elevate-hr-dataset.json) | Single-Turn | Enterprise benchmark dataset for Elevate-HR production validation. | 16 |
| [`basic-dataset.json`](file:///Users/gopikasiva/elevate-hr-agentic-solution/elevate-hr/tests/eval/datasets/basic-dataset.json) | Single-Turn | Starter baseline dataset for smoke testing. | 3 |

---

## Running Evaluations with `agents-cli`

### 1. Single-Turn Evaluation
```bash
# Generate traces
agents-cli eval generate --dataset tests/eval/datasets/eval-data.json --output eval_traces/

# Run grading using custom LLM-as-judge rubric
agents-cli eval grade --metrics custom_response_quality --traces eval_traces/
```

### 2. Multi-Turn Evaluation
```bash
# Generate traces for multi-turn scenarios
agents-cli eval generate --dataset tests/eval/datasets/eval-multi-turn.json --output eval_traces_multiturn/

# Run grading
agents-cli eval grade --metrics custom_response_quality --traces eval_traces_multiturn/
```

### 3. Targeting a Deployed Agent
Pass `--url <base_url> --app-name <name>` to test an already running or deployed agent:
```bash
agents-cli eval generate --url https://elevate-hr-xxxx-uc.a.run.app --app-name app --dataset tests/eval/datasets/eval-data.json --output prod_traces/
```

---

## Dataset Format Specification

Each dataset follows the Gemini Enterprise Agent Platform Evaluation format.

### Shape A: Single-Prompt Case
```json
{
  "eval_cases": [
    {
      "eval_case_id": "policy_bereavement_leave",
      "prompt": {
        "role": "user",
        "parts": [{"text": "How many days of bereavement leave am I entitled to take?"}]
      },
      "reference": {
        "response": {
          "role": "model",
          "parts": [{"text": "Employees are eligible for up to 5 days of paid bereavement leave."}]
        }
      }
    }
  ]
}
```

### Shape B: Continued-Conversation Multi-Turn Case ("N+1" Pattern)
Carries prior turns in `agent_data.turns` ending with a user message:
```json
{
  "eval_cases": [
    {
      "eval_case_id": "multiturn_leave_clarification_and_booking",
      "agent_data": {
        "turns": [
          {
            "turn_index": 0,
            "events": [
              {"author": "user",  "content": {"role": "user",  "parts": [{"text": "I'd like to take vacation next week."}]}},
              {"author": "agent", "content": {"role": "model", "parts": [{"text": "What are your specific start and end dates?"}]}},
              {"author": "user",  "content": {"role": "user",  "parts": [{"text": "From 2026-09-01 to 2026-09-04."}]}}
            ]
          }
        ]
      },
      "reference": {
        "response": {
          "role": "model",
          "parts": [{"text": "Your vacation request for 2026-09-01 to 2026-09-04 has been submitted."}]
        }
      }
    }
  ]
}
```

---

## Beyond Generate and Grade

- **Diff Regression Checks:** `agents-cli eval compare BASE_TRACES CANDIDATE_TRACES`
- **Cluster Failure Modes:** `agents-cli eval analyze RESULTS_FILE`
- **Prompt Auto-Tuning:** `agents-cli eval optimize --dataset tests/eval/datasets/eval-data.json`
- **List Available SDK Metrics:** `agents-cli eval metric list`
