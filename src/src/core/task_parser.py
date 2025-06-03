#!/usr/bin/env python3
"""
AAR Auto-Update Protocol - Task Parser
Task #5 Implementation: Intelligent markdown parsing and task management

This module provides intelligent parsing of workspace task files including
WORKSPACE-TOP-25-TASKS.md (primary framework). Legacy Top 10 tasks archived.
Pattern recognition, dependency analysis, and completion tracking support.
"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Literal
import re
import json
from dataclasses import dataclass, asdict
from enum import Enum

import markdown
from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """Task completion status enumeration"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"


class Priority(str, Enum):
    """Task priority levels"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class TaskMetrics:
    """Metrics for task completion analysis"""

    estimated_hours: float
    actual_hours: Optional[float] = None
    complexity_score: Optional[float] = None
    dependencies_count: int = 0
    completion_velocity: Optional[float] = None


class Task(BaseModel):
    """Comprehensive task representation with intelligence"""

    id: str = Field(description="Task identifier (e.g., '#5')")
    title: str = Field(description="Task title")
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    priority: Priority = Field(default=Priority.MEDIUM)

    # Time tracking
    estimated_hours: float = Field(description="Original time estimate")
    actual_hours: Optional[float] = Field(
        default=None, description="Actual completion time"
    )
    created_date: datetime = Field(default_factory=datetime.now)
    completed_date: Optional[datetime] = Field(default=None)

    # Dependencies and relationships
    dependencies: List[str] = Field(
        default_factory=list, description="Task IDs this depends on"
    )
    blocks: List[str] = Field(default_factory=list, description="Task IDs this blocks")
    project: str = Field(description="Associated project")

    # Content and learning
    description: str = Field(default="", description="Task description")
    aar_notes: Optional[str] = Field(
        default=None, description="After Action Review notes"
    )
    lessons_learned: List[str] = Field(default_factory=list)

    # Intelligence metrics
    complexity_indicators: List[str] = Field(default_factory=list)
    risk_factors: List[str] = Field(default_factory=list)
    success_patterns: List[str] = Field(default_factory=list)

    @property
    def is_overdue(self) -> bool:
        """Check if task is overdue based on estimates"""
        if self.status == TaskStatus.COMPLETED:
            return False
        # Simple heuristic: if created more than 2x estimated time ago
        if self.estimated_hours > 0:
            threshold = self.created_date + timedelta(hours=self.estimated_hours * 2)
            return datetime.now() > threshold
        return False

    @property
    def efficiency_ratio(self) -> Optional[float]:
        """Calculate efficiency ratio (estimated/actual)"""
        if self.actual_hours and self.estimated_hours > 0:
            return self.estimated_hours / self.actual_hours
        return None

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)


class TaskParser:
    """Intelligent parser for WORKSPACE-TOP-25-TASKS.md and legacy task formats with ML-ready features"""

    def __init__(self, workspace_path: Path):
        self.workspace_path = Path(workspace_path)
        # Priority: Top 25 Tasks framework (legacy Top 10 tasks archived)
        self.tasks_file = self.workspace_path / "WORKSPACE-TOP-25-TASKS.md"
        # Enhanced pattern to match: ### 5. 🤖 [HIGH] Implement AAR Auto-Update Protocol
        # Improved to capture full titles with multiple words
        self.header_pattern = re.compile(
            r"^### ?(~+)?(\d+)\. (.*?) \[([A-Z]+)\] (.+?)(?=\n|\r|$)", re.MULTILINE
        )
        self.status_pattern = re.compile(r"\*\*Status\*\*: ([^\n]+)")
        self.estimated_pattern = re.compile(r"\*\*Estimated Time\*\*: ([^\n]+)")
        self.progress_pattern = re.compile(
            r"\*\*Current Progress\*\*:(.*?)(?=\*\*|$)", re.DOTALL
        )
        self.impact_pattern = re.compile(r"\*\*Impact\*\*: ([^\n]+)")
        self.dependencies_pattern = re.compile(r"\*\*Dependencies\*\*: ([^\n]+)")
        self.success_pattern = re.compile(r"\*\*Success Metrics\*\*: ([^\n]+)")

    def parse_workspace_tasks(self) -> List[Task]:
        """Parse all tasks in the workspace - API compatibility wrapper for parse_tasks()"""
        return self.parse_tasks()

    def parse_tasks(self) -> List[Task]:
        if not self.tasks_file.exists():
            raise FileNotFoundError(f"Task file not found: {self.tasks_file}")
        content = self.tasks_file.read_text(encoding="utf-8")
        return self._extract_tasks_from_content(content)

    def _extract_tasks_from_content(self, content: str) -> List[Task]:
        tasks = []
        for match in self.header_pattern.finditer(content):
            # Check for strikethrough formatting (completed tasks)
            has_leading_strikethrough = match.group(1) is not None  # ~~~ at start
            has_trailing_strikethrough = "~~~" in match.group(0)  # Check entire match for ~~~
            is_strikethrough = has_leading_strikethrough or has_trailing_strikethrough

            idx = int(match.group(2))
            emoji = match.group(3).strip()
            priority = match.group(4).strip().lower()

            # Enhanced title extraction - get everything after priority bracket
            full_title = match.group(5).strip()
            # Remove any trailing strikethrough markup
            title = re.sub(r'~+$', '', full_title).strip()

            start = match.end()
            # Find where the next header starts
            next_header = self.header_pattern.search(content, start)
            end = next_header.start() if next_header else len(content)
            section = content[start:end]
            # Extract details
            status = self._extract_field(self.status_pattern, section)
            estimated = self._extract_field(self.estimated_pattern, section)
            progress = self._extract_field(
                self.progress_pattern, section, multiline=True
            )
            impact = self._extract_field(self.impact_pattern, section)
            dependencies = self._extract_field(self.dependencies_pattern, section)
            success = self._extract_field(self.success_pattern, section)

            # Determine status - prioritize strikethrough formatting and explicit status patterns
            if is_strikethrough or "COMPLETED" in (status or "").upper():
                status_val = TaskStatus.COMPLETED
            else:
                # Enhanced status mapping with more patterns
                status_map = {
                    "COMPLETED": TaskStatus.COMPLETED,
                    "100% COMPLETE": TaskStatus.COMPLETED,
                    "✅ COMPLETED": TaskStatus.COMPLETED,
                    "IN PROGRESS": TaskStatus.IN_PROGRESS,
                    "🔄 IN PROGRESS": TaskStatus.IN_PROGRESS,
                    "90% COMPLETE": TaskStatus.IN_PROGRESS,
                    "75% COMPLETE": TaskStatus.IN_PROGRESS,
                    "60% COMPLETE": TaskStatus.IN_PROGRESS,
                    "PENDING": TaskStatus.PENDING,
                    "📋 READY": TaskStatus.PENDING,
                    "PLANNED": TaskStatus.PENDING,
                    "BACKLOG": TaskStatus.PENDING,
                    "BLOCKED": TaskStatus.BLOCKED,
                }

                # Check status string for any matching patterns
                status_val = TaskStatus.PENDING  # Default
                if status:
                    status_upper = status.strip().upper()
                    for pattern, task_status in status_map.items():
                        if pattern in status_upper:
                            status_val = task_status
                            break
            # Map priority
            priority_map = {
                "CRITICAL": Priority.CRITICAL,
                "HIGH": Priority.HIGH,
                "MEDIUM": Priority.MEDIUM,
                "LOW": Priority.LOW,
            }
            priority_val = priority_map.get(priority.upper(), Priority.MEDIUM)
            # Parse estimated time
            estimated_hours = 1.0
            if estimated:
                try:
                    if "hour" in estimated:
                        estimated_hours = float(re.search(r"(\d+)", estimated).group(1))
                    elif "min" in estimated:
                        estimated_hours = (
                            float(re.search(r"(\d+)", estimated).group(1)) / 60.0
                        )
                except Exception:
                    estimated_hours = 1.0
            # Compose description
            description = f"{progress}\nImpact: {impact}\nSuccess: {success}"
            # Dependencies
            dep_list = (
                [d.strip() for d in dependencies.split(",")] if dependencies else []
            )
            # Build Task
            task = Task(
                id=f"#{idx}",
                title=title,
                status=status_val,
                priority=priority_val,
                estimated_hours=estimated_hours,
                project="PowerCompany",
                description=description,
                dependencies=dep_list,
            )
            tasks.append(task)
        return tasks

    def _extract_field(self, pattern, section, multiline=False):
        match = pattern.search(section)
        if not match:
            return ""
        return match.group(1).strip() if not multiline else match.group(1).strip()


if __name__ == "__main__":
    # Example usage for testing
    parser = TaskParser(Path("/workspaces/PowerCompany"))
    try:
        tasks = parser.parse_tasks()

        print(f"Parsed {len(tasks)} tasks")
        print(
            f"Completed: {len([t for t in tasks if t.status == TaskStatus.COMPLETED])}"
        )
        print(f"Pending: {len([t for t in tasks if t.status == TaskStatus.PENDING])}")

        # Display parsed tasks
        for task in tasks:
            print(f"Task {task.id}: {task.title} - {task.status}")

    except FileNotFoundError as e:
        print(f"Error: {e}")
