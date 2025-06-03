#!/usr/bin/env python3
"""
Debug test for Priority Engine
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from core.task_models import TaskModel, TaskPriority, TaskStatus, TaskCategory
    from core.priority_engine_standalone import PriorityEngine
    from datetime import datetime

    print("🔧 Testing Priority Engine...")

    # Create test tasks
    tasks = [
        TaskModel(
            id="test_1",
            title="Critical Infrastructure Setup",
            estimated_minutes=480,  # 8 hours
            priority=TaskPriority.HIGH,
            category=TaskCategory.INFRASTRUCTURE,
            dependencies=["test_2"],
        ),
        TaskModel(
            id="test_2",
            title="Database Configuration",
            estimated_minutes=240,  # 4 hours
            priority=TaskPriority.MEDIUM,
            category=TaskCategory.INFRASTRUCTURE,
        ),
    ]

    print(f"✅ Created {len(tasks)} test tasks")

    # Create priority engine
    engine = PriorityEngine()
    print("✅ Priority Engine initialized")

    # Analyze priorities
    recommendations = engine.analyze_priorities(tasks)
    print(f"✅ Generated {len(recommendations)} recommendations")

    for rec in recommendations:
        print(
            f"   📋 Task {rec.task_id}: {rec.current_priority} → {rec.recommended_priority}"
        )
        print(f"      Confidence: {rec.confidence_score:.2f}")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback

    traceback.print_exc()
