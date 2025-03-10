from datetime import time, datetime, timedelta
from typing import List, Dict, Optional, Any, Union
from pydantic import BaseModel, Field, validator
from enum import Enum

# I don't like how verbose this is, but it works...
class DayOfWeek(str, Enum):
    MONDAY = "MONDAY"
    TUESDAY = "TUESDAY"
    WEDNESDAY = "WEDNESDAY"
    THURSDAY = "THURSDAY"
    FRIDAY = "FRIDAY"
    SATURDAY = "SATURDAY"
    SUNDAY = "SUNDAY"

class TimeSlot(BaseModel):
    """Time slot representing available time on a specific day"""
    day: DayOfWeek
    start_time: time
    end_time: time
    
    @validator('end_time')
    def end_time_after_start_time(cls, v, values):
        if 'start_time' in values and v <= values['start_time']:
            # Special case for slots that go past midnight
            if v == time(0, 0, 0):  # midnight
                return v
            raise ValueError('End time must be after start time')
        return v

class ResourceConstraint(BaseModel):
    """Constraint on resource availability during scheduling"""
    name: str
    max_daily_usage: int  # Max usage per day
    max_weekly_usage: Optional[int] = None  # Optional weekly limit
    
    @validator('max_daily_usage', 'max_weekly_usage')
    def validate_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Resource constraints must be positive')
        return v

class TimeConstraints(BaseModel):
    """Collection of constraints for schedule generation"""
    available_slots: List[TimeSlot]
    max_daily_work_minutes: int = 480  # Default 8 hours
    max_weekly_work_minutes: int = 2400  # Default 40 hours
    resource_constraints: Dict[str, ResourceConstraint] = Field(default_factory=dict)
    
    # Add any specific date exclusions (holidays, vacations, etc)
    excluded_dates: List[datetime] = Field(default_factory=list)
    
    @validator('max_daily_work_minutes', 'max_weekly_work_minutes')
    def validate_work_minutes(cls, v):
        if v <= 0:
            raise ValueError('Work minute constraints must be positive')
        return v
    
    def is_date_available(self, date: datetime) -> bool:
        """Check if a specific date is available (not excluded)"""
        return date.date() not in [ex_date.date() for ex_date in self.excluded_dates]
    
    def get_available_slots_for_day(self, day: DayOfWeek) -> List[TimeSlot]:
        """Get all available time slots for a specific day of week"""
        return [slot for slot in self.available_slots if slot.day == day]
    
    def get_total_available_minutes(self) -> int:
        """Calculate total available minutes across all slots"""
        total = 0
        for slot in self.available_slots:
            # Calculate duration accounting for potential midnight crossover
            start_minutes = slot.start_time.hour * 60 + slot.start_time.minute
            end_minutes = slot.end_time.hour * 60 + slot.end_time.minute
            
            # Handle slots that cross midnight
            if end_minutes <= start_minutes and slot.end_time != time(0, 0):
                duration = (24 * 60 - start_minutes) + end_minutes
            else:
                duration = end_minutes - start_minutes
                
            total += duration
        return total