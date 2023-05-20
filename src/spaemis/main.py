"""
CLI
"""
try:
    import dotenv

    dotenv.load_dotenv()
except ImportError:
    pass


from spaemis.commands import cli

if __name__ == "__main__":
    # Run the CLI tool
    cli()
