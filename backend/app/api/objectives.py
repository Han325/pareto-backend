from typing import List, Dict
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..models.objective import ObjectiveCreate, ObjectiveUpdate, ObjectiveResponse
from ..models.task import TaskCategory
from ..services.objective_service import ObjectiveService
from ..models.base import get_db

router = APIRouter()

@router.post("/", response_model=ObjectiveResponse, status_code=status.HTTP_201_CREATED)
def create_objective(objective: ObjectiveCreate, db: Session = Depends(get_db)):
    """Create a new objective"""
    return ObjectiveService.create_objective(db, objective)

@router.get("/", response_model=List[ObjectiveResponse])
def read_objectives(
    skip: int = 0, 
    limit: int = 100,
    category: TaskCategory = None,
    db: Session = Depends(get_db)
):
    """
    Get all objectives with optional filtering
    
    - **skip**: Number of objectives to skip (pagination)
    - **limit**: Maximum number of objectives to return
    - **category**: Filter by objective category
    """
    if category:
        return ObjectiveService.get_objectives_by_category(db, category)
    else:
        return ObjectiveService.get_objectives(db, skip, limit)

@router.get("/{objective_id}", response_model=ObjectiveResponse)
def read_objective(objective_id: str, db: Session = Depends(get_db)):
    """Get a specific objective by ID"""
    objective = ObjectiveService.get_objective(db, objective_id)
    if objective is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Objective not found"
        )
    return objective

@router.put("/{objective_id}", response_model=ObjectiveResponse)
def update_objective(objective_id: str, objective: ObjectiveUpdate, db: Session = Depends(get_db)):
    """Update an objective"""
    updated_objective = ObjectiveService.update_objective(db, objective_id, objective)
    if updated_objective is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Objective not found"
        )
    return updated_objective

@router.delete("/{objective_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_objective(objective_id: str, db: Session = Depends(get_db)):
    """Delete an objective"""
    success = ObjectiveService.delete_objective(db, objective_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Objective not found"
        )
    return None

@router.put("/{objective_id}/progress", response_model=ObjectiveResponse)
def update_objective_progress(objective_id: str, value: float, db: Session = Depends(get_db)):
    """
    Update the current value of an objective
    
    - **value**: The new current value for the objective
    """
    updated_objective = ObjectiveService.update_objective_progress(db, objective_id, value)
    if updated_objective is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Objective not found"
        )
    return updated_objective

@router.post("/normalize-weights", status_code=status.HTTP_200_OK)
def normalize_objective_weights(db: Session = Depends(get_db)):
    """Normalize all objective weights to sum to 1.0"""
    ObjectiveService.normalize_weights(db)
    return {"message": "Objective weights normalized successfully"}

@router.get("/progress/percentages", response_model=Dict[str, float])
def get_objective_progress_percentages(db: Session = Depends(get_db)):
    """Get progress percentages for all objectives"""
    progress = ObjectiveService.get_progress_percentages(db)
    # Convert UUID keys to strings for JSON serialization
    return {str(obj_id): percent for obj_id, percent in progress.items()}

@router.get("/progress/overall", response_model=float)
def get_overall_progress(db: Session = Depends(get_db)):
    """Get weighted average progress across all objectives"""
    return ObjectiveService.calculate_overall_progress(db)

@router.get("/category/{category}", response_model=List[ObjectiveResponse])
def read_objectives_by_category(category: TaskCategory, db: Session = Depends(get_db)):
    """Get all objectives for a specific category"""
    return ObjectiveService.get_objectives_by_category(db, category)