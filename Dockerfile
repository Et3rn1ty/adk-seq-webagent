# =============================================================================
# MULTI-STAGE DOCKERFILE FOR GOOGLE CLOUD RUN DEPLOYMENT
# =============================================================================
# This Dockerfile creates a containerized version of the multi-agent system
# optimized for Google Cloud Run deployment with security best practices

# =============================================================================
# BASE IMAGE SELECTION
# =============================================================================
# Use Python 3.13 slim image as the base
# - python:3.13-slim: Lightweight Python runtime with minimal system packages
# - 'slim' variant reduces image size and attack surface compared to full Python image
# - Python 3.13 provides the latest features and performance improvements
# - Compatible with Google ADK requirements
FROM python:3.13-slim

# =============================================================================
# WORKING DIRECTORY SETUP
# =============================================================================
# Set the working directory inside the container to /app
# All subsequent commands will be executed relative to this directory
# This is where our application code and dependencies will be installed
WORKDIR /app

# =============================================================================
# UV INSTALLATION
# =============================================================================
# Install uv - an extremely fast Python package installer and resolver
# uv is 10-100x faster than pip and provides better dependency resolution
# Download and install uv using the official installation script
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# =============================================================================
# DEPENDENCY INSTALLATION (OPTIMIZATION LAYER)
# =============================================================================
# Copy dependency files first to leverage Docker layer caching
# This allows Docker to cache the dependency installation step
# If pyproject.toml and uv.lock don't change, this layer won't be rebuilt
COPY pyproject.toml uv.lock ./

# =============================================================================
# SECURITY: NON-ROOT USER CREATION
# =============================================================================
# Create a non-root user for security best practices
# Running containers as root is a security risk - if the container is compromised,
# the attacker would have root access to the container
#
# adduser flags explained:
# --disabled-password: Don't set a password (login via key/token only)
# --gecos "": Skip interactive prompts for user information
# myuser: The username for our application user
RUN adduser --disabled-password --gecos "" myuser && \
    chown -R myuser:myuser /app

# Switch to non-root user for dependency installation
# This ensures the virtual environment is created with correct ownership
USER myuser

# Install Python dependencies using uv as the non-root user
# This ensures the virtual environment is created with correct paths for the container
# --frozen: Use exact versions from uv.lock without updating
# --no-cache: Don't store uv cache to reduce image size
# This installs: google-adk, gitpython, pygithub, python-dotenv, uvicorn, and their dependencies
# uv sync creates a virtual environment at /app/.venv by default
RUN uv sync --frozen --no-cache

# =============================================================================
# APPLICATION CODE DEPLOYMENT
# =============================================================================
# Copy all application files to the container
# This includes:
# - main.py (FastAPI application entry point)
# - agents/ directory (all agent definitions and configurations)
# - tools/ directory (custom tools like file_writer_tool.py)
# - utils/ directory (utilities like file_loader.py)
# - Any other project files
#
# Note: .dockerignore file can be used to exclude unnecessary files
# Files will be owned by root, but myuser has read access
COPY . .

# =============================================================================
# ENVIRONMENT CONFIGURATION
# =============================================================================
# Add the virtual environment bin directory to PATH
# This ensures installed packages (like uvicorn) are accessible
# uv sync creates a venv at /app/.venv, so we need /app/.venv/bin in PATH
ENV PATH="/app/.venv/bin:/home/myuser/.local/bin:$PATH"

# =============================================================================
# CONTAINER STARTUP COMMAND
# =============================================================================
# Define the command that runs when the container starts
# This uses the "exec form" of CMD (JSON array format) which is preferred
# 
# Detailed CMD breakdown:
# 
# ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port $PORT"]
# 
# 1. "sh": Execute the Bourne shell
#    - Uses the system's default shell interpreter
#    - Lightweight and available in all Linux containers
# 
# 2. "-c": Shell flag meaning "execute the following command string"
#    - Tells sh to run the command that follows as a single string
#    - Allows environment variable expansion (like $PORT)
#    - Without -c, sh would try to read from stdin or a file
# 
# 3. "uvicorn main:app --host 0.0.0.0 --port $PORT": The actual command string
# 
#    uvicorn: 
#    - Lightning-fast ASGI (Asynchronous Server Gateway Interface) server
#    - Designed for Python async frameworks like FastAPI
#    - Handles HTTP requests and WebSocket connections efficiently
#    - Production-ready server with automatic worker management
# 
#    main:app:
#    - Module:object notation for importing the FastAPI application
#    - "main" = the Python file (main.py) containing our FastAPI app
#    - "app" = the variable name of the FastAPI instance in main.py
#    - Equivalent to: from main import app
# 
#    --host 0.0.0.0:
#    - Bind to all available network interfaces
#    - 0.0.0.0 means "listen on all IP addresses"
#    - Required for Cloud Run: containers must accept traffic from any source
#    - Default would be 127.0.0.1 (localhost only), which Cloud Run can't reach
# 
#    --port $PORT:
#    - Use the PORT environment variable for the listening port
#    - Cloud Run automatically sets PORT (usually 8080)
#    - $PORT expands to the actual port number at runtime
#    - The application MUST listen on this specific port to receive traffic
# 
# Why use sh -c instead of direct uvicorn?
# - Allows environment variable expansion ($PORT)
# - Provides shell features if needed (pipes, redirects, etc.)
# - More flexible for complex startup commands
# 
# Alternative approaches:
# - Direct: CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
# - Script: CMD ["./start.sh"] (with startup script)
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port $PORT"]

# =============================================================================
