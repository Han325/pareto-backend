from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.models.base import Base, engine, get_db
from app.api import tasks, objectives, schedules

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Pareto Life Planner API",
    description="A multi-objective life planner using Pareto optimization",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
app.include_router(objectives.router, prefix="/objectives", tags=["objectives"])
app.include_router(schedules.router, prefix="/schedules", tags=["schedules"])

@app.get("/")
async def root():
    return {
        "message": "Pareto Life Planner API",
        "docs": "/docs",
        "endpoints": {
            "tasks": "/tasks",
            "objectives": "/objectives",
            "schedules": "/schedules"
        }
    }

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint that also verifies database connection"""
    try:
        # Execute a simple query to verify database connection
        db.execute("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)