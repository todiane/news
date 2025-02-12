import subprocess
import sys
import time
from pathlib import Path

def run_fastapi():
    """Run the FastAPI development server"""
    subprocess.Popen([
        "uvicorn", 
        "main:app", 
        "--reload",
        "--host", "0.0.0.0",
        "--port", "8000"
    ])

def run_tailwind():
    """Run Tailwind CSS in watch mode"""
    subprocess.Popen([
        "tailwindcss",
        "-i", "./static/css/input.css",
        "-o", "./static/css/main.css",
        "--watch"
    ])

def main():
    print("Starting development servers...")
    
    # Ensure required directories exist
    Path("./static/css").mkdir(parents=True, exist_ok=True)
    
    # Create input.css if it doesn't exist
    input_css = Path("./static/css/input.css")
    if not input_css.exists():
        input_css.write_text("""@tailwind base;
@tailwind components;
@tailwind utilities;
""")
    
    # Start both processes
    run_tailwind()
    run_fastapi()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down development servers...")
        sys.exit(0)

if __name__ == "__main__":
    main()