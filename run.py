import asyncio
import argparse

from evaluation_utils.runner import Runner
from evaluation_utils.commons import setup_logging, GAME_DATA_DIR
from evaluation_utils.renderer import get_renderer


def main():
    parser = argparse.ArgumentParser(description="Orak Starter Kit Runner")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--session-id", default=None, help="Use existing session id instead of creating a new session")
    parser.add_argument("--local", action="store_true", help="Run in local mode")
    args = parser.parse_args()

    setup_logging(verbose=args.verbose)

    # Initialize the centralized renderer
    renderer = get_renderer()
    renderer.start(
        local=args.local,
        session_id=args.session_id,
        game_data_path=GAME_DATA_DIR
    )

    try:
        runner = Runner(session_id=args.session_id, local=args.local, renderer=renderer)
        asyncio.run(runner.evaluate_all_games())

        # Show final summary with total score
        total_score = sum(runner.scores.values())
        renderer.show_final_summary("all_games", total_score)
    except Exception as e:
        # Mark evaluation as failed
        renderer.complete_evaluation(success=False)
        raise
    finally:
        renderer.stop()


if __name__ == "__main__":
    main()
