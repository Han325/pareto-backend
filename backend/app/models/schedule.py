import uuid
from sqlalchemy import Column, String, DateTime, Integer, Boolean, ForeignKey, Table, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, validator

from .base import Base

# Association table for schedule-task many-to-many relationship
schedule_tasks = Table(
    'schedule_tasks',
    Base.metadata,
    Column('schedule_id', UUID(as_uuid=True), ForeignKey('schedules.id'), primary_key=True),
    Column('task_id', UUID(as_uuid=True), ForeignKey('tasks.id'), primary_key=True),
    # Store scheduled start time for each task
    Column('start_time', DateTime, nullable=False)
)

class Schedule(Base):
    """Schedule model representing a proposed arrangement of tasks."""
    __tablename__ = "schedules"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    
    # Store scores as JSON - not ideal but works for now
    # Format: {"objective_id": score_float, ...}
    objective_scores = Column(JSON, default={})
    
    # Pareto optimization data
    pareto_rank = Column(Integer, default=0)
    is_dominated = Column(Boolean, default=False)
    
    # Many-to-many relationship with tasks
    tasks = relationship(
        "Task",
        secondary=schedule_tasks,
        backref="schedules"
    )
    
    def __repr__(self):
        return f"<Schedule {self.name} ({self.start_date.date()} to {self.end_date.date()})>"
    
    @property
    def duration_days(self):
        """Calculate schedule duration in days"""
        delta = self.end_date - self.start_date
        return delta.days + 1  # Include both start and end date

# Pydantic API models
class ScheduleTaskInfo(BaseModel):
    task_id: uuid.UUID
    start_time: datetime

class ScheduleBase(BaseModel):
    name: str
    start_date: datetime
    end_date: datetime
    
    @validator('end_date')
    def end_date_after_start_date(cls, v, values):
        if 'start_date' in values and v < values['start_date']:
            raise ValueError('End date must be after start date')
        return v

class ScheduleCreate(ScheduleBase):
    tasks: List[ScheduleTaskInfo] = Field(default_factory=list)

class ScheduleUpdate(BaseModel):
    name: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    tasks: Optional[List[ScheduleTaskInfo]] = None
    
    @validator('end_date')
    def end_date_after_start_date(cls, v, values):
        if v is not None and 'start_date' in values and values['start_date'] is not None and v < values['start_date']:
            raise ValueError('End date must be after start date')
        return v

class ScheduleResponse(ScheduleBase):
    id: uuid.UUID
    tasks: List[ScheduleTaskInfo]
    objective_scores: Dict[str, float]  # objective_id -> score
    pareto_rank: int
    is_dominated: bool
    
    class Config:
        from_attributes = True
    
    # Some useful methods for the front-end
    def average_score(self) -> float:
        """Calculate average objective score"""
        if not self.objective_scores:
            return 0.0
        return sum(self.objective_scores.values()) / len(self.objective_scores)
    
    def task_count(self) -> int:
        """Get number of tasks in schedule"""
        return len(self.tasks)

# For the Pareto optimization endpoint
class ParetoScheduleResponse(BaseModel):
    schedules: List[ScheduleResponse]
    pareto_front_size: int
    dominated_count: int