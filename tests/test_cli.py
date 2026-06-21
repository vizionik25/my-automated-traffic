import os
import tempfile
import pytest
from click.testing import CliRunner
from my_automated_traffic.cli import main_cli

def test_cli_add_offer() -> None:
    """Test the add-offer CLI command creates an offer in the database."""
    temp_db_fd, temp_db_path = tempfile.mkstemp()
    os.close(temp_db_fd)
    
    try:
        runner = CliRunner()
        result = runner.invoke(main_cli, [
            "--db-path", temp_db_path,
            "add-offer",
            "--url", "http://offer.com",
            "--desc", "Adult dating hook",
            "--rules", "No spamming",
            "--niche", "dating"
        ])
        assert result.exit_code == 0
        assert "Successfully added offer" in result.output
    finally:
        if os.path.exists(temp_db_path):
            os.unlink(temp_db_path)
