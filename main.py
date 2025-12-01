"""
FastAPI Application Entry Point for Google Cloud Run Deployment

This file serves as the main entry point for deploying the multi-agent system to Google Cloud Run.
It uses the Agent Development Kit (ADK) to create a FastAPI application that can serve both
a web interface and REST API endpoints for interacting with the multi-agent system.

Key Components:
1. FastAPI app creation using ADK's get_fast_api_app()
2. Configuration for Cloud Run deployment
3. Session management setup
4. CORS configuration for web access
5. Web interface enablement
"""

import os
import uvicorn
from google.adk.cli.fast_api import get_fast_api_app

# =============================================================================
# DIRECTORY AND PATH CONFIGURATION
# =============================================================================

# Get the absolute path to the directory where main.py is located
# This ensures we can find our agents directory regardless of where the script is run from
# os.path.abspath() converts relative paths to absolute paths
# os.path.dirname() gets the directory containing the file
AGENT_DIR = os.path.dirname(os.path.abspath(__file__))

# =============================================================================
# SESSION MANAGEMENT CONFIGURATION
# =============================================================================

# Configure the session service URI for storing conversation sessions
# SQLite is used here for simplicity - it creates a local database file
# In production, you might want to use a more robust database like PostgreSQL
# The "./sessions.db" path is relative to the container's working directory
SESSION_SERVICE_URI = "sqlite:///./sessions.db"

# =============================================================================
# CORS (Cross-Origin Resource Sharing) CONFIGURATION
# =============================================================================

# Define allowed origins for CORS to enable web browser access
# This is crucial for the web interface to work properly
# - "http://localhost": Allows local development access
# - "http://localhost:8080": Common alternative local port
# - "*": Allows access from any origin (use with caution in production)
ALLOWED_ORIGINS = ["http://localhost", "http://localhost:8080", "*"]

# =============================================================================
# WEB INTERFACE CONFIGURATION
# =============================================================================

# Enable the web interface for browser-based interaction with agents
# When True: Provides a user-friendly web UI for testing and interaction
# When False: Only provides REST API endpoints (headless mode)
# For Cloud Run deployment, we want the web interface enabled
SERVE_WEB_INTERFACE = True

# =============================================================================
# FASTAPI APPLICATION CREATION
# =============================================================================

# Create the FastAPI application instance using ADK's built-in function
# This function automatically sets up all the necessary routes and middleware
# for serving ADK agents through a web interface and REST API
app = get_fast_api_app(
    # Path to the directory containing all agent folders
    # Each subdirectory in 'agents/' represents a different agent
    # The ADK will automatically discover and load all agents from this directory
    agents_dir=os.path.join(AGENT_DIR, "agents"),
    
    # Database connection string for session persistence
    # Sessions allow maintaining conversation context across multiple requests
    session_service_uri=SESSION_SERVICE_URI,
    
    # CORS configuration to allow web browser access
    # Essential for the web interface to function properly
    allow_origins=ALLOWED_ORIGINS,
    
    # Enable/disable the web interface
    # When enabled, provides HTML pages for agent interaction
    web=SERVE_WEB_INTERFACE,
)

# =============================================================================
# CUSTOM ROUTE EXTENSIONS (OPTIONAL)
# =============================================================================

# You can add custom FastAPI routes here if needed
# This allows extending the application with additional functionality
# beyond what ADK provides out of the box

# Example custom route:
# @app.get("/health")
# async def health_check():
#     """Health check endpoint for monitoring"""
#     return {"status": "healthy", "service": "website-builder-agent"}

# @app.get("/agents/list")
# async def list_agents():
#     """Custom endpoint to list available agents"""
#     return {"agents": ["root_website_builder", "questions_generator", "questions_researcher"]}

# =============================================================================
# APPLICATION STARTUP CONFIGURATION
# =============================================================================

if __name__ == "__main__":
    """
    Application startup configuration for both local development and Cloud Run deployment
    
    This section handles the server startup with proper configuration for different environments:
    - Local development: Uses default port 8080
    - Cloud Run: Uses the PORT environment variable provided by the platform
    
    Key configurations:
    - host="0.0.0.0": Binds to all network interfaces (required for containers)
    - port: Uses Cloud Run's PORT environment variable or defaults to 8080
    - The uvicorn server handles HTTP requests and forwards them to the FastAPI app
    """
    
    # Cloud Run provides a PORT environment variable that specifies which port to use
    # We use os.environ.get() to read this variable, with 8080 as a fallback
    # This ensures compatibility with both local development and Cloud Run deployment
    port = int(os.environ.get("PORT", 8080))
    
    # Start the uvicorn ASGI server
    # - app: The FastAPI application instance created above
    # - host="0.0.0.0": Listen on all network interfaces (required for Cloud Run)
    # - port: The port number determined above
    uvicorn.run(app, host="0.0.0.0", port=port)
