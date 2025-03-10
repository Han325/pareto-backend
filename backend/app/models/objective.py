import enum
import uuid
from sqlalchemy import Column, String, Float, Enum
from sqlalchemy.dialects.postgresql import UUID
from typing import Optional
from pydantic import BaseModel, Field, validator

from .base import Base
from .task import TaskCategory

# TODO: Consider adding more granular timeframes later
class TimeFrame(str, enum.Enum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    YEARLY = "YEARLY"

class Objective(Base):
    """Database model for life objectives/goals."""
    __tablename__ = "objectives"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    category = Column(Enum(TaskCategory), nullable=False)
    target_value = Column(Float, nullable=False)  # what we're aiming for
    current_value = Column(Float, default=0.0)    # where we are now
    weight = Column(Float, nullable=False)        # importance (0-1)
    measurement_unit = Column(String, nullable=False)
    time_frame = Column(Enum(TimeFrame), nullable=False)

    def __repr__(self):
        return f"<Objective {self.name}>"

# API models below
class ObjectiveBase(BaseModel):
    name: str
    category: TaskCategory
    target_value: float
    weight: float
    measurement_unit: str
    time_frame: TimeFrame
    
    # Ensure weight is valid
    @validator('weight')
    def weight_must_be_valid(cls, v):
        if not 0 <= v <= 1:
            raise ValueError('Weight must be between 0 and 1')
        return v

class ObjectiveCreate(ObjectiveBase):
    current_value: float = 0.0  # Default to 0 for new objectives

class ObjectiveUpdate(BaseModel):
    # All fields optional for partial updates
    name: Optional[str] = None
    category: Optional[TaskCategory] = None
    target_value: Optional[float] = None
    current_value: Optional[float] = None
    weight: Optional[float] = None
    measurement_unit: Optional[str] = None
    time_frame: Optional[TimeFrame] = None
    
    @validator('weight')
    def validate_weight(cls, v):
        if v is not None and not (0 <= v <= 1):
            raise ValueError('Weight must be between 0 and 1')
        return v

class ObjectiveResponse(ObjectiveBase):
    id: uuid.UUID
    current_value: float
    
    class Config:
        from_attributes = True
        
    # Helper method to calculate progress percentage
    def progress_percentage(self) -> float:
        if self.target_value == 0:
            return 100.0 if self.current_value >= 0 else 0.0
        return min(100.0, (self.current_value / self.target_value) * 100)