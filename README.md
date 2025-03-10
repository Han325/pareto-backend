# Pareto Life Planner Backend

A FastAPI-based backend for a multi-objective life planner using Pareto optimization to help users balance multiple life goals.

## Features

- Task management (create, read, update, delete)
- Objective definition and tracking
- Schedule generation using various strategies
- Pareto optimization for finding the best schedules

## Requirements

- Python 3.8+
- Poetry (recommended) or pip

## Installation

### Using Poetry (recommended)

```bash
# Install Poetry if not already installed
# curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install
```

### Using pip

```bash
# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Running the Application

### Development Server

```bash
cd backend
uvicorn main:app --reload
```

The API will be available at http://localhost:8000

### API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Testing

### Running Unit Tests

```bash
cd backend
pytest
```

## Project Structure

```
backend/
├── app/
│   ├── core/
│   │   ├── pareto.py       # Pareto optimization algorithms
│   │   ├── scheduler.py    # Schedule generation logic
│   │   └── scoring.py      # Objective scoring functions
│   ├── models/
│   │   ├── task.py
│   │   ├── objective.py
│   │   └── schedule.py
│   ├── services/
│   │   ├── task_service.py
│   │   ├── objective_service.py
│   │   └── schedule_service.py
│   ├── api/
│   │   ├── tasks.py
│   │   ├── objectives.py
│   │   └── schedules.py
│   └── utils/
│       ├── auth.py
│       └── validation.py
└── tests/
```

## API Endpoints

### Tasks API

- POST /tasks/ - Create new task
- GET /tasks/ - List all tasks
- GET /tasks/{id} - Get task details
- PUT /tasks/{id} - Update task
- DELETE /tasks/{id} - Delete task

### Objectives API

- POST /objectives/ - Create objective
- GET /objectives/ - List objectives
- PUT /objectives/{id} - Update objective
- DELETE /objectives/{id} - Delete objective

### Schedule API

- POST /schedules/generate - Generate optimal schedules
- GET /schedules/ - List current schedules
- GET /schedules/pareto - Get Pareto-optimal schedules
- PUT /schedules/{id} - Update schedule

## License

MIT