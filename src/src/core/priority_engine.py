#!/usr/bin/env python3
"""
AAR Auto-Update Protocol - Priority Engine
Task #5 Implementation: Intelligent priority ranking and dependency analysis

This module provides ML-powered priority analysis, dependency resolution,
and smart re-ranking based on completion patterns and workspace dynamics.
"""

from typing import List, Optional
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
from .config_manager import config_manager


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
            self.priority_weights = {
                PriorityFactor.CRITICAL_PATH: config.priority_engine.base_weights.get(
                    "dependency", 0.3
                ),
                PriorityFactor.DEPENDENCY_BLOCKER: config.priority_engine.base_weights.get(
                    "dependency", 0.25
                ),
                PriorityFactor.CLIENT_IMPACT: config.priority_engine.base_weights.get(
                    "impact", 0.2
                ),
                PriorityFactor.INFRASTRUCTURE_FOUNDATION: config.priority_engine.base_weights.get(
                    "impact", 0.15
                ),
                PriorityFactor.TIME_SENSITIVITY: config.priority_engine.base_weights.get(
                    "time_sensitivity", 0.1
                ),
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
        """API compatibility wrapper for analyze_priorities() - returns tasks with updated priorities"""
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
                recommendations.append(
                    PriorityRecommendation(
                        task_id=score.task_id,
                        current_priority=current_task.priority,
                        recommended_priority=recommended_priority,
                        reasoning="; ".join(score.reasoning),
                        confidence_score=self._calculate_confidence(score),
                        dependencies_factor=score.dependency_factor,
                        time_factor=score.time_factor,
                        impact_factor=score.impact_factor,
                    )
                )
        return sorted(recommendations, key=lambda r: r.confidence_score, reverse=True)

    def _build_dependency_graph(self, tasks: List[TaskModel]) -> None:
        """Builds a directed graph of task dependencies for analysis."""
        self.dependency_graph.clear()
        for task in tasks:
            self.dependency_graph.add_node(task.id, task=task)
        for task in tasks:
            for dep_id in getattr(task, "dependencies", []):
                if self.dependency_graph.has_node(dep_id):
                    self.dependency_graph.add_edge(dep_id, task.id)

    def _calculate_priority_scores(self, tasks: List[TaskModel]) -> List[PriorityScore]:
        """Scores each task using hybrid factors. Skips completed tasks."""
        scores = []
        for task in tasks:
            if getattr(task, "status", None) == TaskStatus.COMPLETED:
                continue
            score = self._calculate_single_task_score(task, tasks)
            scores.append(score)
        return sorted(scores, key=lambda s: s.final_score, reverse=True)

    def _calculate_single_task_score(
        self, task: TaskModel, all_tasks: List[TaskModel]
    ) -> PriorityScore:
        """Scores a single task using base, dependency, time, impact, and velocity factors."""
        reasoning = []
        # Base priority score (from enum)
        base_score = self._priority_to_score(
            getattr(task, "priority", TaskPriority.MEDIUM)
        )
        # Dependency factor: higher if task blocks many others
        blocked_tasks = list(self.dependency_graph.successors(task.id))
        dependency_factor = min(len(blocked_tasks) * 0.2, 1.0)
        if blocked_tasks:
            reasoning.append(f"Blocks {len(blocked_tasks)} other tasks")
        # Critical path analysis
        if self._is_on_critical_path(task.id):
            dependency_factor += 0.3
            reasoning.append("On critical path")
        # Time sensitivity factor (use estimated_minutes if available, else fallback)
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

    def _is_on_critical_path(self, task_id: str) -> bool:
        """Determine if task is on the critical path (no dependencies or many dependents)."""
        try:
            if self.dependency_graph.has_node(task_id):
                predecessors = list(self.dependency_graph.predecessors(task_id))
                successors = list(self.dependency_graph.successors(task_id))
                return len(predecessors) == 0 or len(successors) >= 2
        except Exception:
            pass
        return False

    def _calculate_time_sensitivity(self, estimated_minutes: Optional[float]) -> float:
        """Calculate time sensitivity factor based on estimated minutes."""
        if estimated_minutes is None:
            return 0.5  # Default if missing
        estimated_days = estimated_minutes / (8 * 60)  # 8-hour workdays
        if estimated_days <= 0.25:
            return 0.9
        elif estimated_days <= 1:
            return 0.7
        elif estimated_days <= 3:
            return 0.5
        else:
            return 0.3

    def _calculate_impact_factor(self, task: TaskModel) -> float:
        """Calculate impact factor based on project and content keywords."""
        impact_score = 0.5
        if getattr(task, "project", None) and "client" in task.project.lower():
            impact_score += 0.3
        if getattr(task, "project", None) and "infrastructure" in task.project.lower():
            impact_score += 0.2
        high_impact_keywords = [
            "critical",
            "blocker",
            "foundation",
            "pipeline",
            "deployment",
            "production",
            "automation",
        ]
        content = (
            f"{getattr(task, 'title', '')} {getattr(task, 'description', '')}".lower()
        )
        for keyword in high_impact_keywords:
            if keyword in content:
                impact_score += 0.1
        return min(impact_score, 1.0)

    def _calculate_velocity_factor(self, task: TaskModel) -> float:
        """Placeholder for future ML-based velocity prediction."""
        return 0.5

    def _calculate_confidence(self, score: PriorityScore) -> float:
        """Calculate confidence in priority recommendation."""
        base_confidence = 0.7
        if len(score.reasoning) >= 3:
            base_confidence += 0.2
        if score.dependency_factor > 0.5:
            base_confidence += 0.1
        return min(base_confidence, 1.0)

    def generate_dependency_analysis(
        self, tasks: List[TaskModel]
    ) -> List[DependencyGraph]:
        """Generate comprehensive dependency analysis for all tasks."""
        self._build_dependency_graph(tasks)
        analysis = []
        for task in tasks:
            if getattr(task, "status", None) != TaskStatus.COMPLETED:
                deps = DependencyGraph(
                    task_id=task.id,
                    direct_dependencies=getattr(task, "dependencies", []),
                    transitive_dependencies=self._get_transitive_dependencies(task.id),
                    blocks_directly=list(self.dependency_graph.successors(task.id)),
                    blocks_transitively=self._get_transitive_blocks(task.id),
                    critical_path_member=self._is_on_critical_path(task.id),
                )
                analysis.append(deps)
        return analysis

    def _get_transitive_dependencies(self, task_id: str) -> List[str]:
        """Get all transitive dependencies for a task."""
        if not self.dependency_graph.has_node(task_id):
            return []
        try:
            ancestors = nx.ancestors(self.dependency_graph, task_id)
            return list(ancestors)
        except Exception:
            return []

    def _get_transitive_blocks(self, task_id: str) -> List[str]:
        """Get all tasks transitively blocked by this task."""
        if not self.dependency_graph.has_node(task_id):
            return []
        try:
            descendants = nx.descendants(self.dependency_graph, task_id)
            return list(descendants)
        except Exception:
            return []
