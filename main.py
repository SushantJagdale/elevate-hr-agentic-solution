"""Main Application Entrypoint for Enterprise HR Agentic Virtual Assistant."""

import argparse
import sys
import uvicorn
from app.config import settings
from app.agent.orchestrator import hr_orchestrator


def run_cli_interactive():
    """Run interactive terminal chat loop."""
    print("=" * 70)
    print("🌟 Altostrat Enterprise HR & Workplace Virtual Assistant (ADK)")
    print(f"   Model: {settings.GEMINI_MODEL} | Retrieval: {settings.RETRIEVAL_MODE}")
    print("   Type 'exit' or 'quit' to end session.")
    print("=" * 70)

    session_id = "cli_session_001"
    while True:
        try:
            user_input = input("\n👤 You: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit", "q"]:
                print("\n👋 Goodbye!")
                break

            print("\n🤖 Assistant is thinking & verifying guardrails...")
            result = hr_orchestrator.run_turn(
                session_id=session_id,
                user_prompt=user_input,
            )

            print("\n🤖 Assistant:")
            print(result.get("response", ""))
            
            if result.get("tool_calls"):
                print("\n⚡ Executed Tools:")
                for tc in result["tool_calls"]:
                    print(f"   • {tc['tool_name']} ({tc.get('execution_latency_ms', 0)}ms)")

            if result.get("citations"):
                print("\n📚 Grounded Citations:")
                for c in result["citations"]:
                    print(f"   • {c}")

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error during turn execution: {e}")


def run_single_prompt(prompt: str):
    """Run a single prompt and print the JSON response."""
    result = hr_orchestrator.run_turn(
        session_id="single_turn_001",
        user_prompt=prompt,
    )
    print("\n--- RESPONSE ---")
    print(result.get("response", ""))
    print("\n--- METADATA ---")
    print(f"Status: {result.get('status')} | Verdict: {result.get('verdict')}")
    print(f"Tools: {[t['tool_name'] for t in result.get('tool_calls', [])]}")
    print(f"Attribution Score: {result.get('grounding_score')}")


def run_server(host: str = "0.0.0.0", port: int = 8080):
    """Launch FastAPI Web Server."""
    print(f"🚀 Starting Enterprise HR Assistant Web Server on http://{host}:{port}...")
    uvicorn.run("app.api.server:app", host=host, port=port, reload=False)


def main():
    parser = argparse.ArgumentParser(
        description="Enterprise HR Agentic Virtual Assistant"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # CLI subparser
    subparsers.add_parser("cli", help="Start interactive CLI chat session")

    # Server subparser
    server_parser = subparsers.add_parser("server", help="Launch FastAPI Web UI server")
    server_parser.add_argument("--port", type=int, default=settings.PORT, help="Port to bind")
    server_parser.add_argument("--host", type=str, default=settings.HOST, help="Host to bind")

    # Single run subparser
    run_parser = subparsers.add_parser("run", help="Run a single test prompt")
    run_parser.add_argument("prompt", type=str, help="Prompt string")

    # Tests subparser
    subparsers.add_parser("test", help="Run automated test suite")

    args = parser.parse_args()

    if args.command == "cli":
        run_cli_interactive()
    elif args.command == "server":
        run_server(host=args.host, port=args.port)
    elif args.command == "run":
        run_single_prompt(args.prompt)
    elif args.command == "test":
        import pytest
        sys.exit(pytest.main(["-v", "tests/"]))
    else:
        # Default to interactive CLI if no arg supplied
        run_cli_interactive()


if __name__ == "__main__":
    main()
