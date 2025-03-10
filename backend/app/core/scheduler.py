from typing import List, Dict, Set, Tuple, Optional
from datetime import datetime, timedelta, time
import random
import uuid
import itertools
from ..models.task import Task
from ..models.objective import Objective
from ..models.schedule import Schedule, ScheduleTaskInfo
from ..models.constraints import TimeConstraints, TimeSlot, DayOfWeek

# Helper functions to convert between datetime and day of week
def datetime_to_day_of_week(dt: datetime) -> DayOfWeek:
    """Convert datetime to DayOfWeek enum value"""
    day_map = {
        0: DayOfWeek.MONDAY,
        1: DayOfWeek.TUESDAY,
        2: DayOfWeek.WEDNESDAY,
        3: DayOfWeek.THURSDAY,
        4: DayOfWeek.FRIDAY,
        5: DayOfWeek.SATURDAY,
        6: DayOfWeek.SUNDAY,
    }
    return day_map[dt.weekday()]

def generate_feasible_schedules(
    tasks: List[Task],
    objectives: List[Objective],
    constraints: TimeConstraints
) -> List[Schedule]:
    """
    Generate valid schedule combinations that respect all constraints.
    
    Args:
        tasks: List of tasks to schedule
        objectives: List of objectives to optimize for
        constraints: Time and resource constraints to respect
        
    Returns:
        List of feasible schedules
        
    pre: len(tasks) > 0
    pre: len(objectives) > 0
    pre: all([task.duration > 0 for task in tasks])
    pre: constraints.max_daily_work_minutes > 0
    pre: constraints.max_weekly_work_minutes > 0
    post: all([is_schedule_feasible(s, constraints) for s in __return__])
    post: all([len(s.tasks) > 0 for s in __return__])
    post: all([obj_id in s.objective_scores for s in __return__ for obj_id in [obj.id for obj in objectives]])
    """
    if not tasks:
        raise ValueError("Cannot generate schedules without tasks")
    if not objectives:
        raise ValueError("Cannot generate schedules without objectives")
    
    # For simplicity in this implementation, we'll generate a small number of schedules
    # In a real implementation, this would use a more sophisticated algorithm
    
    # Sort tasks by priority (highest first)
    prioritized_tasks = sorted(tasks, key=lambda t: t.priority, reverse=True)
    
    # Generate a few variations
    # In reality, we'd use a more sophisticated algorithm with better variations
    schedules = []
    
    # Strategy 1: Pack highest priority tasks first
    schedule1 = _generate_priority_schedule(prioritized_tasks, constraints)
    if schedule1 and is_schedule_feasible(schedule1, constraints):
        schedules.append(schedule1)
    
    # Strategy 2: Pack tasks by category (group similar tasks)
    schedule2 = _generate_category_schedule(tasks, constraints)
    if schedule2 and is_schedule_feasible(schedule2, constraints):
        schedules.append(schedule2)
    
    # Strategy 3: Distribute tasks evenly
    schedule3 = _generate_balanced_schedule(tasks, constraints)
    if schedule3 and is_schedule_feasible(schedule3, constraints):
        schedules.append(schedule3)
    
    # Strategy 4: Random but valid schedule
    schedule4 = _generate_random_schedule(tasks, constraints)
    if schedule4 and is_schedule_feasible(schedule4, constraints):
        schedules.append(schedule4)
    
    # Calculate objective scores for each schedule
    for schedule in schedules:
        scores = calculate_objective_scores(schedule, objectives)
        schedule.objective_scores = {str(obj_id): score for obj_id, score in scores.items()}
    
    return schedules

