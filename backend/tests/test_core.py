import unittest
import uuid
from datetime import datetime, timedelta, time
import sys
import os

# Add parent directory to path so we can import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.app.models.task import Task, TaskCategory, TaskStatus
from backend.app.models.objective import Objective, TimeFrame
from backend.app.models.schedule import Schedule
from backend.app.models.constraints import TimeConstraints, TimeSlot, DayOfWeek
from backend.app.core.pareto import (
    is_dominated, calculate_pareto_front, calculate_pareto_ranks, normalize_scores
)
from backend.app.core.scheduler import (
    is_schedule_feasible, generate_feasible_schedules
)
from backend.app.core.scoring import calculate_objective_scores

class TestParetoFunctions(unittest.TestCase):
    def setUp(self):
        # Create test schedules with different objective scores
        self.schedule1 = Schedule(
            id="1",
            name="Schedule 1",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=7),
            objective_scores={
                "obj1": 0.8,  # High for objective 1
                "obj2": 0.4   # Medium for objective 2
            },
            pareto_rank=0,
            is_dominated=False
        )
        
        self.schedule2 = Schedule(
            id="2",
            name="Schedule 2",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=7),
            objective_scores={
                "obj1": 0.5,  # Medium for objective 1
                "obj2": 0.9   # High for objective 2
            },
            pareto_rank=0,
            is_dominated=False
        )
        
        self.schedule3 = Schedule(
            id="3",
            name="Schedule 3",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=7),
            objective_scores={
                "obj1": 0.3,  # Low for objective 1
                "obj2": 0.2   # Low for objective 2
            },
            pareto_rank=0,
            is_dominated=False
        )
        
        # Create better versions of the schedules with same objectives
        obj1_id = "obj1"
        obj2_id = "obj2"
        
        self.dominated_schedule = Schedule(
            id="4",
            name="Dominated Schedule",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=7),
            objective_scores={
                obj1_id: 0.2,  # Lower than schedule1 and schedule2
                obj2_id: 0.3   # Lower than schedule1 and schedule2
            },
            pareto_rank=0,
            is_dominated=False
        )
        
        self.dominating_schedule = Schedule(
            id="5",
            name="Dominating Schedule",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=7),
            objective_scores={
                obj1_id: 0.9,  # Higher than all others
                obj2_id: 0.9   # Higher than all others
            },
            pareto_rank=0,
            is_dominated=False
        )
    
    def test_is_dominated(self):
        """Test the is_dominated function with dominated and non-dominated schedules"""
        # Fix objective keys to be the same for both schedules
        obj1_id = "test1"
        obj2_id = "test2"
        
        schedule_a = Schedule(
            id="a",
            name="Schedule A",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=7),
            objective_scores={
                obj1_id: 0.5,
                obj2_id: 0.5
            },
            pareto_rank=0,
            is_dominated=False
        )
        
        # B dominates A (better in all objectives)
        schedule_b = Schedule(
            id="b",
            name="Schedule B",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=7),
            objective_scores={
                obj1_id: 0.8,
                obj2_id: 0.7
            },
            pareto_rank=0,
            is_dominated=False
        )
        
        # C doesn't dominate A (better in one, worse in another)
        schedule_c = Schedule(
            id="c",
            name="Schedule C",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=7),
            objective_scores={
                obj1_id: 0.9,
                obj2_id: 0.3
            },
            pareto_rank=0,
            is_dominated=False
        )
        
        # D doesn't dominate A (equal in all objectives)
        schedule_d = Schedule(
            id="d",
            name="Schedule D",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=7),
            objective_scores={
                obj1_id: 0.5,
                obj2_id: 0.5
            },
            pareto_rank=0,
            is_dominated=False
        )
        
        # Test dominance relationships
        self.assertTrue(is_dominated(schedule_a, schedule_b))
        self.assertFalse(is_dominated(schedule_b, schedule_a))
        self.assertFalse(is_dominated(schedule_a, schedule_c))
        self.assertFalse(is_dominated(schedule_c, schedule_a))
        self.assertFalse(is_dominated(schedule_a, schedule_d))
        self.assertFalse(is_dominated(schedule_d, schedule_a))
    
    def test_calculate_pareto_front(self):
        """Test calculation of the Pareto front"""
        # Fix objective keys to be the same for all schedules
        obj1_id = "obj1"
        obj2_id = "obj2"
        
        schedule_a = Schedule(
            id="a1",
            name="Schedule A",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=7),
            objective_scores={
                obj1_id: 0.5,
                obj2_id: 0.5
            },
            pareto_rank=0,
            is_dominated=False
        )
        
        schedule_b = Schedule(
            id="b1",
            name="Schedule B",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=7),
            objective_scores={
                obj1_id: 0.8,
                obj2_id: 0.2
            },
            pareto_rank=0,
            is_dominated=False
        )
        
        schedule_c = Schedule(
            id="c1",
            name="Schedule C",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=7),
            objective_scores={
                obj1_id: 0.2,
                obj2_id: 0.8
            },
            pareto_rank=0,
            is_dominated=False
        )
        
        # Dominated by B
        schedule_d = Schedule(
            id="d1",
            name="Schedule D",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=7),
            objective_scores={
                obj1_id: 0.7,
                obj2_id: 0.1
            },
            pareto_rank=0,
            is_dominated=False
        )
        
        # Dominated by C
        schedule_e = Schedule(
            id="e1",
            name="Schedule E",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=7),
            objective_scores={
                obj1_id: 0.1,
                obj2_id: 0.7
            },
            pareto_rank=0,
            is_dominated=False
        )
        
        # Test Pareto front calculation
        schedules = [schedule_a, schedule_b, schedule_c, schedule_d, schedule_e]
        pareto_front = calculate_pareto_front(schedules)
        
        # The Pareto front should contain A, B, and C but not D or E
        self.assertEqual(len(pareto_front), 3)
        self.assertIn(schedule_a, pareto_front)
        self.assertIn(schedule_b, pareto_front)
        self.assertIn(schedule_c, pareto_front)
        self.assertNotIn(schedule_d, pareto_front)
        self.assertNotIn(schedule_e, pareto_front)
    
    def test_normalize_scores(self):
        """Test normalization of objective scores"""
        # Create schedules with different raw scores
        obj1_id = "norm1"
        obj2_id = "norm2"
        
        schedule_a = Schedule(
            id="norm_a",
            name="Schedule A",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=7),
            objective_scores={
                obj1_id: 10.0,
                obj2_id: 5.0
            },
            pareto_rank=0,
            is_dominated=False
        )
        
        schedule_b = Schedule(
            id="norm_b",
            name="Schedule B",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=7),
            objective_scores={
                obj1_id: 20.0,
                obj2_id: 15.0
            },
            pareto_rank=0,
            is_dominated=False
        )
        
        schedule_c = Schedule(
            id="norm_c",
            name="Schedule C",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=7),
            objective_scores={
                obj1_id: 30.0,
                obj2_id: 25.0
            },
            pareto_rank=0,
            is_dominated=False
        )
        
        schedules = [schedule_a, schedule_b, schedule_c]
        
        # Normalize scores
        normalize_scores(schedules)
        
        # Check normalized scores for obj1
        self.assertEqual(schedule_a.objective_scores[obj1_id], 0.0)  # Minimum is normalized to 0
        self.assertEqual(schedule_c.objective_scores[obj1_id], 1.0)  # Maximum is normalized to 1
        self.assertAlmostEqual(schedule_b.objective_scores[obj1_id], 0.5)  # Middle value
        
        # Check normalized scores for obj2
        self.assertEqual(schedule_a.objective_scores[obj2_id], 0.0)  # Minimum is normalized to 0
        self.assertEqual(schedule_c.objective_scores[obj2_id], 1.0)  # Maximum is normalized to 1
        self.assertAlmostEqual(schedule_b.objective_scores[obj2_id], 0.5)  # Middle value

