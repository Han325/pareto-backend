from typing import List, Optional, Dict, Any
import uuid
import json
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from ..models.schedule import Schedule, ScheduleCreate, ScheduleUpdate, ScheduleTaskInfo
from ..models.task import Task
from ..models.objective import Objective
from ..models.constraints import TimeConstraints
from ..core.pareto import calculate_pareto_front, normalize_scores
from ..core.scheduler import generate_feasible_schedules, is_schedule_feasible
from ..core.scoring import calculate_objective_scores

class ScheduleService:
    """Service for schedule-related operations"""
    
    @staticmethod
    def get_schedules(db: Session, skip: int = 0, limit: int = 100) -> List[Schedule]:
        """Get all schedules with pagination"""
        return db.query(Schedule).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_schedule(db: Session, schedule_id: uuid.UUID) -> Optional[Schedule]:
        """Get a specific schedule by ID"""
        return db.query(Schedule).filter(Schedule.id == schedule_id).first()
    
    @staticmethod
    def create_schedule(db: Session, schedule: ScheduleCreate) -> Schedule:
        """Create a new schedule"""
        # Create the schedule
        db_schedule = Schedule(
            name=schedule.name,
            start_date=schedule.start_date,
            end_date=schedule.end_date,
            objective_scores={},
            pareto_rank=0,
            is_dominated=False
        )
        
        db.add(db_schedule)
        db.commit()
        db.refresh(db_schedule)
        
        # Add tasks to the schedule
        for task_info in schedule.tasks:
            task = db.query(Task).filter(Task.id == task_info.task_id).first()
            if task:
                db_schedule.tasks.append(task)
                # In a real implementation, we'd store the start time in the join table here
                
        db.commit()
        db.refresh(db_schedule)
        
        # Calculate objective scores
        objectives = db.query(Objective).all()
        scores = calculate_objective_scores(db_schedule, objectives)
        
        # Store scores as strings (JSON doesn't support UUID keys)
        db_schedule.objective_scores = {str(obj_id): score for obj_id, score in scores.items()}
        
        db.commit()
        db.refresh(db_schedule)
        
        return db_schedule
    
    @staticmethod
    def update_schedule(db: Session, schedule_id: uuid.UUID, 
                       schedule: ScheduleUpdate) -> Optional[Schedule]:
        """Update an existing schedule"""
        db_schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
        
        if not db_schedule:
            return None
            
        # Update basic fields
        update_data = schedule.dict(exclude_unset=True, exclude={"tasks"})
        
        for key, value in update_data.items():
            setattr(db_schedule, key, value)
            
        # Update tasks if provided
        if schedule.tasks is not None:
            # Clear existing tasks
            db_schedule.tasks = []
            
            # Add new tasks
            for task_info in schedule.tasks:
                task = db.query(Task).filter(Task.id == task_info.task_id).first()
                if task:
                    db_schedule.tasks.append(task)
                    # In a real implementation, we'd store the start time in the join table here
            
            # Recalculate objective scores
            objectives = db.query(Objective).all()
            scores = calculate_objective_scores(db_schedule, objectives)
            
            # Store scores as strings (JSON doesn't support UUID keys)
            db_schedule.objective_scores = {str(obj_id): score for obj_id, score in scores.items()}
        
        db.commit()
        db.refresh(db_schedule)
        return db_schedule
    
    @staticmethod
    def delete_schedule(db: Session, schedule_id: uuid.UUID) -> bool:
        """Delete a schedule"""
        db_schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
        
        if not db_schedule:
            return False
            
        db.delete(db_schedule)
        db.commit()
        return True
    
    @staticmethod
    def generate_schedules(db: Session, constraints: TimeConstraints, 
                         days: int = 7) -> List[Schedule]:
        """Generate feasible schedules based on tasks and objectives"""
        # Get all tasks and objectives
        tasks = db.query(Task).filter(Task.status != "COMPLETED").all()
        objectives = db.query(Objective).all()
        
        # Generate schedules
        schedules = generate_feasible_schedules(tasks, objectives, constraints)
        
        # Save schedules to database
        db_schedules = []
        
        for schedule in schedules:
            # Create new schedule
            db_schedule = Schedule(
                name=schedule.name,
                start_date=schedule.start_date,
                end_date=schedule.end_date,
                objective_scores=schedule.objective_scores,
                pareto_rank=schedule.pareto_rank,
                is_dominated=schedule.is_dominated
            )
            
            db.add(db_schedule)
            db.commit()
            db.refresh(db_schedule)
            
            # Add tasks
            for task in schedule.tasks:
                db_task = db.query(Task).filter(Task.id == task.id).first()
                if db_task:
                    db_schedule.tasks.append(db_task)
                    # In a real implementation, we'd store the start time in the join table here
            
            db.commit()
            db.refresh(db_schedule)
            db_schedules.append(db_schedule)
            
        return db_schedules
    
    @staticmethod
    def get_pareto_optimal_schedules(db: Session) -> List[Schedule]:
        """Get Pareto-optimal schedules"""
        schedules = db.query(Schedule).all()
        
        if not schedules:
            return []
            
        # Normalize scores across schedules
        for schedule in schedules:
            # Convert string keys back to UUIDs
            schedule.objective_scores = {uuid.UUID(k): v for k, v in schedule.objective_scores.items()}
            
        # Calculate Pareto front
        pareto_front = calculate_pareto_front(schedules)
        
        # Update schedules in database
        for schedule in schedules:
            # Convert back to string keys for database storage
            schedule.objective_scores = {str(k): v for k, v in schedule.objective_scores.items()}
            db.add(schedule)
            
        db.commit()
        
        # Return only Pareto-optimal schedules
        return [s for s in schedules if s.pareto_rank == 0]
    
    @staticmethod
    def check_schedule_feasibility(db: Session, schedule_id: uuid.UUID, 
                                 constraints: TimeConstraints) -> bool:
        """Check if a schedule is feasible given constraints"""
        schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
        
        if not schedule:
            return False
            
        return is_schedule_feasible(schedule, constraints)
    
    @staticmethod
    def calculate_objective_scores(schedule: Schedule, 
                                 objectives: List[Objective]) -> Dict[uuid.UUID, float]:
        """Calculate objective scores for a schedule"""
        return calculate_objective_scores(schedule, objectives)