from typing import List, Dict, Any, Set
import uuid
import re
from fastapi import HTTPException, status
from datetime import datetime, timedelta

from ..models.task import Task, TaskStatus
from ..models.objective import Objective
from ..models.schedule import Schedule

def validate_uuid(id_str: str) -> uuid.UUID:
    """Validate and convert string to UUID"""
    try:
        return uuid.UUID(id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid UUID format: {id_str}"
        )

def validate_positive_number(value: float, field_name: str) -> float:
    """Validate that a number is positive"""
    if value <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} must be a positive number"
        )
    return value

def validate_range(value: float, min_val: float, max_val: float, field_name: str) -> float:
    """Validate that a number is within a specified range"""
    if value < min_val or value > max_val:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} must be between {min_val} and {max_val}"
        )
    return value

def validate_date_range(start_date: datetime, end_date: datetime) -> None:
    """Validate that end date is after start date"""
    if end_date <= start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End date must be after start date"
        )

def validate_task_dependencies(tasks: List[Task]) -> None:
    """Validate that there are no circular dependencies between tasks"""
    # Build dependency graph
    graph = {task.id: [dep.id for dep in task.dependencies] for task in tasks}
    
    # Check for cycles
    visited = set()
    temp_visited = set()
    
    def has_cycle(node, visited, temp_visited):
        """Helper function to check for cycles using DFS"""
        visited.add(node)
        temp_visited.add(node)
        
        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                if has_cycle(neighbor, visited, temp_visited):
                    return True
            elif neighbor in temp_visited:
                return True
                
        temp_visited.remove(node)
        return False
    
    # Check each unvisited node
    for task in tasks:
        if task.id not in visited:
            if has_cycle(task.id, visited, temp_visited):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Circular dependency detected between tasks"
                )

def validate_schedule_tasks(schedule: Schedule) -> None:
    """Validate tasks in a schedule"""
    # Check for task conflicts
    task_times = []
    
    for task in schedule.tasks:
        # This is a simplified check - in a real implementation we'd use the actual start times
        # Start time would be stored in the schedule_tasks join table
        start_time = datetime.now()  # Placeholder
        end_time = start_time + timedelta(minutes=task.duration)
        
        # Check for overlaps
        for other_start, other_end in task_times:
            if (start_time < other_end and end_time > other_start):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Schedule contains overlapping tasks"
                )
                
        task_times.append((start_time, end_time))
        
    # Validate dependencies
    validate_task_dependencies(schedule.tasks)

def sanitize_string(input_str: str) -> str:
    """Sanitize string input to prevent injection attacks"""
    # Remove any potentially dangerous characters
    # This is a simplified version - more comprehensive sanitization would be needed in production
    sanitized = re.sub(r'[<>\'";]', '', input_str)
    return sanitized