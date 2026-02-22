import sys
from unittest.mock import patch
from research_cli.cli import create_parser

def test_version_output(capsys):
    parser, _ = create_parser()
    with patch.object(sys, 'argv', ['research', '--version']):
        try:
            parser.parse_args(['--version'])
        except SystemExit:
            pass
    captured = capsys.readouterr()
    assert "research-cli 0.1.45" in captured.out or "research-cli 0.1.45" in captured.err
