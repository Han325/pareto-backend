from typing import List, Dict, Set, Tuple, Optional
from datetime import datetime, timedelta
import uuid
import math
from ..models.task import Task, TaskCategory
from ..models.objective import Objective, TimeFrame
from ..models.schedule import Schedule

def calculate_objective_scores(schedule: Schedule, objectives: List[Objective]) -> Dict[str, float]:
    """
    Calculate how well a schedule satisfies each objective.
    
    Args:
        schedule: The schedule to evaluate
        objectives: List of objectives to score against
        
    Returns:
        Dictionary mapping objective IDs to scores
    """
    scores = {}
    
    for objective in objectives:
        # Calculate raw score for this objective
        raw_score = score_schedule_for_objective(schedule, objective)
        
        # Normalize to 0-1 scale (higher is better)
        normalized_score = min(1.0, max(0.0, raw_score / (objective.target_value or 1.0)))
        
        # Store score
        scores[str(objective.id)] = normalized_score
    
    return scores

def score_schedule_for_objective(schedule: Schedule, objective: Objective) -> float:
    """
    Calculate a raw score for how well a schedule satisfies an objective.
    
    Args:
        schedule: The schedule to evaluate
        objective: The objective to score against
        
    Returns:
        Raw score value (higher is better)
    """
    # Filter tasks by category
    relevant_tasks = [task for task in schedule.tasks if task.category == objective.category]
    
    # No relevant tasks means zero score
    if not relevant_tasks:
        return 0.0
    
    # Calculate base score depending on time frame
    if objective.time_frame == TimeFrame.DAILY:
        return _calculate_daily_score(schedule, relevant_tasks, objective)
    elif objective.time_frame == TimeFrame.WEEKLY:
        return _calculate_weekly_score(schedule, relevant_tasks, objective)
    elif objective.time_frame == TimeFrame.MONTHLY:
        return _calculate_monthly_score(schedule, relevant_tasks, objective)
    elif objective.time_frame == TimeFrame.YEARLY:
        return _calculate_yearly_score(schedule, relevant_tasks, objective)
    
    # Default fallback
    return sum(task.duration for task in relevant_tasks) / 60.0  # hours

def _calculate_daily_score(schedule: Schedule, tasks: List[Task], objective: Objective) -> float:
    """Calculate score for a daily objective"""
    # Get schedule duration in days
    days = (schedule.end_date - schedule.start_date).days + 1
    
    # Calculate average daily value
    total_value = sum(task.duration for task in tasks) / 60.0  # hours
    daily_average = total_value / days
    
    return daily_average

def _calculate_weekly_score(schedule: Schedule, tasks: List[Task], objective: Objective) -> float:
    """Calculate score for a weekly objective"""
    # Get schedule duration in weeks (partial weeks count)
    weeks = ((schedule.end_date - schedule.start_date).days + 1) / 7.0
    
    # Calculate average weekly value
    total_value = sum(task.duration for task in tasks) / 60.0  # hours
    weekly_average = total_value / max(1.0, weeks)  # avoid division by zero
    
    return weekly_average

def _calculate_monthly_score(schedule: Schedule, tasks: List[Task], objective: Objective) -> float:
    """Calculate score for a monthly objective"""
    # Get schedule duration in months (approximate)
    months = ((schedule.end_date - schedule.start_date).days + 1) / 30.0
    
    # Calculate average monthly value
    total_value = sum(task.duration for task in tasks) / 60.0  # hours
    monthly_average = total_value / max(1.0, months)  # avoid division by zero
    
    return monthly_average

def _calculate_yearly_score(schedule: Schedule, tasks: List[Task], objective: Objective) -> float:
    """Calculate score for a yearly objective"""
    # Get schedule duration in years (approximate)
    years = ((schedule.end_date - schedule.start_date).days + 1) / 365.0
    
    # Calculate average yearly value
    total_value = sum(task.duration for task in tasks) / 60.0  # hours
    yearly_average = total_value / max(1.0, years)  # avoid division by zero
    
    return yearly_average

def calculate_objective_weights(objectives: List[Objective]) -> Dict[uuid.UUID, float]:
    """
    Calculate normalized weights for objectives where all weights sum to 1.0.
    
    Args:
        objectives: List of objectives with raw weights
        
    Returns:
        Dictionary mapping objective IDs to normalized weights
    """
    if not objectives:
        return {}
    
    # Extract raw weights
    raw_weights = {obj.id: obj.weight for obj in objectives}
    
    # Calculate sum of all weights
    total_weight = sum(raw_weights.values())
    
    # Normalize weights
    if total_weight == 0:
        # If all weights are zero, distribute evenly
        normalized_weights = {obj_id: 1.0 / len(objectives) for obj_id in raw_weights}
    else:
        # Otherwise normalize to sum to 1.0
        normalized_weights = {obj_id: raw_weight / total_weight 
                             for obj_id, raw_weight in raw_weights.items()}
    
    return normalized_weights

def calculate_weighted_score(scores: Dict[uuid.UUID, float], 
                           weights: Dict[uuid.UUID, float]) -> float:
    """
    Calculate a weighted sum of objective scores.
    
    Args:
        scores: Dictionary mapping objective IDs to scores
        weights: Dictionary mapping objective IDs to weights
        
    Returns:
        Weighted sum score
    """
    # Calculate weighted sum
    weighted_sum = 0.0
    
    for obj_id, score in scores.items():
        if obj_id in weights:
            weighted_sum += score * weights[obj_id]
    
    return weighted_sum

def score_schedules(schedules: List[Schedule], 
                  objectives: List[Objective],
                  normalize: bool = True) -> Dict[uuid.UUID, Dict[uuid.UUID, float]]:
    """
    Calculate scores for multiple schedules against multiple objectives.
    
    Args:
        schedules: List of schedules to evaluate
        objectives: List of objectives to score against
        normalize: Whether to normalize scores across schedules (0-1 scale)
        
    Returns:
        Dictionary mapping schedule IDs to dictionaries mapping objective IDs to scores
    """
    # Calculate raw scores
    scores = {}
    
    for schedule in schedules:
        schedule_scores = {}
        
        for objective in objectives:
            raw_score = score_schedule_for_objective(schedule, objective)
            schedule_scores[objective.id] = raw_score
        
        scores[schedule.id] = schedule_scores
    
    # Normalize scores if requested
    if normalize and schedules:
        # Find min/max for each objective
        min_scores = {}
        max_scores = {}
        
        for objective in objectives:
            obj_scores = [scores[schedule.id][objective.id] for schedule in schedules]
            
            if obj_scores:
                min_scores[objective.id] = min(obj_scores)
                max_scores[objective.id] = max(obj_scores)
            else:
                min_scores[objective.id] = 0.0
                max_scores[objective.id] = 1.0
        
        # Normalize scores
        for schedule in schedules:
            for objective in objectives:
                obj_id = objective.id
                raw_score = scores[schedule.id][obj_id]
                
                # Avoid division by zero
                if max_scores[obj_id] == min_scores[obj_id]:
                    normalized = 1.0 if raw_score > 0 else 0.0
                else:
                    # Scale to 0-1 range
                    normalized = (raw_score - min_scores[obj_id]) / (max_scores[obj_id] - min_scores[obj_id])
                
                scores[schedule.id][obj_id] = normalized
    
    return scores