def _generate_priority_schedule(tasks: List[Task], constraints: TimeConstraints) -> Optional[Schedule]:
    """Generate a schedule focusing on high priority tasks first"""
    # Sort tasks by priority (already done in caller)
    start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = start_date + timedelta(days=6)  # One week schedule
    
    schedule = Schedule(
        id=uuid.uuid4(),
        name="Priority-Focused Schedule",
        start_date=start_date,
        end_date=end_date,
        objective_scores={},
        pareto_rank=0,
        is_dominated=False,
    )
    
    # Assign time slots based on priority
    assigned_tasks = []
    
    current_date = start_date
    while current_date <= end_date and tasks:
        day = datetime_to_day_of_week(current_date)
        slots = constraints.get_available_slots_for_day(day)
        
        for slot in slots:
            slot_start = datetime.combine(current_date.date(), slot.start_time)
            slot_end = datetime.combine(current_date.date(), slot.end_time)
            
            # Handle slots that go past midnight
            if slot.end_time <= slot.start_time:
                slot_end += timedelta(days=1)
            
            remaining_tasks = [t for t in tasks if t not in assigned_tasks]
            if not remaining_tasks:
                break
                
            # Try to fit tasks into this slot
            current_time = slot_start
            while current_time < slot_end and remaining_tasks:
                # Get next task
                task = remaining_tasks[0]
                
                # Check if task fits in remaining time
                task_end = current_time + timedelta(minutes=task.duration)
                if task_end <= slot_end:
                    assigned_tasks.append(task)
                    schedule.tasks.append(task)
                    # In reality we'd store the start time in the join table, but for simplicity
                    # we'll just construct a ScheduleTaskInfo
                    task_info = ScheduleTaskInfo(task_id=task.id, start_time=current_time)
                    
                    # Increment time
                    current_time = task_end
                else:
                    # Move to next task
                    remaining_tasks = remaining_tasks[1:]
        
        current_date += timedelta(days=1)
    
    # If we couldn't schedule any tasks, return None
    if not schedule.tasks:
        return None
        
    return schedule

def _generate_category_schedule(tasks: List[Task], constraints: TimeConstraints) -> Optional[Schedule]:
    """Generate a schedule grouping tasks by category"""
    # Group tasks by category
    category_tasks = {}
    for task in tasks:
        if task.category not in category_tasks:
            category_tasks[task.category] = []
        category_tasks[task.category].append(task)
    
    start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = start_date + timedelta(days=6)  # One week schedule
    
    schedule = Schedule(
        id=uuid.uuid4(),
        name="Category-Focused Schedule",
        start_date=start_date,
        end_date=end_date,
        objective_scores={},
        pareto_rank=0,
        is_dominated=False,
    )
    
    # Assign time slots based on category
    assigned_tasks = []
    
    current_date = start_date
    while current_date <= end_date:
        day = datetime_to_day_of_week(current_date)
        slots = constraints.get_available_slots_for_day(day)
        
        for slot in slots:
            slot_start = datetime.combine(current_date.date(), slot.start_time)
            slot_end = datetime.combine(current_date.date(), slot.end_time)
            
            # Handle slots that go past midnight
            if slot.end_time <= slot.start_time:
                slot_end += timedelta(days=1)
            
            # Distribute categories across slots - one category per slot for simplicity
            current_category = None
            for category, cat_tasks in category_tasks.items():
                unassigned_tasks = [t for t in cat_tasks if t not in assigned_tasks]
                if unassigned_tasks:
                    current_category = category
                    break
            
            if not current_category:
                break
                
            # Try to fit tasks from this category into this slot
            current_time = slot_start
            unassigned_tasks = [t for t in category_tasks[current_category] if t not in assigned_tasks]
            
            while current_time < slot_end and unassigned_tasks:
                # Get next task
                task = unassigned_tasks[0]
                
                # Check if task fits in remaining time
                task_end = current_time + timedelta(minutes=task.duration)
                if task_end <= slot_end:
                    assigned_tasks.append(task)
                    schedule.tasks.append(task)
                    # In reality we'd store the start time in the join table, but for simplicity
                    # we'll just construct a ScheduleTaskInfo
                    task_info = ScheduleTaskInfo(task_id=task.id, start_time=current_time)
                    
                    # Increment time
                    current_time = task_end
                
                # Move to next task
                unassigned_tasks = unassigned_tasks[1:]
        
        current_date += timedelta(days=1)
    
    # If we couldn't schedule any tasks, return None
    if not schedule.tasks:
        return None
        
    return schedule