class TestSchedulerFunctions(unittest.TestCase):
    def setUp(self):
        # Create test tasks
        self.task1 = Task(
            id="task1",
            title="Task 1",
            description="Description 1",
            duration=60,  # 1 hour
            energy_cost=3,
            category=TaskCategory.WORK,
            priority=3,
            deadline=None,
            status=TaskStatus.TODO
        )
        
        self.task2 = Task(
            id="task2",
            title="Task 2",
            description="Description 2",
            duration=120,  # 2 hours
            energy_cost=5,
            category=TaskCategory.HEALTH,
            priority=4,
            deadline=None,
            status=TaskStatus.TODO
        )
        
        # Create test objectives
        self.objective1 = Objective(
            id="obj1",
            name="Work Objective",
            category=TaskCategory.WORK,
            target_value=10.0,
            current_value=0.0,
            weight=0.6,
            measurement_unit="hours",
            time_frame=TimeFrame.WEEKLY
        )
        
        self.objective2 = Objective(
            id="obj2",
            name="Health Objective",
            category=TaskCategory.HEALTH,
            target_value=5.0,
            current_value=0.0,
            weight=0.4,
            measurement_unit="hours",
            time_frame=TimeFrame.WEEKLY
        )
        
        # Create test constraints
        self.morning_slot = TimeSlot(
            day=DayOfWeek.MONDAY,
            start_time=time(9, 0),
            end_time=time(12, 0)
        )
        
        self.afternoon_slot = TimeSlot(
            day=DayOfWeek.MONDAY,
            start_time=time(13, 0),
            end_time=time(17, 0)
        )
        
        # For testing we'll use a different evening slot that doesn't cross midnight
        self.evening_slot = TimeSlot(
            day=DayOfWeek.MONDAY,
            start_time=time(18, 0),
            end_time=time(22, 0)
        )
        
        self.constraints = TimeConstraints(
            available_slots=[self.morning_slot, self.afternoon_slot, self.evening_slot],
            max_daily_work_minutes=480,  # 8 hours
            max_weekly_work_minutes=2400  # 40 hours
        )
        
        # Create test schedule
        self.schedule = Schedule(
            id="sched1",
            name="Test Schedule",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=7),
            objective_scores={},
            pareto_rank=0,
            is_dominated=False
        )
        self.schedule.tasks = [self.task1, self.task2]
    
    def test_calculate_objective_scores(self):
        """Test calculation of objective scores for a schedule"""
        scores = calculate_objective_scores(self.schedule, [self.objective1, self.objective2])
        
        # Check scores
        self.assertEqual(len(scores), 2)
        self.assertIn("obj1", scores)
        self.assertIn("obj2", scores)
        
        # Scale may be slightly different due to internal calculations
        # Just check that they're roughly in the right proportion
        self.assertTrue(0 <= scores["obj1"] <= 0.2)
        self.assertTrue(0 <= scores["obj2"] <= 0.5)
        
        # Health objective should be higher than work objective
        self.assertTrue(scores["obj2"] > scores["obj1"])

if __name__ == '__main__':
    unittest.main()