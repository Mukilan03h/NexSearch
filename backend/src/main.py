"""
CLI entry point for the AI Research Assistant.
Supports direct query execution and interactive mode.
"""
import argparse
import sys

from src.agents.orchestrator import ResearchOrchestrator
from src.utils.config import settings
from src.utils.logger import setup_logger

logger = setup_logger(__name__, log_file="logs/research.log")


def main():
    parser = argparse.ArgumentParser(
        description="AI Research Assistant — Fetch, analyze, and summarize academic papers.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m src.main --query "transformer architectures for NLP"
  python -m src.main --query "reinforcement learning" --max-papers 20
  python -m src.main --interactive
        """,
    )
    parser.add_argument(
        "--query", "-q", type=str, help="Research query to investigate"
    )
    parser.add_argument(
        "--max-papers", "-m", type=int, default=None, help="Maximum papers to fetch"
    )
    parser.add_argument(
        "--output", "-o", type=str, default=None, help="Output file path (default: stdout)"
    )
    parser.add_argument(
        "--interactive", "-i", action="store_true", help="Interactive mode: enter queries at prompt"
    )

    args = parser.parse_args()

    if args.interactive:
        interactive_mode()
    elif args.query:
        run_query(args.query, args.max_papers, args.output)
    else:
        parser.print_help()
        sys.exit(1)


def run_query(query: str, max_papers: int = None, output_file: str = None):
    """Execute a single research query."""
    print(f"\n🔬 Researching: '{query}'")
    print("=" * 60)

    try:
        orchestrator = ResearchOrchestrator()
        report = orchestrator.research(query=query, max_papers=max_papers)

        # Output report
        if output_file:
            report.save_markdown(output_file)
            print(f"\n✅ Report saved to: {output_file}")
        else:
            print("\n" + report.markdown_output)

        print(f"\n📊 Summary:")
        print(f"   Papers analyzed: {report.papers_analyzed}")
        print(f"   Themes found: {len(report.themes)}")
        print(f"   Citations: {len(report.citations)}")
        if report.minio_url:
            print(f"   Stored at: {report.minio_url}")

    except Exception as e:
        logger.error(f"Research failed: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")
        sys.exit(1)


def interactive_mode():
    """Interactive REPL for research queries."""
    print("\n🤖 AI Research Assistant — Interactive Mode")
    print("Type a research query, or 'quit' to exit.\n")

    orchestrator = ResearchOrchestrator()

    while True:
        try:
            query = input("🔍 Query: ").strip()
            if not query or query.lower() in ("quit", "exit", "q"):
                print("Goodbye! 👋")
                break

            report = orchestrator.research(query=query)
            print("\n" + report.markdown_output)
            print(f"\n📊 {report.papers_analyzed} papers | {len(report.themes)} themes | {len(report.citations)} citations\n")

        except KeyboardInterrupt:
            print("\nGoodbye! 👋")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")


if __name__ == "__main__":
    main()
