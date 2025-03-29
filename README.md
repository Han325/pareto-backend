# Pareto Life Planner Backend

A FastAPI backend for the Pareto Life Planner application, which helps users balance multiple life goals using Pareto optimization techniques.

## Features

- Task management with durations, categories, and dependencies
- Objective definition and tracking in multiple life categories
- Schedule generation with multiple strategies
- Pareto optimization to find schedules that balance competing objectives

## Quick Start

### Development Setup

```bash
# Create a virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application (with hot reload)
cd backend
python main.py
```

The API will be available at http://localhost:8000

### API Documentation

When the server is running, you can access:
- API documentation at http://localhost:8000/docs
- Alternative documentation at http://localhost:8000/redoc

### Testing

To run the unit tests:

```bash
# Activate virtual environment
source venv/bin/activate

# Run core functionality tests
python -m backend.tests.test_core

# Run API integration tests (with server running)
python backend/tests/test_api.py

# Run tests and start server in one command
./test_server.sh
```

## Deployment Options

### Render Deployment (Recommended)

This repository includes a `render.yaml` file for easy deployment to [Render](https://render.com).

1. Sign up for a free Render account
2. Connect your GitHub repository
3. Create a new Web Service, selecting the repository
4. Render will automatically detect the `render.yaml` configuration
5. Click "Apply" to deploy

### Docker Container

```bash
# Build the Docker image
docker build -t pareto-backend .

# Run the container
docker run -d -p 8000:8000 --name pareto pareto-backend
```

## API Endpoints

Main resource endpoints:

- `/tasks` - Create, read, update and delete tasks
- `/objectives` - Manage life goals and objectives
- `/schedules` - Generate and manage schedules

## Architecture

The application follows a layered architecture:

- `models/` - Database models and Pydantic schemas
- `api/` - API routes and controllers 
- `services/` - Business logic layer
- `core/` - Algorithmic implementations (scheduling, Pareto optimization)
- `utils/` - Utility functions and helpers

## License

This project is licensed under the MIT License - see the LICENSE file for details.
