#!/usr/bin/env python3
"""
Task Models for AAR Auto-Update Protocol
Pydantic models for task management and analysis
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from enum import Enum


class TaskStatus(str, Enum):
    """Task completion status"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    """Task priority levels"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskCategory(str, Enum):
    """Task category types"""

    INFRASTRUCTURE = "infrastructure"
    CLIENT_DELIVERABLE = "client_deliverable"
    DOCUMENTATION = "documentation"
    QUALITY_AUTOMATION = "quality_automation"
    WORKSPACE_MANAGEMENT = "workspace_management"
    PORTFOLIO_MANAGEMENT = "portfolio_management"


class AARNotes(BaseModel):
    """After Action Review notes structure"""

    root_cause: Optional[str] = None
    fix_applied: Optional[str] = None
    validation: Optional[str] = None
    next_steps: Optional[str] = None
    complications: Optional[str] = None
    key_learnings: List[str] = Field(default_factory=list)
    dependencies_unblocked: List[str] = Field(default_factory=list)
    quality_impact: Optional[str] = None


class TaskModel(BaseModel):
    """Core task model for workspace management"""

    id: str = Field(..., description="Task identifier (e.g., '#1', '#2')")
    title: str = Field(..., description="Task title")
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    category: TaskCategory = TaskCategory.WORKSPACE_MANAGEMENT

    # Time tracking
    estimated_minutes: int = Field(..., description="Original time estimate in minutes")
    actual_minutes: Optional[int] = None
    completion_date: Optional[datetime] = None

    # Relationships
    dependencies: List[str] = Field(
        default_factory=list, description="Task IDs this depends on"
    )
    blocks: List[str] = Field(default_factory=list, description="Task IDs this blocks")

    # Content
    description: Optional[str] = None
    goal: Optional[str] = None
    scope: Optional[str] = None
    impact: Optional[str] = None
    prerequisites: List[str] = Field(default_factory=list)

    # Resolution and AAR
    resolution: Optional[str] = None
    aar_notes: Optional[AARNotes] = None
    ai_model_used: Optional[str] = None

    # Metadata
    project: Optional[str] = None
    files_involved: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    @property
    def is_completed(self) -> bool:
        """Check if task is completed"""
        return self.status == TaskStatus.COMPLETED

    @property
    def time_variance_percent(self) -> Optional[float]:
        """Calculate time estimate variance percentage"""
        if self.actual_minutes is None:
            return None
        return (
            (self.actual_minutes - self.estimated_minutes) / self.estimated_minutes
        ) * 100

    @property
    def efficiency_score(self) -> Optional[float]:
        """Calculate efficiency score (lower is better)"""
        if self.actual_minutes is None:
            return None
        return self.actual_minutes / self.estimated_minutes


class WorkspaceMetrics(BaseModel):
    """Workspace-wide task metrics"""

    total_tasks: int
    completed_tasks: int
    pending_tasks: int
    blocked_tasks: int

    total_estimated_hours: float
    total_actual_hours: Optional[float]
    average_completion_rate: Optional[float]

    completion_velocity: Optional[float] = Field(description="Tasks per day")
    time_estimate_accuracy: Optional[float] = Field(
        description="Percentage accuracy of estimates"
    )


class DependencyGraph(BaseModel):
    """Task dependency analysis"""

    task_id: str
    direct_dependencies: List[str]
    transitive_dependencies: List[str]
    blocks_directly: List[str]
    blocks_transitively: List[str]
    critical_path_member: bool = False


class PriorityRecommendation(BaseModel):
    """AI-generated priority recommendation"""

    task_id: str
    current_priority: TaskPriority
    recommended_priority: TaskPriority
    reasoning: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    dependencies_factor: float
    time_factor: float
    impact_factor: float


class WorkspaceSnapshot(BaseModel):
    """Complete workspace state snapshot"""

    timestamp: datetime = Field(default_factory=datetime.now)
    tasks: List[TaskModel]
    metrics: WorkspaceMetrics
    dependency_graph: List[DependencyGraph]
    priority_recommendations: List[PriorityRecommendation]

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
