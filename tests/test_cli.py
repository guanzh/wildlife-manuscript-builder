from wmb import __version__
from wmb.cli import main


def test_cli_help_surface(capsys):
    assert main(["--help"]) == 0
    assert "Wildlife Manuscript Builder" in capsys.readouterr().out


def test_cli_version_surface(capsys):
    assert main(["--version"]) == 0
    assert __version__ in capsys.readouterr().out
