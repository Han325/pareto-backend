from typing import List, Optional
# import uuid (replaced by str)
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from ..models.task import TaskCreate, TaskUpdate, TaskResponse, TaskStatus, TaskCategory
from ..services.task_service import TaskService
from ..models.base import get_db

router = APIRouter()

@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    """Create a new task"""
    return TaskService.create_task(db, task)

@router.get("/", response_model=List[TaskResponse])
def read_tasks(
    skip: int = 0, 
    limit: int = 100,
    status: Optional[TaskStatus] = None,
    category: Optional[TaskCategory] = None,
    min_priority: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Get all tasks with optional filtering
    
    - **skip**: Number of tasks to skip (pagination)
    - **limit**: Maximum number of tasks to return
    - **status**: Filter by task status
    - **category**: Filter by task category
    - **min_priority**: Filter by minimum priority level
    """
    # Basic tasks fetch with pagination
    tasks = TaskService.get_tasks(db, skip, limit)
    
    # Apply filters if provided
    if status:
        tasks = [t for t in tasks if t.status == status]
    
    if category:
        tasks = [t for t in tasks if t.category == category]
    
    if min_priority:
        tasks = [t for t in tasks if t.priority >= min_priority]
    
    return tasks

@router.get("/{task_id}", response_model=TaskResponse)
def read_task(task_id: str, db: Session = Depends(get_db)):
    """Get a specific task by ID"""
    task = TaskService.get_task(db, task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    return task

@router.put("/{task_id}", response_model=TaskResponse)
def update_task(task_id: str, task: TaskUpdate, db: Session = Depends(get_db)):
    """Update a task"""
    # Check for circular dependencies
    if task.dependencies:
        circular = TaskService.check_circular_dependencies(task_id, task.dependencies, db)
        if circular:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Circular dependency detected"
            )
    
    updated_task = TaskService.update_task(db, task_id, task)
    if updated_task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    return updated_task

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: str, db: Session = Depends(get_db)):
    """Delete a task"""
    success = TaskService.delete_task(db, task_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    return None

@router.get("/category/{category}", response_model=List[TaskResponse])
def read_tasks_by_category(category: TaskCategory, db: Session = Depends(get_db)):
    """Get all tasks for a specific category"""
    return TaskService.get_tasks_by_category(db, category)

@router.get("/status/{status}", response_model=List[TaskResponse])
def read_tasks_by_status(status: TaskStatus, db: Session = Depends(get_db)):
    """Get all tasks with a specific status"""
    return TaskService.get_tasks_by_status(db, status)

@router.get("/priority/high", response_model=List[TaskResponse])
def read_high_priority_tasks(
    min_priority: int = Query(4, ge=1, le=5),
    db: Session = Depends(get_db)
):
    """
    Get high priority tasks
    
    - **min_priority**: Minimum priority level (1-5) to consider as high priority
    """
    return TaskService.get_high_priority_tasks(db, min_priority)