import enum
import uuid
from sqlalchemy import Column, String, Integer, Float, DateTime, Enum, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, validator

from .base import Base

# Association table for tracking task dependencies
# A bit ugly but SQLAlchemy needs this for many-to-many self-refs
task_dependencies = Table(
    'task_dependencies',
    Base.metadata,
    Column('task_id', String, ForeignKey('tasks.id'), primary_key=True),
    Column('dependency_id', String, ForeignKey('tasks.id'), primary_key=True)
)

class TaskCategory(str, enum.Enum):
    # Main life categories - might expand this later
    WORK = "WORK"
    HEALTH = "HEALTH"
    RELATIONSHIPS = "RELATIONSHIPS"
    LEARNING = "LEARNING"
    LEISURE = "LEISURE"
    CHORES = "CHORES"
    FINANCE = "FINANCE"
    OTHER = "OTHER"  # Catch-all for misc tasks

class TaskStatus(str, enum.Enum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    # NOTE: Maybe add BLOCKED and CANCELLED later?

class Task(Base):
    """Task model representing individual activities that can be scheduled."""
    __tablename__ = "tasks"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    description = Column(String)
    duration = Column(Integer, nullable=False)  # in minutes
    energy_cost = Column(Integer, nullable=False)  # 1-10 scale
    category = Column(Enum(TaskCategory), nullable=False)
    priority = Column(Integer, nullable=False)  # 1-5 scale
    deadline = Column(DateTime, nullable=True)  # optional deadline
    status = Column(Enum(TaskStatus), default=TaskStatus.TODO)
    
    # Self-referential relationship for dependencies
    # Thanks to StackOverflow for helping with this nightmare
    dependencies = relationship(
        "Task",
        secondary=task_dependencies,
        primaryjoin=id==task_dependencies.c.task_id,
        secondaryjoin=id==task_dependencies.c.dependency_id,
        backref="dependent_tasks"
    )
    
    # We'll add this once the Schedule model is created
    # schedules = relationship("ScheduleTask", back_populates="task")
    
    def __repr__(self):
        return f"<Task {self.title} ({self.status.value})>"
    
    def is_high_priority(self):
        return self.priority >= 4
    
    def energy_level_text(self):
        if self.energy_cost <= 3:
            return "Low energy"
        elif self.energy_cost <= 7:
            return "Medium energy"
        else:
            return "High energy"

# API Pydantic models below
class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    duration: int  # minutes
    energy_cost: int  # 1-10
    category: TaskCategory
    priority: int  # 1-5
    deadline: Optional[datetime] = None
    
    @validator('priority')
    def priority_range(cls, v):
        if not 1 <= v <= 5:
            raise ValueError('Priority must be between 1 and 5')
        return v
    
    @validator('energy_cost')
    def energy_range(cls, v):
        if not 1 <= v <= 10:
            raise ValueError('Energy cost must be between 1 and 10')
        return v
    
class TaskCreate(TaskBase):
    # Default to empty list if no dependencies specified
    dependencies: List[str] = Field(default_factory=list)

class TaskUpdate(BaseModel):
    # All fields optional for PATCH requests
    title: Optional[str] = None
    description: Optional[str] = None
    duration: Optional[int] = None
    energy_cost: Optional[int] = None
    category: Optional[TaskCategory] = None
    priority: Optional[int] = None
    deadline: Optional[datetime] = None
    status: Optional[TaskStatus] = None
    dependencies: Optional[List[str]] = None
    
    @validator('priority')
    def priority_range(cls, v):
        if v is not None and not (1 <= v <= 5):
            raise ValueError('Priority must be between 1 and 5')
        return v
    
    @validator('energy_cost')
    def energy_range(cls, v):
        if v is not None and not (1 <= v <= 10):
            raise ValueError('Energy cost must be between 1 and 10')
        return v

class TaskResponse(TaskBase):
    id: str
    status: TaskStatus
    dependencies: List[str]
    
    class Config:
        from_attributes = True
        
    def time_until_deadline(self):
        if not self.deadline:
            return None
        return (self.deadline - datetime.now()).total_seconds()