#!/usr/bin/env python3
"""
Priority Engine for Priorities Management System
Intelligent priority ranking and dependency analysis

This module provides ML-powered priority analysis, dependency resolution,
and smart re-ranking based on completion patterns and workspace dynamics.
"""

from typing import List, Optional, Dict, Any
import networkx as nx
from dataclasses import dataclass
from enum import Enum

from .task_models import (
    TaskModel,
    TaskPriority,
    TaskStatus,
    DependencyGraph,
    PriorityRecommendation,
)

try:
    from .config_manager import config_manager
except ImportError:
    # Fallback for standalone use
    config_manager = None


class PriorityFactor(Enum):
    """Factors influencing task priority calculation"""

    CRITICAL_PATH = "critical_path"
    DEPENDENCY_BLOCKER = "dependency_blocker"
    CLIENT_IMPACT = "client_impact"
    INFRASTRUCTURE_FOUNDATION = "infrastructure_foundation"
    TIME_SENSITIVITY = "time_sensitivity"
    COMPLETION_VELOCITY = "completion_velocity"
    RISK_MITIGATION = "risk_mitigation"


@dataclass
class PriorityScore:
    """Comprehensive priority scoring"""

    task_id: str
    base_priority: float
    dependency_factor: float
    time_factor: float
    impact_factor: float
    velocity_factor: float
    final_score: float
    reasoning: List[str]


