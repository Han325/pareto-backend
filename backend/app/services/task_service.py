from typing import List, Optional, Dict, Set
import uuid
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from ..models.task import Task, TaskCreate, TaskUpdate, TaskStatus, TaskCategory
from ..models.base import Base

class TaskService:
    """Service for task-related operations"""
    
    @staticmethod
    def get_tasks(db: Session, skip: int = 0, limit: int = 100) -> List[Task]:
        """Get all tasks with pagination"""
        return db.query(Task).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_task(db: Session, task_id: str) -> Optional[Task]:
        """Get a specific task by ID"""
        return db.query(Task).filter(Task.id == task_id).first()
    
    @staticmethod
    def create_task(db: Session, task: TaskCreate) -> Task:
        """Create a new task"""
        # Check if dependencies exist
        if task.dependencies:
            for dep_id in task.dependencies:
                dep = db.query(Task).filter(Task.id == dep_id).first()
                if not dep:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Dependency task with ID {dep_id} not found"
                    )
        
        # Create new task
        db_task = Task(
            title=task.title,
            description=task.description,
            duration=task.duration,
            energy_cost=task.energy_cost,
            category=task.category,
            priority=task.priority,
            deadline=task.deadline,
            status=TaskStatus.TODO
        )
        
        db.add(db_task)
        db.commit()
        db.refresh(db_task)
        
        # Add dependencies
        if task.dependencies:
            for dep_id in task.dependencies:
                dep = db.query(Task).filter(Task.id == dep_id).first()
                db_task.dependencies.append(dep)
            
            db.commit()
            db.refresh(db_task)
        
        return db_task
    
    @staticmethod
    def update_task(db: Session, task_id: str, task: TaskUpdate) -> Optional[Task]:
        """Update an existing task"""
        db_task = db.query(Task).filter(Task.id == task_id).first()
        
        if not db_task:
            return None
        
        # Update task fields if provided
        update_data = task.dict(exclude_unset=True)
        
        # Handle dependencies separately
        if "dependencies" in update_data:
            dependencies = update_data.pop("dependencies")
            
            # Validate dependencies
            if dependencies:
                for dep_id in dependencies:
                    dep = db.query(Task).filter(Task.id == dep_id).first()
                    if not dep:
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Dependency task with ID {dep_id} not found"
                        )
            
            # Clear existing dependencies
            db_task.dependencies = []
            
            # Add new dependencies
            if dependencies:
                for dep_id in dependencies:
                    dep = db.query(Task).filter(Task.id == dep_id).first()
                    db_task.dependencies.append(dep)
        
        # Update other fields
        for key, value in update_data.items():
            setattr(db_task, key, value)
        
        db.commit()
        db.refresh(db_task)
        return db_task
    
    @staticmethod
    def delete_task(db: Session, task_id: str) -> bool:
        """Delete a task"""
        db_task = db.query(Task).filter(Task.id == task_id).first()
        
        if not db_task:
            return False
        
        db.delete(db_task)
        db.commit()
        return True
    
    @staticmethod
    def get_tasks_by_category(db: Session, category: TaskCategory) -> List[Task]:
        """Get all tasks for a specific category"""
        return db.query(Task).filter(Task.category == category).all()
    
    @staticmethod
    def get_tasks_by_status(db: Session, status: TaskStatus) -> List[Task]:
        """Get all tasks with a specific status"""
        return db.query(Task).filter(Task.status == status).all()
    
    @staticmethod
    def get_high_priority_tasks(db: Session, min_priority: int = 4) -> List[Task]:
        """Get all high priority tasks"""
        return db.query(Task).filter(Task.priority >= min_priority).all()
    
    @staticmethod
    def check_circular_dependencies(task_id: str, dependency_ids: List[str], 
                                   db: Session) -> bool:
        """
        Check if adding these dependencies would create a circular dependency.
        
        Returns True if circular dependency detected, False otherwise.
        """
        # Helper function to find all indirect dependencies
        def get_all_dependencies(tid: str, visited: Set[str] = None) -> Set[str]:
            if visited is None:
                visited = set()
                
            if tid in visited:
                return visited
                
            visited.add(tid)
            
            task = db.query(Task).filter(Task.id == tid).first()
            if not task:
                return visited
                
            for dep in task.dependencies:
                get_all_dependencies(dep.id, visited)
                
            return visited
        
        # Check if the task appears in its own dependency tree
        for dep_id in dependency_ids:
            all_indirect_deps = get_all_dependencies(dep_id)
            if task_id in all_indirect_deps:
                return True
                
        return False