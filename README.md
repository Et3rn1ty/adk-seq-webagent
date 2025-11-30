# AI Website Builder

An intelligent website builder powered by Google's ADK (Agent Development Kit) that automatically generates production-ready websites from natural language descriptions.

## Overview

This project uses a sequential multi-agent system to transform user ideas into complete, functional websites. The system conducts research, writes specifications, creates designs, and generates clean, responsive code - all automatically.

## Architecture

The system uses six specialized agents in sequence:

1. **Question Generator Agent** - Generates targeted research questions based on user input
2. **Parallel Research Agent** - Conducts comprehensive research to gather necessary information
3. **Query Generator Agent** - Refines queries for better research outcomes
4. **Requirements Writer Agent** - Translates research and user input into detailed functional requirements
5. **Designer Agent** - Acts as a Frontend Architect/UI-UX Specialist, creating text-based mockups and design systems with precise specifications (colors, typography, components, layouts)
6. **Code Writer Agent** - Implements designs as production-ready HTML5, CSS, and JavaScript

## Tools

- **File Writer Tool** - Saves generated code to the filesystem
- **Git Operations Tool** - Manages version control
- **GitHub Operations Tool** - Handles GitHub repository operations

## How It Works

1. User provides a website concept or description
2. Agents sequentially process the input through research, requirements gathering, design, and implementation
3. Each agent outputs structured data consumed by the next agent in the pipeline
4. Final output: Production-ready, responsive, accessible website code

## Tech Stack

- **Google ADK** (Agent Development Kit) - Multi-agent orchestration
- **Gemini 2.0 Flash & 2.5 Flash** - LLM models powering the agents
- **Python 3.13+** - Runtime environment
- **GitPython** - Git integration
- **PyGithub** - GitHub API integration

## Installation

```bash
# Install dependencies using uv
uv sync

# Or using pip
pip install -e .
```

## Development

```bash
# Install development dependencies
uv sync --extra dev

# Run tests
pytest
```

## Output

Generated website files are saved to the filesystem with proper structure and organization.