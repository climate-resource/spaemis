"""
CLI
"""
import dotenv

from spaemis.commands import cli

dotenv.load_dotenv()

if __name__ == "__main__":
    # Run the CLI tool
    cli()
