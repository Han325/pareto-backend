from typing import List, Dict, Any
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session

from ..models.schedule import Schedule, ScheduleCreate, ScheduleUpdate, ScheduleResponse, ParetoScheduleResponse
from ..models.constraints import TimeConstraints
from ..services.schedule_service import ScheduleService
from ..models.base import get_db

router = APIRouter()

@router.post("/", response_model=ScheduleResponse, status_code=status.HTTP_201_CREATED)
def create_schedule(schedule: ScheduleCreate, db: Session = Depends(get_db)):
    """Create a new schedule"""
    return ScheduleService.create_schedule(db, schedule)

@router.get("/", response_model=List[ScheduleResponse])
def read_schedules(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Get all schedules with pagination
    
    - **skip**: Number of schedules to skip (pagination)
    - **limit**: Maximum number of schedules to return
    """
    return ScheduleService.get_schedules(db, skip, limit)

@router.get("/{schedule_id}", response_model=ScheduleResponse)
def read_schedule(schedule_id: uuid.UUID, db: Session = Depends(get_db)):
    """Get a specific schedule by ID"""
    schedule = ScheduleService.get_schedule(db, schedule_id)
    if schedule is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found"
        )
    return schedule

@router.put("/{schedule_id}", response_model=ScheduleResponse)
def update_schedule(schedule_id: uuid.UUID, schedule: ScheduleUpdate, db: Session = Depends(get_db)):
    """Update a schedule"""
    updated_schedule = ScheduleService.update_schedule(db, schedule_id, schedule)
    if updated_schedule is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found"
        )
    return updated_schedule

@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_schedule(schedule_id: uuid.UUID, db: Session = Depends(get_db)):
    """Delete a schedule"""
    success = ScheduleService.delete_schedule(db, schedule_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found"
        )
    return None

@router.post("/generate", response_model=List[ScheduleResponse])
def generate_schedules(
    constraints: TimeConstraints,
    days: int = Body(7, ge=1, le=30),
    db: Session = Depends(get_db)
):
    """
    Generate feasible schedules based on tasks and objectives
    
    - **constraints**: Time and resource constraints to respect
    - **days**: Number of days to schedule for (default: 7)
    """
    return ScheduleService.generate_schedules(db, constraints, days)

@router.get("/pareto", response_model=List[ScheduleResponse])
def get_pareto_optimal_schedules(db: Session = Depends(get_db)):
    """Get Pareto-optimal schedules"""
    return ScheduleService.get_pareto_optimal_schedules(db)

@router.post("/{schedule_id}/check-feasibility", response_model=bool)
def check_schedule_feasibility(
    schedule_id: uuid.UUID,
    constraints: TimeConstraints,
    db: Session = Depends(get_db)
):
    """
    Check if a schedule is feasible given constraints
    
    - **schedule_id**: ID of the schedule to check
    - **constraints**: Time and resource constraints to validate against
    """
    schedule = ScheduleService.get_schedule(db, schedule_id)
    if schedule is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found"
        )
    
    return ScheduleService.check_schedule_feasibility(db, schedule_id, constraints)