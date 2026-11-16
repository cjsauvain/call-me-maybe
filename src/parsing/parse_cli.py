import argparse


def parse_cli() -> argparse.Namespace:
    """Parse the command line arguments."""
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        "--function-definitions",
        help="JSON file containing function definitions for the LLM",
        type=str,
        default="./data/input/function_definitions.json",
    )
    parser.add_argument(
        "--input",
        help="JSON file containing prompts for the LLM",
        type=str,
        default="./data/input/function_calling_tests.json",
    )
    parser.add_argument(
        "--output",
        help="JSON file containing the LLM outputs",
        type=str,
        default="./data/output/function_calls.json",
    )
    parser.add_argument(
        "--generation-visualization",
        help="Enable visualization of the generation process",
        action="store_true",
        default=False,
    )

    return parser.parse_args()
