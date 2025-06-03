#!/usr/bin/env python3
"""
Simple debug test for task creation
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from core.task_models import TaskModel, TaskPriority, TaskStatus, TaskCategory
    from datetime import datetime

    print("🔍 Testing TaskModel creation...")

    # Create minimal task
    task = TaskModel(id="test_1", title="Test Task", estimated_minutes=60)

    print(f"✅ Success! Created task: {task.title}")
    print(f"   ID: {task.id}")
    print(f"   Status: {task.status}")
    print(f"   Priority: {task.priority}")
    print(f"   Category: {task.category}")
    print(f"   Estimated: {task.estimated_minutes} minutes")

except Exception as e:
    print(f"❌ Error creating TaskModel: {e}")
    import traceback

    traceback.print_exc()