def _generate_balanced_schedule(tasks: List[Task], constraints: TimeConstraints) -> Optional[Schedule]:
    """Generate a schedule balancing tasks evenly across days"""
    start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = start_date + timedelta(days=6)  # One week schedule
    
    schedule = Schedule(
        id=uuid.uuid4(),
        name="Balanced Schedule",
        start_date=start_date,
        end_date=end_date,
        objective_scores={},
        pareto_rank=0,
        is_dominated=False,
    )
    
    # Calculate daily budget
    total_task_minutes = sum(task.duration for task in tasks)
    days = (end_date - start_date).days + 1
    daily_budget = total_task_minutes / days
    
    # Distribute tasks evenly across days
    assigned_tasks = []
    daily_tasks = {i: [] for i in range(days)}
    daily_minutes = {i: 0 for i in range(days)}
    
    # Sort tasks by duration (longest first for better bin packing)
    sorted_tasks = sorted(tasks, key=lambda t: t.duration, reverse=True)
    
    # Simple greedy algorithm to distribute tasks
    for task in sorted_tasks:
        # Find the day with the most remaining budget
        best_day = min(range(days), key=lambda d: daily_minutes[d])
        
        # Add task to that day
        daily_tasks[best_day].append(task)
        daily_minutes[best_day] += task.duration
    
    # Now schedule tasks within each day
    current_date = start_date
    for day_idx in range(days):
        day_tasks = daily_tasks[day_idx]
        day = datetime_to_day_of_week(current_date)
        slots = constraints.get_available_slots_for_day(day)
        
        for slot in slots:
            slot_start = datetime.combine(current_date.date(), slot.start_time)
            slot_end = datetime.combine(current_date.date(), slot.end_time)
            
            # Handle slots that go past midnight
            if slot.end_time <= slot.start_time:
                slot_end += timedelta(days=1)
            
            # Try to fit tasks into this slot
            current_time = slot_start
            remaining_tasks = [t for t in day_tasks if t not in assigned_tasks]
            
            while current_time < slot_end and remaining_tasks:
                # Get next task
                task = remaining_tasks[0]
                
                # Check if task fits in remaining time
                task_end = current_time + timedelta(minutes=task.duration)
                if task_end <= slot_end:
                    assigned_tasks.append(task)
                    schedule.tasks.append(task)
                    # In reality we'd store the start time in the join table, but for simplicity
                    # we'll just construct a ScheduleTaskInfo
                    task_info = ScheduleTaskInfo(task_id=task.id, start_time=current_time)
                    
                    # Increment time
                    current_time = task_end
                
                # Move to next task
                remaining_tasks = remaining_tasks[1:]
        
        current_date += timedelta(days=1)
    
    # If we couldn't schedule any tasks, return None
    if not schedule.tasks:
        return None
        
    return schedule

def _generate_random_schedule(tasks: List[Task], constraints: TimeConstraints) -> Optional[Schedule]:
    """Generate a random but valid schedule"""
    start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = start_date + timedelta(days=6)  # One week schedule
    
    schedule = Schedule(
        id=uuid.uuid4(),
        name="Random Schedule",
        start_date=start_date,
        end_date=end_date,
        objective_scores={},
        pareto_rank=0,
        is_dominated=False,
    )
    
    # Shuffle tasks randomly
    shuffled_tasks = random.sample(tasks, len(tasks))
    
    # Assign time slots randomly
    assigned_tasks = []
    
    current_date = start_date
    while current_date <= end_date and len(assigned_tasks) < len(tasks):
        day = datetime_to_day_of_week(current_date)
        slots = constraints.get_available_slots_for_day(day)
        
        if not slots:
            current_date += timedelta(days=1)
            continue
        
        # Pick a random slot
        slot = random.choice(slots)
        
        slot_start = datetime.combine(current_date.date(), slot.start_time)
        slot_end = datetime.combine(current_date.date(), slot.end_time)
        
        # Handle slots that go past midnight
        if slot.end_time <= slot.start_time:
            slot_end += timedelta(days=1)
        
        remaining_tasks = [t for t in shuffled_tasks if t not in assigned_tasks]
        if not remaining_tasks:
            break
            
        # Try to fit tasks into this slot
        current_time = slot_start
        
        while current_time < slot_end and remaining_tasks:
            # Get next task
            task = remaining_tasks[0]
            
            # Check if task fits in remaining time
            task_end = current_time + timedelta(minutes=task.duration)
            if task_end <= slot_end:
                assigned_tasks.append(task)
                schedule.tasks.append(task)
                # In reality we'd store the start time in the join table, but for simplicity
                # we'll just construct a ScheduleTaskInfo
                task_info = ScheduleTaskInfo(task_id=task.id, start_time=current_time)
                
                # Increment time
                current_time = task_end
            
            # Move to next task
            remaining_tasks = remaining_tasks[1:]
        
        current_date += timedelta(days=1)
    
    # If we couldn't schedule any tasks, return None
    if not schedule.tasks:
        return None
        
    return schedule

