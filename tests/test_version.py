import sys
from unittest.mock import patch
from research_cli.cli import create_parser, VERSION

def test_version_output(capsys):
    parser, _ = create_parser()
    with patch.object(sys, 'argv', ['research', '--version']):
        try:
            parser.parse_args(['--version'])
        except SystemExit:
            pass
    captured = capsys.readouterr()
    expected = f"research-cli {VERSION}"
    assert expected in captured.out or expected in captured.err
