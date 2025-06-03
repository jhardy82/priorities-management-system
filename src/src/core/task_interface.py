#!/usr/bin/env python3
"""
Universal Task Interface for Priorities Management System
Provides adapters and interfaces for different task data sources
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
import json
import yaml
import csv
import re
from datetime import datetime

from .task_models import TaskModel, TaskPriority, TaskStatus, TaskCategory
from .config_manager import config_manager


class TaskSourceAdapter(ABC):
    """Abstract base class for task source adapters"""

    @abstractmethod
    def load_tasks(self, source_path: str) -> List[TaskModel]:
        """Load tasks from the specified source"""
        pass

    @abstractmethod
    def save_tasks(self, tasks: List[TaskModel], target_path: str) -> bool:
        """Save tasks to the specified target"""
        pass

    @abstractmethod
    def validate_source(self, source_path: str) -> bool:
        """Validate that the source is readable by this adapter"""
        pass


class MarkdownTaskAdapter(TaskSourceAdapter):
    """Adapter for markdown-formatted task files"""

    def __init__(self):
        # Common markdown task patterns
        self.task_patterns = [
            r"^[-*+]\s*\[([ x])\]\s*(.*?)(?:\s*\[([^\]]+)\])?$",  # GitHub style
            r"^(\d+)\.\s*(.*?)(?:\s*-\s*([^-]+))?$",  # Numbered lists
            r"^##?\s*(.*?)(?:\s*-\s*([^-]+))?$",  # Headers as tasks
        ]

        self.priority_keywords = {
            "critical": TaskPriority.CRITICAL,
            "urgent": TaskPriority.CRITICAL,
            "high": TaskPriority.HIGH,
            "important": TaskPriority.HIGH,
            "medium": TaskPriority.MEDIUM,
            "normal": TaskPriority.MEDIUM,
            "low": TaskPriority.LOW,
            "minor": TaskPriority.LOW,
        }

    def load_tasks(self, source_path: str) -> List[TaskModel]:
        """Load tasks from markdown file"""
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                content = f.read()

            tasks = []
            lines = content.split("\n")

            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if not line:
                    continue

                task = self._parse_markdown_line(line, line_num, source_path)
                if task:
                    tasks.append(task)

            return tasks

        except Exception as e:
            print(f"Error loading markdown tasks from {source_path}: {e}")
            return []

    def _parse_markdown_line(
        self, line: str, line_num: int, source_path: str
    ) -> Optional[TaskModel]:
        """Parse a single markdown line into a task"""
        for pattern in self.task_patterns:
            match = re.match(pattern, line, re.IGNORECASE)
            if match:
                return self._create_task_from_match(match, line, line_num, source_path)

        return None

    def _create_task_from_match(
        self, match, line: str, line_num: int, source_path: str
    ) -> TaskModel:
        """Create TaskModel from regex match"""
        groups = match.groups()

        # Extract task details
        if len(groups) >= 2:
            status_indicator = groups[0] if groups[0] else ""
            title = groups[1].strip() if groups[1] else line.strip()
            metadata = groups[2].strip() if len(groups) > 2 and groups[2] else ""
        else:
            status_indicator = ""
            title = groups[0].strip() if groups and groups[0] else line.strip()
            metadata = ""

        # Determine status
        status = TaskStatus.PENDING
        if status_indicator:
            if status_indicator.lower() in ["x", "done", "completed"]:
                status = TaskStatus.COMPLETED
            elif status_indicator.lower() in ["~", "progress", "wip"]:
                status = TaskStatus.IN_PROGRESS
            elif status_indicator.lower() in ["!", "blocked"]:
                status = TaskStatus.BLOCKED

        # Extract priority from title and metadata
        priority = self._extract_priority(f"{title} {metadata}")

        # Extract category
        category = self._extract_category(f"{title} {metadata}")

        # Extract time estimates
        estimated_minutes = self._extract_time_estimate(f"{title} {metadata}")

        # Generate unique ID
        task_id = f"{Path(source_path).stem}_{line_num}_{hash(title) % 10000}"

        return TaskModel(
            id=task_id,
            title=title,
            description=metadata,
            status=status,
            priority=priority,
            category=category,
            estimated_minutes=estimated_minutes,
            source_file=source_path,
            source_line=line_num,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

    def _extract_priority(self, text: str) -> TaskPriority:
        """Extract priority from text using keywords"""
        text_lower = text.lower()
        for keyword, priority in self.priority_keywords.items():
            if keyword in text_lower:
                return priority
        return TaskPriority.MEDIUM

    def _extract_category(self, text: str) -> TaskCategory:
        """Extract category from text using keywords"""
        text_lower = text.lower()

        category_keywords = {
            "infrastructure": TaskCategory.INFRASTRUCTURE,
            "client": TaskCategory.CLIENT_DELIVERABLE,
            "customer": TaskCategory.CLIENT_DELIVERABLE,
            "docs": TaskCategory.DOCUMENTATION,
            "documentation": TaskCategory.DOCUMENTATION,
            "test": TaskCategory.QUALITY_AUTOMATION,
            "testing": TaskCategory.QUALITY_AUTOMATION,
            "quality": TaskCategory.QUALITY_AUTOMATION,
            "workspace": TaskCategory.WORKSPACE_MANAGEMENT,
            "portfolio": TaskCategory.PORTFOLIO_MANAGEMENT,
        }

        for keyword, category in category_keywords.items():
            if keyword in text_lower:
                return category

        return TaskCategory.WORKSPACE_MANAGEMENT

    def _extract_time_estimate(self, text: str) -> int:
        """Extract time estimate from text in minutes"""
        # Look for patterns like "2h", "30m", "1.5 hours"
        time_patterns = [
            r"(\d+\.?\d*)\s*h(?:ours?)?",
            r"(\d+)\s*m(?:ins?|inutes?)?",
            r"(\d+\.?\d*)\s*hours?",
        ]

        for pattern in time_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = float(match.group(1))
                if "m" in pattern:  # Minutes
                    return int(value)
                else:  # Hours - convert to minutes
                    return int(value * 60)

        return 60  # Default to 1 hour if no estimate found

    def save_tasks(self, tasks: List[TaskModel], target_path: str) -> bool:
        """Save tasks to markdown file"""
        try:
            content_lines = []
            content_lines.append("# Tasks")
            content_lines.append("")

            # Group by status
            status_groups = {}
            for task in tasks:
                status = task.status
                if status not in status_groups:
                    status_groups[status] = []
                status_groups[status].append(task)

            for status, task_list in status_groups.items():
                content_lines.append(f"## {status.value.title()}")
                content_lines.append("")

                for task in task_list:
                    # Format task line
                    status_symbol = {
                        TaskStatus.COMPLETED: "[x]",
                        TaskStatus.IN_PROGRESS: "[~]",
                        TaskStatus.BLOCKED: "[!]",
                        TaskStatus.PENDING: "[ ]",
                        TaskStatus.CANCELLED: "[c]",
                    }.get(task.status, "[ ]")

                    line = f"- {status_symbol} {task.title}"

                    # Add metadata
                    metadata_parts = []
                    if task.priority != TaskPriority.MEDIUM:
                        metadata_parts.append(task.priority.value)
                    if task.estimated_minutes and task.estimated_minutes > 0:
                        hours = task.estimated_minutes / 60
                        if hours >= 1:
                            metadata_parts.append(f"{hours:.1f}h")
                        else:
                            metadata_parts.append(f"{task.estimated_minutes}m")
                    if task.category:
                        metadata_parts.append(task.category.value)

                    if metadata_parts:
                        line += f" [{', '.join(metadata_parts)}]"

                    content_lines.append(line)

                content_lines.append("")

            with open(target_path, "w", encoding="utf-8") as f:
                f.write("\n".join(content_lines))

            return True

        except Exception as e:
            print(f"Error saving tasks to {target_path}: {e}")
            return False

    def validate_source(self, source_path: str) -> bool:
        """Validate markdown file"""
        try:
            path = Path(source_path)
            return path.exists() and path.suffix.lower() in [".md", ".markdown"]
        except Exception:
            return False


class JSONTaskAdapter(TaskSourceAdapter):
    """Adapter for JSON-formatted task files"""

    def load_tasks(self, source_path: str) -> List[TaskModel]:
        """Load tasks from JSON file"""
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            tasks = []
            task_list = data if isinstance(data, list) else data.get("tasks", [])

            for task_data in task_list:
                task = self._create_task_from_dict(task_data, source_path)
                if task:
                    tasks.append(task)

            return tasks

        except Exception as e:
            print(f"Error loading JSON tasks from {source_path}: {e}")
            return []

    def _create_task_from_dict(
        self, task_data: Dict[str, Any], source_path: str
    ) -> Optional[TaskModel]:
        """Create TaskModel from dictionary"""
        try:
            return TaskModel(
                id=task_data.get("id", f"json_{hash(str(task_data)) % 10000}"),
                title=task_data.get("title", ""),
                description=task_data.get("description", ""),
                status=TaskStatus(task_data.get("status", "pending")),
                priority=TaskPriority(task_data.get("priority", "medium")),
                category=TaskCategory(
                    task_data.get("category", "workspace_management")
                ),
                estimated_minutes=task_data.get("estimated_minutes", 60),
                dependencies=task_data.get("dependencies", []),
                source_file=source_path,
                created_at=(
                    datetime.fromisoformat(task_data["created_at"])
                    if "created_at" in task_data
                    else datetime.now()
                ),
                updated_at=(
                    datetime.fromisoformat(task_data["updated_at"])
                    if "updated_at" in task_data
                    else datetime.now()
                ),
            )
        except Exception as e:
            print(f"Error creating task from data {task_data}: {e}")
            return None

    def save_tasks(self, tasks: List[TaskModel], target_path: str) -> bool:
        """Save tasks to JSON file"""
        try:
            task_data = []
            for task in tasks:
                task_dict = {
                    "id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "status": task.status.value,
                    "priority": task.priority.value,
                    "category": task.category.value,
                    "estimated_minutes": task.estimated_minutes,
                    "dependencies": getattr(task, "dependencies", []),
                    "created_at": task.created_at.isoformat(),
                    "updated_at": task.updated_at.isoformat(),
                }
                task_data.append(task_dict)

            with open(target_path, "w", encoding="utf-8") as f:
                json.dump({"tasks": task_data}, f, indent=2, ensure_ascii=False)

            return True

        except Exception as e:
            print(f"Error saving tasks to {target_path}: {e}")
            return False

    def validate_source(self, source_path: str) -> bool:
        """Validate JSON file"""
        try:
            path = Path(source_path)
            if not (path.exists() and path.suffix.lower() == ".json"):
                return False

            with open(source_path, "r") as f:
                json.load(f)
            return True

        except Exception:
            return False


class UniversalTaskInterface:
    """Universal interface for loading tasks from multiple sources"""

    def __init__(self, config=None):
        if config is None:
            try:
                config = config_manager.config
            except Exception:
                config = None

        self.config = config
        self.adapters = {
            "markdown": MarkdownTaskAdapter(),
            "json": JSONTaskAdapter(),
            # Add more adapters as needed
        }

    def load_all_tasks(self, search_paths: List[str] = None) -> List[TaskModel]:
        """Load tasks from all configured sources"""
        if search_paths is None:
            search_paths = ["."]

        all_tasks = []

        for adapter_name, adapter in self.adapters.items():
            if self._is_source_enabled(adapter_name):
                patterns = self._get_source_patterns(adapter_name)

                for search_path in search_paths:
                    for pattern in patterns:
                        task_files = self._find_files(search_path, pattern)

                        for task_file in task_files:
                            if adapter.validate_source(task_file):
                                tasks = adapter.load_tasks(task_file)
                                all_tasks.extend(tasks)

        return all_tasks

    def save_tasks(
        self, tasks: List[TaskModel], target_path: str, format_type: str = "json"
    ) -> bool:
        """Save tasks using specified format"""
        adapter = self.adapters.get(format_type)
        if not adapter:
            print(f"Unsupported format: {format_type}")
            return False

        return adapter.save_tasks(tasks, target_path)

    def _is_source_enabled(self, adapter_name: str) -> bool:
        """Check if source type is enabled in configuration"""
        if not self.config:
            return True  # Default to enabled if no config

        source_key = f"{adapter_name}_files"
        task_sources = getattr(self.config, "task_sources", {})
        source_config = task_sources.get(source_key)

        return source_config.enabled if source_config else False

    def _get_source_patterns(self, adapter_name: str) -> List[str]:
        """Get file patterns for source type"""
        if not self.config:
            # Default patterns
            default_patterns = {
                "markdown": ["**/*TASKS*.md", "**/*TODO*.md"],
                "json": ["**/*tasks*.json"],
            }
            return default_patterns.get(adapter_name, [])

        source_key = f"{adapter_name}_files"
        task_sources = getattr(self.config, "task_sources", {})
        source_config = task_sources.get(source_key)

        return source_config.patterns if source_config else []

    def _find_files(self, search_path: str, pattern: str) -> List[str]:
        """Find files matching pattern in search path"""
        try:
            from pathlib import Path

            search_dir = Path(search_path)

            if not search_dir.exists():
                return []

            # Use glob to find matching files
            matching_files = list(search_dir.glob(pattern))
            return [str(f) for f in matching_files if f.is_file()]

        except Exception as e:
            print(f"Error finding files with pattern {pattern}: {e}")
            return []