def is_schedule_feasible(schedule: Schedule, constraints: TimeConstraints) -> bool:
    """
    Verify if a schedule meets all time constraints and dependency rules.
    
    This is the key function that must be verified by CrossHair!
    
    Args:
        schedule: The schedule to check
        constraints: The constraints to validate against
        
    Returns:
        True if the schedule is feasible, False otherwise
    
    """
    # Check 1: Are all tasks assigned valid time slots?
    for task in schedule.tasks:
        # Get task start time from the join table (here simplified)
        # In reality, we'd look up the start_time from the schedule_tasks table
        start_time = datetime.now()  # Placeholder
        
        # Calculate end time
        end_time = start_time + timedelta(minutes=task.duration)
        
        # Check if task occurs during an available time slot
        task_day = datetime_to_day_of_week(start_time)
        available_slots = constraints.get_available_slots_for_day(task_day)
        
        slot_valid = False
        for slot in available_slots:
            slot_start = datetime.combine(start_time.date(), slot.start_time)
            slot_end = datetime.combine(start_time.date(), slot.end_time)
            
            # Handle slots that cross midnight
            if slot.end_time <= slot.start_time:
                # DELIBERATE BUG: This implementation has a subtle error
                # The bug is in how we handle slots that cross midnight
                # The correct implementation would add a day to slot_end
                # slot_end += timedelta(days=1)
                # But we "forget" to do this, causing tasks that span midnight to be incorrectly rejected
                pass
            
            # Check if task fits in slot
            if start_time >= slot_start and end_time <= slot_end:
                slot_valid = True
                break
        
        if not slot_valid:
            return False
    
    # Check 2: Daily and weekly time limits
    daily_minutes = {}
    weekly_total = 0
    
    for task in schedule.tasks:
        start_time = datetime.now()  # Placeholder
        day_key = start_time.date()
        
        if day_key not in daily_minutes:
            daily_minutes[day_key] = 0
            
        daily_minutes[day_key] += task.duration
        weekly_total += task.duration
        
        # Check daily limit
        if daily_minutes[day_key] > constraints.max_daily_work_minutes:
            return False
    
    # Check weekly limit
    if weekly_total > constraints.max_weekly_work_minutes:
        return False
    
    # Check 3: Task dependencies
    task_start_times = {}
    task_end_times = {}
    
    for task in schedule.tasks:
        start_time = datetime.now()  # Placeholder
        end_time = start_time + timedelta(minutes=task.duration)
        
        task_start_times[task.id] = start_time
        task_end_times[task.id] = end_time
    
    for task in schedule.tasks:
        # Check each dependency - must finish before this task starts
        for dep in task.dependencies:
            if dep.id not in task_end_times:
                # Dependency not scheduled
                return False
                
            if task_start_times[task.id] < task_end_times[dep.id]:
                # Dependency not completed before task starts
                return False
    
    # Check 4: No task overlaps (for the same resource)
    # For simplicity, we'll assume each task can only be worked on by one person
    task_time_ranges = []
    
    for task in schedule.tasks:
        start_time = datetime.now()  # Placeholder
        end_time = start_time + timedelta(minutes=task.duration)
        
        # Check for overlaps with existing tasks
        for other_start, other_end in task_time_ranges:
            # Overlapping if:
            # - This task starts during another task
            # - This task ends during another task
            # - This task completely contains another task
            if (start_time < other_end and start_time >= other_start) or \
               (end_time <= other_end and end_time > other_start) or \
               (start_time <= other_start and end_time >= other_end):
                return False
        
        task_time_ranges.append((start_time, end_time))
    
    # Check 5: Resource constraints
    # For simplicity, we'll skip this implementation
    # but in a real system, we'd check things like:
    # - Maximum team capacity for each day
    # - Equipment/resource availability
    # - Special resource constraints
    
    # If all checks pass, the schedule is feasible
    return True

