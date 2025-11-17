"""Run the FastAPI server"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import uvicorn
from config import Config


def main():
    """Run the API server"""
    print("=" * 60)
    print("Starting RAG Search API Server")
    print("=" * 60)

    try:
        Config.validate()
    except ValueError as e:
        print(f"\n✗ Configuration error: {e}")
        print("\nPlease check your .env file.")
        return

    print(f"\nServer will run at: http://{Config.API_HOST}:{Config.API_PORT}")
    print("\nAvailable endpoints:")
    print(f"  - http://localhost:{Config.API_PORT}/")
    print(f"  - http://localhost:{Config.API_PORT}/health")
    print(f"  - http://localhost:{Config.API_PORT}/search")
    print(f"  - http://localhost:{Config.API_PORT}/chat")
    print(f"  - http://localhost:{Config.API_PORT}/docs (API documentation)")
    print("\n" + "=" * 60)

    uvicorn.run(
        "src.api.search_api:app",
        host=Config.API_HOST,
        port=Config.API_PORT,
        reload=True
    )


if __name__ == "__main__":
    main()
