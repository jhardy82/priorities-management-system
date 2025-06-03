"""
Priorities Management System - Core Package
Enterprise task management and prioritization engine
"""

from .config_manager import ConfigManager, PrioritiesConfig, config_manager
from .task_models import (
    TaskModel,
    TaskPriority,
    TaskStatus,
    TaskCategory,
    PriorityRecommendation,
    DependencyGraph,
)
from .priority_engine_standalone import PriorityEngine, PriorityScore, PriorityFactor
from .task_interface import UniversalTaskInterface, MarkdownTaskAdapter, JSONTaskAdapter

__version__ = "1.0.0"
__author__ = "Avanade Modern Workplace Engineering"

__all__ = [
    "ConfigManager",
    "PrioritiesConfig",
    "config_manager",
    "TaskModel",
    "TaskPriority",
    "TaskStatus",
    "TaskCategory",
    "PriorityRecommendation",
    "DependencyGraph",
    "PriorityEngine",
    "PriorityScore",
    "PriorityFactor",
    "UniversalTaskInterface",
    "MarkdownTaskAdapter",
    "JSONTaskAdapter",
]