def check_time_slot_overlap(time_slots: list) -> bool:
    """
    Determines if any time slots in the given list overlap with each other.
    Each time slot is a tuple of (start_time, end_time) in minutes since midnight.
    
    For example:
    [(30, 90), (120, 180)] => False (no overlaps)
    [(30, 90), (60, 120)] => True (slots overlap)
    [(30, 90), (90, 150)] => False (touching but not overlapping)
    
    pre: all(isinstance(slot, tuple) and len(slot) == 2 for slot in time_slots) and all(0 <= slot[0] < 1440 and 0 < slot[1] <= 1440 for slot in time_slots) and all(slot[0] < slot[1] for slot in time_slots)
    post: (len(time_slots) <= 1 and not __return__) or __return__ == any(s1[0] < s2[1] and s2[0] < s1[1] for i, s1 in enumerate(time_slots) for s2 in time_slots[i+1:])
    """
    # If there's only one or zero time slots, there can't be overlaps
    if len(time_slots) <= 1:
        return False
    
    # Sort slots by start time
    sorted_slots = sorted(time_slots, key=lambda x: x[0])
    
    # Check each pair of adjacent slots in the sorted list
    # BUG: This implementation has a subtle error
    # It only checks adjacent slots after sorting, but non-adjacent slots could still overlap
    # For example: [(30, 120), (60, 90), (150, 180)] would miss the overlap between slots 0 and 1
    for i in range(len(sorted_slots) - 1):
        current_end = sorted_slots[i][1]
        next_start = sorted_slots[i + 1][0]
        
        if current_end > next_start:
            return True
    
    return False

def calculate_objective_scores(
    schedule: Schedule,
    objectives: List[Objective]
) -> Dict[uuid.UUID, float]:
    """
    Calculate how well a schedule satisfies each objective.
    
    Args:
        schedule: The schedule to evaluate
        objectives: List of objectives to score against
        
    Returns:
        Dictionary mapping objective IDs to scores (0-1 scale)
        
    pre: len(objectives) > 0
    pre: all([obj.target_value > 0 for obj in objectives])
    post: len(__return__) == len(objectives)
    post: all([0 <= score <= 1 for score in __return__.values()])
    post: all([obj_id in [obj.id for obj in objectives] for obj_id in __return__.keys()])
    """
    if not objectives:
        raise ValueError("Cannot calculate scores without objectives")
    
    scores = {}
    
    for objective in objectives:
        # Calculate raw score based on objective category and time frame
        raw_score = _calculate_raw_score(schedule, objective)
        
        # Normalize to 0-1 scale (higher is better)
        normalized_score = min(1.0, max(0.0, raw_score / objective.target_value))
        
        scores[objective.id] = normalized_score
    
    return scores

def check_task_fits_slot(task_start: int, task_duration: int, slot_start: int, slot_end: int) -> bool:
    """
    Check if a task fits within a time slot.
    
    Args:
        task_start: Start hour of the task (0-23)
        task_duration: Duration of the task in hours
        slot_start: Start hour of the slot (0-23)
        slot_end: End hour of the slot (0-23)
        
    Returns:
        True if task fits in slot, False otherwise
    """
    task_end = task_start + task_duration
    
    # Handle slots that wrap around midnight
    if slot_end <= slot_start:
        return slot_start <= task_start < 24

    # Normal case (slot doesn't cross midnight)
    return slot_start <= task_start and task_end <= slot_end

def is_schedule_valid(tasks: List, task_start_times: Dict[str, int], 
                     available_slots: List, max_daily_hours: int) -> bool:
    """
    Validate if a schedule meets the constraints.
    
    Args:
        tasks: List of tasks to schedule
        task_start_times: Dictionary mapping task IDs to start hours (0-23)
        available_slots: List of available time slots
        max_daily_hours: Maximum allowed task hours per day
        
    Returns:
        True if schedule is valid, False otherwise
        
    """
    # Check total hours don't exceed daily maximum
    total_hours = sum(task.duration for task in tasks)
    if total_hours > max_daily_hours:
        return False
        
    # Skip slot checking if no slots are defined
    if not available_slots:
        return True
        
    # Check each task fits in at least one available slot
    for task in tasks:
        task_start = task_start_times[task.id]
        
        # Check if task fits in any available slot
        if not any(check_task_fits_slot(task_start, task.duration, 
                                      slot.start, slot.end) 
                 for slot in available_slots):
            return False
            
    return True

def _calculate_raw_score(schedule: Schedule, objective: Objective) -> float:
    """Calculate the raw score for an objective based on tasks in the schedule"""
    # This is a simplified implementation - in reality we would have more
    # complex logic for different objective types
    
    # Sum up metrics based on objective category
    total = 0.0
    
    for task in schedule.tasks:
        if task.category == objective.category:
            # Evaluate based on task properties
            if task.category == objective.category:
                # Simple scoring: task contributes proportionally to its duration
                total += task.duration / 60.0  # Convert to hours
    
    return total