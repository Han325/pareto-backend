from typing import List, Dict, Set, Tuple
import uuid
from ..models.schedule import Schedule

def is_dominated(schedule_a: Schedule, schedule_b: Schedule) -> bool:
    """
    Check if schedule_a is dominated by schedule_b.
    A schedule is dominated if another schedule has better or equal scores for all objectives,
    and strictly better score for at least one objective.
    
    Args:
        schedule_a: First schedule to compare
        schedule_b: Second schedule to compare
        
    Returns:
        True if schedule_a is dominated by schedule_b, False otherwise
    """
    # Extract objective scores for each schedule
    scores_a = schedule_a.objective_scores
    scores_b = schedule_b.objective_scores
    
    # Both schedules must have the same objectives to compare
    if set(scores_a.keys()) != set(scores_b.keys()):
        raise ValueError("Schedules must have the same objectives to compare dominance")
    
    # Check if schedule_b dominates schedule_a
    # 1. schedule_b must be at least as good as schedule_a for all objectives
    # 2. schedule_b must be strictly better than schedule_a for at least one objective
    at_least_one_better = False
    
    for obj_id, score_a in scores_a.items():
        score_b = scores_b[obj_id]
        
        # If schedule_a has a better score for any objective, it's not dominated
        if score_a > score_b:
            return False
        
        # Check if schedule_b is strictly better for this objective
        if score_b > score_a:
            at_least_one_better = True
    
    # If we got here, schedule_b is at least as good as schedule_a for all objectives
    # Return True only if schedule_b is strictly better for at least one objective
    return at_least_one_better

def is_dominated_by_any(schedule: Schedule, other_schedules: List[Schedule]) -> bool:
    """
    Check if a schedule is dominated by any schedule in a list.
    
    Args:
        schedule: Schedule to check
        other_schedules: List of schedules to compare against
        
    Returns:
        True if the schedule is dominated by any schedule in the list, False otherwise
    """
    return any(is_dominated(schedule, other) for other in other_schedules)

def calculate_pareto_front(schedules: List[Schedule]) -> List[Schedule]:
    """
    Calculate the Pareto-optimal set of schedules.
    
    A schedule is Pareto-optimal if no other schedule dominates it.
    
    Args:
        schedules: List of schedules to analyze
        
    Returns:
        List of schedules that form the Pareto front
        
    pre: len(schedules) > 0
    post: all([not is_dominated(s, other_s) for s in __return__ for other_s in __return__ if s != other_s])
    post: len(__return__) <= len(schedules)
    post: all([s in schedules for s in __return__])
    """
    if not schedules:
        raise ValueError("Cannot calculate Pareto front of empty schedule list")
    
    pareto_front = []
    
    # First pass: find all non-dominated schedules
    for i, schedule in enumerate(schedules):
        # Check if this schedule is dominated by any other schedule
        is_dominated_flag = False
        
        for j, other_schedule in enumerate(schedules):
            if i == j:  # Skip comparing to itself
                continue
                
            if is_dominated(schedule, other_schedule):
                is_dominated_flag = True
                break
        
        # If not dominated by any other schedule, add to Pareto front
        if not is_dominated_flag:
            # Update the schedule state
            schedule.is_dominated = False
            schedule.pareto_rank = 0
            pareto_front.append(schedule)
        else:
            # Update the schedule state
            schedule.is_dominated = True
    
    return pareto_front

def calculate_pareto_ranks(schedules: List[Schedule]) -> Dict[int, List[Schedule]]:
    """
    Calculate Pareto ranks for all schedules.
    
    Rank 0 is the Pareto front. Rank 1 is the Pareto front of the remaining schedules
    after removing rank 0, and so on.
    
    Args:
        schedules: List of schedules to rank
        
    Returns:
        Dictionary mapping ranks to lists of schedules at that rank
    """
    if not schedules:
        return {}
    
    # Make a copy to avoid modifying the input
    remaining = schedules.copy()
    ranks = {}
    rank = 0
    
    # Calculate each Pareto front and remove it from consideration
    while remaining:
        # Calculate current Pareto front
        front = calculate_pareto_front(remaining)
        
        # Set rank for these schedules
        for schedule in front:
            schedule.pareto_rank = rank
        
        # Store this front
        ranks[rank] = front
        
        # Remove these from consideration for the next rank
        remaining = [s for s in remaining if s not in front]
        
        # Move to next rank
        rank += 1
    
    return ranks

# Utility function to get normalized scores (0-1 scale)
def normalize_scores(schedules: List[Schedule]) -> None:
    """
    Normalize all objective scores to 0-1 scale across schedules.
    
    This in-place operation modifies the objective_scores of each schedule.
    
    Args:
        schedules: List of schedules to normalize
    """
    if not schedules:
        return
    
    # First, find all unique objective IDs
    all_objectives = set()
    for schedule in schedules:
        all_objectives.update(schedule.objective_scores.keys())
    
    # For each objective, find min and max values
    for obj_id in all_objectives:
        scores = [schedule.objective_scores.get(obj_id, 0) for schedule in schedules]
        min_score = min(scores)
        max_score = max(scores)
        
        # Avoid division by zero if all scores are the same
        if max_score == min_score:
            # If all the same, set to 1.0 (perfect score)
            for schedule in schedules:
                if obj_id in schedule.objective_scores:
                    schedule.objective_scores[obj_id] = 1.0
        else:
            # Normalize to 0-1 scale
            range_score = max_score - min_score
            for schedule in schedules:
                if obj_id in schedule.objective_scores:
                    normalized = (schedule.objective_scores[obj_id] - min_score) / range_score
                    schedule.objective_scores[obj_id] = normalized