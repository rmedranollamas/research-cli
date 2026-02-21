import argparse
import sys
import os
import asyncio
from .config import DEFAULT_MODEL, ResearchError
from .db import get_task, get_recent_tasks
from .utils import get_console, truncate_query, save_report_to_file, print_report
from .researcher import ResearchAgent


def create_parser():
    script_name = os.path.basename(sys.argv[0])

    # If called via 'think' entry point, default to 'think' subcommand
    # No longer needed as 'think' command is being removed
    # if (
    #     script_name == think
    #     and len(sys.argv) > 1
    #     and sys.argv[1]
    #     not in [run, think, list, show, -h, --help, --version]
    # ):
    #     sys.argv.insert(1, think)

    parser = argparse.ArgumentParser(description=Gemini