"""
Member Retention - Streamlit App Runner
Launches the Streamlit application for gym membership retention

This script is designed to work both locally and on cloud platforms like Render.
It handles:
- Environment setup
- Optional pre-flight validation
- Supabase authentication table checks
- Streamlit server startup with correct port and headless/cloud-safe settings
"""

import subprocess
import sys
import os
from pathlib import Path
import dotenv


def run_setup_validation():
    """
    Run optional setup validation.
    Uses `utils/setup.py` to check project dependencies and environment.
    Installs missing dependencies if needed.
    """
    print("Running pre-flight checks...")
    print("-" * 60)

    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root / "utils"))

    try:
        from setup import SetupValidator

        validator = SetupValidator(project_root)
        success = validator.run_all_checks(install_deps=True, force_install=False)

        if not success:
            print("\n" + "=" * 60)
            print("⚠️  Setup validation found issues, but continuing anyway...")
            print("=" * 60)
            print()
        return success

    except ImportError as e:
        print(f"⚠️  Could not import setup validator: {e}")
        print("   Continuing without validation...")
        print()
        return False
    except Exception as e:
        print(f"⚠️  Error during setup validation: {e}")
        print("   Continuing anyway...")
        print()
        return False


def check_auth_setup():
    """
    Check if the Supabase authentication table exists.
    If missing, optionally run a setup script to create it.
    """
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    supabase_schema = os.getenv("SUPABASE_SCHEMA", "public")
    auth_table = os.getenv("AUTH_TABLE", "auth")

    if not supabase_url or not supabase_key:
        print("⚠️  Warning: Supabase credentials not found in .env")
        print("    Authentication will not work without setup.")
        print()
        return False

    try:
        from supabase import create_client

        client = create_client(supabase_url, supabase_key)
        # Try querying the table
        result = client.schema(supabase_schema).table(auth_table).select("username").limit(1).execute()
        print(f"✓ Auth table found: {supabase_schema}.{auth_table}")
        return True

    except Exception as e:
        print(f"⚠️  Auth table not found: {supabase_schema}.{auth_table}")
        print()
        print("Would you like to create it now? (y/n): ", end="")
        response = input().strip().lower()

        if response == 'y':
            print()
            print("Running setup script...")
            setup_script = Path(__file__).parent / "src" / "setup_auth.py"
            result = subprocess.run([sys.executable, str(setup_script)])
            return result.returncode == 0
        else:
            print()
            print("⚠️  You can create it later by running:")
            print("    python src/setup_auth.py")
            print()
            return False


def clear_streamlit_cache():
    """
    Clear Streamlit cache to prevent stale data or config conflicts.
    """
    try:
        cache_path = Path.home() / ".streamlit" / "cache"
        if cache_path.exists():
            import shutil
            shutil.rmtree(cache_path, ignore_errors=True)
    except Exception:
        pass  # silently ignore failures


def main():
    """
    Main function
    """
    from dotenv import load_dotenv
    load_dotenv()  # Load environment variables from .env file

    app_path = Path(__file__).parent / "app" / "app.py"
    if not app_path.exists():
        print(f"Error: Streamlit app not found at {app_path}")
        sys.exit(1)

    print("=" * 60)
    print("Anticipa - Supply Chain Optimization")
    print("=" * 60)
    print()

    # Detect if running in cloud (Render) or local
    is_cloud = os.getenv("RENDER") or os.getenv("STREAMLIT_SHARING") or os.getenv("PORT")

    if not is_cloud:
        # Local environment: run validations and auth checks
        clear_streamlit_cache()
        run_setup_validation()
        check_auth_setup()
    else:
        print("🌐 Cloud deployment detected - skipping interactive setup")

    print()
    print("Starting Streamlit server...")
    print(f"App location: {app_path}")
    print("-" * 60)

    # Prepare environment for subprocess
    env = os.environ.copy()
    env['PYTHONDONTWRITEBYTECODE'] = '1'

    # Get port from environment (Render sets this dynamically)
    port = os.getenv("PORT", "8501")  # fallback for local development

    # Launch Streamlit
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run",
            str(app_path),
            "--server.port", port,
            "--server.address", "0.0.0.0",
            "--server.headless", "true",
            "--server.enableCORS", "false",
            "--server.enableXsrfProtection", "false"
        ], check=True, env=env)
    except subprocess.CalledProcessError as e:
        print("\n" + "="*60)
        print("❌ Streamlit failed to start")
        print("="*60)
        print(f"Error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nShutting down Streamlit app...")
        sys.exit(0)


if __name__ == "__main__":
    main()
