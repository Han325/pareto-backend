from typing import List, Optional, Dict
import uuid
from sqlalchemy.orm import Session

from ..models.objective import Objective, ObjectiveCreate, ObjectiveUpdate
from ..models.task import TaskCategory

class ObjectiveService:
    """Service for objective-related operations"""
    
    @staticmethod
    def get_objectives(db: Session, skip: int = 0, limit: int = 100) -> List[Objective]:
        """Get all objectives with pagination"""
        return db.query(Objective).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_objective(db: Session, objective_id: uuid.UUID) -> Optional[Objective]:
        """Get a specific objective by ID"""
        return db.query(Objective).filter(Objective.id == objective_id).first()
    
    @staticmethod
    def create_objective(db: Session, objective: ObjectiveCreate) -> Objective:
        """Create a new objective"""
        db_objective = Objective(
            name=objective.name,
            category=objective.category,
            target_value=objective.target_value,
            current_value=objective.current_value,
            weight=objective.weight,
            measurement_unit=objective.measurement_unit,
            time_frame=objective.time_frame
        )
        
        db.add(db_objective)
        db.commit()
        db.refresh(db_objective)
        return db_objective
    
    @staticmethod
    def update_objective(db: Session, objective_id: uuid.UUID, 
                       objective: ObjectiveUpdate) -> Optional[Objective]:
        """Update an existing objective"""
        db_objective = db.query(Objective).filter(Objective.id == objective_id).first()
        
        if not db_objective:
            return None
            
        # Update objective fields if provided
        update_data = objective.dict(exclude_unset=True)
        
        for key, value in update_data.items():
            setattr(db_objective, key, value)
            
        db.commit()
        db.refresh(db_objective)
        return db_objective
    
    @staticmethod
    def delete_objective(db: Session, objective_id: uuid.UUID) -> bool:
        """Delete an objective"""
        db_objective = db.query(Objective).filter(Objective.id == objective_id).first()
        
        if not db_objective:
            return False
            
        db.delete(db_objective)
        db.commit()
        return True
    
    @staticmethod
    def get_objectives_by_category(db: Session, category: TaskCategory) -> List[Objective]:
        """Get all objectives for a specific category"""
        return db.query(Objective).filter(Objective.category == category).all()
    
    @staticmethod
    def update_objective_progress(db: Session, objective_id: uuid.UUID, 
                                value: float) -> Optional[Objective]:
        """Update the current value of an objective"""
        db_objective = db.query(Objective).filter(Objective.id == objective_id).first()
        
        if not db_objective:
            return None
            
        db_objective.current_value = value
        db.commit()
        db.refresh(db_objective)
        return db_objective
    
    @staticmethod
    def normalize_weights(db: Session) -> None:
        """Normalize all objective weights to sum to 1.0"""
        objectives = db.query(Objective).all()
        
        if not objectives:
            return
            
        # Calculate sum of all weights
        total_weight = sum(obj.weight for obj in objectives)
        
        if total_weight == 0:
            # If all weights are zero, distribute evenly
            even_weight = 1.0 / len(objectives)
            for obj in objectives:
                obj.weight = even_weight
        else:
            # Normalize weights to sum to 1.0
            for obj in objectives:
                obj.weight = obj.weight / total_weight
                
        db.commit()
    
    @staticmethod
    def get_progress_percentages(db: Session) -> Dict[uuid.UUID, float]:
        """Calculate progress percentage for all objectives"""
        objectives = db.query(Objective).all()
        
        if not objectives:
            return {}
            
        progress = {}
        
        for obj in objectives:
            if obj.target_value == 0:
                # Handle division by zero
                percent = 100.0 if obj.current_value >= 0 else 0.0
            else:
                percent = min(100.0, (obj.current_value / obj.target_value) * 100)
                
            progress[obj.id] = percent
            
        return progress
    
    @staticmethod
    def calculate_overall_progress(db: Session) -> float:
        """Calculate weighted average progress across all objectives"""
        objectives = db.query(Objective).all()
        
        if not objectives:
            return 0.0
            
        progress_values = ObjectiveService.get_progress_percentages(db)
        
        # Calculate sum of all weights
        total_weight = sum(obj.weight for obj in objectives)
        
        if total_weight == 0:
            # If all weights are zero, use simple average
            return sum(progress_values.values()) / len(progress_values) if progress_values else 0.0
            
        # Calculate weighted average
        weighted_sum = 0.0
        
        for obj in objectives:
            if obj.id in progress_values:
                weighted_sum += progress_values[obj.id] * (obj.weight / total_weight)
                
        return weighted_sum