class PriorityEngine:
    """Intelligent priority analysis and recommendation engine

    This engine uses a hybrid scoring system:
    - Dependency analysis (critical path, blockers)
    - Time sensitivity (estimated time to complete)
    - Impact assessment (client/infrastructure/keywords)
    - Velocity (future ML placeholder)

    Teaching comments are included for maintainability and onboarding.
    """

    def __init__(self, config=None):
        self.dependency_graph = nx.DiGraph()
        self.completion_history = []  # List[Dict] for future ML/analytics

        # Load configuration
        if config is None:
            try:
                config = config_manager.config
            except Exception:
                # Use default configuration if none available
                config = None

        # Priority weights can be tuned via configuration
        if config and hasattr(config, "priority_engine"):
            weights = config.priority_engine.base_weights
            self.priority_weights = {
                PriorityFactor.CRITICAL_PATH: weights.get("dependency", 0.3),
                PriorityFactor.DEPENDENCY_BLOCKER: weights.get("dependency", 0.25),
                PriorityFactor.CLIENT_IMPACT: weights.get("impact", 0.2),
                PriorityFactor.INFRASTRUCTURE_FOUNDATION: weights.get("impact", 0.15),
                PriorityFactor.TIME_SENSITIVITY: weights.get("time_sensitivity", 0.1),
            }
            self.critical_path_multiplier = (
                config.priority_engine.critical_path_multiplier
            )
            self.blocker_penalty_multiplier = (
                config.priority_engine.blocker_penalty_multiplier
            )
        else:
            # Default weights for standalone use
            self.priority_weights = {
                PriorityFactor.CRITICAL_PATH: 0.3,
                PriorityFactor.DEPENDENCY_BLOCKER: 0.25,
                PriorityFactor.CLIENT_IMPACT: 0.2,
                PriorityFactor.INFRASTRUCTURE_FOUNDATION: 0.15,
                PriorityFactor.TIME_SENSITIVITY: 0.1,
            }
            self.critical_path_multiplier = 1.5
            self.blocker_penalty_multiplier = 2.0

    def calculate_priorities(self, tasks: List[TaskModel]) -> List[TaskModel]:
        """API compatibility wrapper for analyze_priorities()

        Returns tasks with updated priorities
        """
        recommendations = self.analyze_priorities(tasks)

        # Apply recommendations to tasks and return the updated list
        if recommendations:
            for rec in recommendations:
                task = next((t for t in tasks if t.id == rec.task_id), None)
                if task:
                    task.priority = rec.recommended_priority

        return sorted(
            tasks,
            key=lambda t: getattr(t, "priority", TaskPriority.MEDIUM).value,
            reverse=True,
        )

    def analyze_priorities(
        self, tasks: List[TaskModel]
    ) -> List[PriorityRecommendation]:
        """Generate intelligent priority recommendations

        - Builds dependency graph
        - Scores each task using hybrid factors
        - Returns recommendations for priority changes
        """
        self._build_dependency_graph(tasks)
        priority_scores = self._calculate_priority_scores(tasks)
        recommendations = []

        for score in priority_scores:
            current_task = next(t for t in tasks if t.id == score.task_id)
            recommended_priority = self._score_to_priority(score.final_score)

            if recommended_priority != current_task.priority:
                # Convert reasoning list to string
                reasoning_text = (
                    "; ".join(score.reasoning)
                    if isinstance(score.reasoning, list)
                    else str(score.reasoning)
                )

                recommendations.append(
                    PriorityRecommendation(
                        task_id=score.task_id,
                        current_priority=current_task.priority,
                        recommended_priority=recommended_priority,
                        reasoning=reasoning_text,
                        confidence_score=self._calculate_confidence(score),
                        dependencies_factor=score.dependency_factor,
                        time_factor=score.time_factor,
                        impact_factor=score.impact_factor,
                    )
                )

        return recommendations

    def _calculate_priority_scores(self, tasks: List[TaskModel]) -> List[PriorityScore]:
        """Scores each task using hybrid factors. Skips completed tasks."""
        scores = []
        active_tasks = [t for t in tasks if t.status != TaskStatus.COMPLETED]

        for task in active_tasks:
            score = self._calculate_task_score(task, active_tasks)
            scores.append(score)

        return scores

    def _calculate_task_score(
        self, task: TaskModel, all_tasks: List[TaskModel]
    ) -> PriorityScore:
        """Calculate comprehensive priority score for a single task"""
        reasoning = []

        # Base priority score
        base_score = self._priority_to_score(task.priority)

        # Dependency factor
        dependency_factor = base_score
        blocked_tasks = [
            t for t in all_tasks if t.id in self.dependency_graph.successors(task.id)
        ]
        if blocked_tasks:
            dependency_factor += 0.2
            reasoning.append(f"Blocks {len(blocked_tasks)} other tasks")

        if self._is_on_critical_path(task.id):
            dependency_factor += 0.3
            reasoning.append("On critical path")

        # Time sensitivity factor
        est_minutes = getattr(task, "estimated_minutes", None)
        if est_minutes is None and hasattr(task, "estimated_hours"):
            est_minutes = getattr(task, "estimated_hours", 1.0) * 60

        time_factor = self._calculate_time_sensitivity(est_minutes)
        if time_factor > 0.5:
            reasoning.append("Time-sensitive due to estimates")

        # Impact factor based on project and content
        impact_factor = self._calculate_impact_factor(task)
        if impact_factor > 0.7:
            reasoning.append("High impact on client/infrastructure")

        # Velocity factor: placeholder for future ML
        velocity_factor = self._calculate_velocity_factor(task)

        # Weighted final score
        final_score = (
            base_score * 0.3
            + dependency_factor * 0.3
            + time_factor * 0.2
            + impact_factor * 0.2
        )

        return PriorityScore(
            task_id=task.id,
            base_priority=base_score,
            dependency_factor=dependency_factor,
            time_factor=time_factor,
            impact_factor=impact_factor,
            velocity_factor=velocity_factor,
            final_score=final_score,
            reasoning=reasoning,
        )

    def _priority_to_score(self, priority: TaskPriority) -> float:
        """Convert priority enum to numerical score."""
        priority_map = {
            TaskPriority.CRITICAL: 1.0,
            TaskPriority.HIGH: 0.8,
            TaskPriority.MEDIUM: 0.6,
            TaskPriority.LOW: 0.4,
        }
        return priority_map.get(priority, 0.6)

    def _score_to_priority(self, score: float) -> TaskPriority:
        """Convert numerical score back to priority enum."""
        if score >= 0.9:
            return TaskPriority.CRITICAL
        elif score >= 0.7:
            return TaskPriority.HIGH
        elif score >= 0.5:
            return TaskPriority.MEDIUM
        else:
            return TaskPriority.LOW

    def _build_dependency_graph(self, tasks: List[TaskModel]) -> None:
        """Build networkx graph from task dependencies"""
        self.dependency_graph.clear()

        for task in tasks:
            self.dependency_graph.add_node(task.id)
            if hasattr(task, "dependencies") and task.dependencies:
                for dep_id in task.dependencies:
                    self.dependency_graph.add_edge(dep_id, task.id)

    def _is_on_critical_path(self, task_id: str) -> bool:
        """Check if task is on the critical path"""
        try:
            # Simple heuristic: tasks with many successors
            successors = list(self.dependency_graph.successors(task_id))
            return len(successors) >= 2
        except Exception:
            return False

    def _calculate_time_sensitivity(self, est_minutes: Optional[float]) -> float:
        """Calculate time sensitivity factor based on estimated minutes."""
        if est_minutes is None:
            return 0.5  # Default medium sensitivity

        # Shorter tasks get higher time sensitivity
        if est_minutes <= 30:
            return 0.8  # Quick wins
        elif est_minutes <= 120:
            return 0.6  # Medium tasks
        else:
            return 0.3  # Long tasks

    def _calculate_impact_factor(self, task: TaskModel) -> float:
        """Calculate impact factor based on task content and category"""
        impact_score = 0.5  # Base impact

        # Check for high-impact keywords
        content = f"{task.title} {getattr(task, 'description', '')}"
        high_impact_keywords = [
            "client",
            "customer",
            "production",
            "critical",
            "urgent",
            "infrastructure",
            "security",
            "compliance",
            "deadline",
            "blocker",
            "dependency",
            "foundation",
            "platform",
        ]

        for keyword in high_impact_keywords:
            if keyword.lower() in content.lower():
                impact_score += 0.1

        # Category-based adjustments
        if hasattr(task, "category"):
            if task.category in ["INFRASTRUCTURE", "CLIENT_DELIVERABLE"]:
                impact_score += 0.2

        return min(impact_score, 1.0)  # Cap at 1.0

    def _calculate_velocity_factor(self, task: TaskModel) -> float:
        """Calculate velocity factor (placeholder for ML implementation)"""
        # Future: analyze historical completion patterns
        return 0.5  # Neutral for now

    def _calculate_confidence(self, score: PriorityScore) -> float:
        """Calculate confidence in the priority recommendation"""
        # More reasoning = higher confidence
        base_confidence = min(len(score.reasoning) * 0.2, 0.8)

        # High score differences = higher confidence
        score_variance = abs(score.final_score - score.base_priority)
        confidence_boost = min(score_variance, 0.2)

        return min(base_confidence + confidence_boost, 1.0)

    def generate_dependency_analysis(
        self, tasks: List[TaskModel]
    ) -> List[DependencyGraph]:
        """Generate comprehensive dependency analysis for all tasks."""
        self._build_dependency_graph(tasks)

        dependency_analyses = []
        for task in tasks:
            task_id = task.id
            try:
                # Get direct successors and predecessors
                direct_blocks = list(self.dependency_graph.successors(task_id))
                direct_deps = list(self.dependency_graph.predecessors(task_id))

                # Get transitive dependencies
                descendants = nx.descendants(self.dependency_graph, task_id)
                ancestors = nx.ancestors(self.dependency_graph, task_id)

                dependency_analyses.append(
                    DependencyGraph(
                        task_id=task_id,
                        direct_dependencies=direct_deps,
                        transitive_dependencies=list(ancestors),
                        blocks_directly=direct_blocks,
                        blocks_transitively=list(descendants),
                        critical_path_member=self._is_on_critical_path(task_id),
                    )
                )
            except Exception:
                # Handle graph errors gracefully
                dependency_analyses.append(
                    DependencyGraph(
                        task_id=task_id,
                        direct_dependencies=[],
                        transitive_dependencies=[],
                        blocks_directly=[],
                        blocks_transitively=[],
                        critical_path_member=False,
                    )
                )

        return dependency_analyses
