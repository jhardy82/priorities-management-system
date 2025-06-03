#!/usr/bin/env python3
"""
Test Script for Priorities Management System
Validates core functionality and integration
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core import (
    UniversalTaskInterface,
    PriorityEngine,
    config_manager,
    TaskModel,
    TaskPriority,
    TaskStatus,
    TaskCategory,
)
from datetime import datetime


def create_test_tasks():
    """Create sample tasks for testing"""
    tasks = [
        TaskModel(
            id="test_1",
            title="Critical Infrastructure Setup",
            description="Set up core infrastructure components",
            status=TaskStatus.PENDING,
            priority=TaskPriority.HIGH,
            category=TaskCategory.INFRASTRUCTURE,
            estimated_minutes=480,  # 8 hours
            dependencies=["test_2"],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
        TaskModel(
            id="test_2",
            title="Database Configuration",
            description="Configure database connections and schema",
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.MEDIUM,
            category=TaskCategory.INFRASTRUCTURE,
            estimated_minutes=240,  # 4 hours
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
        TaskModel(
            id="test_3",
            title="Client Requirements Documentation",
            description="Document client requirements and specifications",
            status=TaskStatus.PENDING,
            priority=TaskPriority.HIGH,
            category=TaskCategory.CLIENT_DELIVERABLE,
            estimated_minutes=360,  # 6 hours
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
    ]
    return tasks


def test_priority_engine():
    """Test the priority engine functionality"""
    print("🔧 Testing Priority Engine...")

    try:
        # Create priority engine
        engine = PriorityEngine()
        print("✅ Priority Engine created successfully")

        # Create test tasks
        tasks = create_test_tasks()
        print(f"✅ Created {len(tasks)} test tasks")

        # Analyze priorities
        recommendations = engine.analyze_priorities(tasks)
        print(f"✅ Generated {len(recommendations)} priority recommendations")

        # Print recommendations
        for rec in recommendations:
            print(
                f"   📋 Task {rec.task_id}: {rec.current_priority} → {rec.recommended_priority}"
            )
            print(f"      Reasoning: {rec.reasoning}")

        return True

    except Exception as e:
        print(f"❌ Priority Engine test failed: {e}")
        return False


def test_task_interface():
    """Test the universal task interface"""
    print("\n📁 Testing Task Interface...")

    try:
        # Create task interface
        interface = UniversalTaskInterface()
        print("✅ Task Interface created successfully")

        # Create test tasks
        tasks = create_test_tasks()

        # Test saving tasks
        test_file = "test_output.json"
        success = interface.save_tasks(tasks, test_file, "json")

        if success:
            print(f"✅ Tasks saved to {test_file}")
        else:
            print(f"❌ Failed to save tasks to {test_file}")
            return False

        # Test loading tasks
        loaded_tasks = interface.adapters["json"].load_tasks(test_file)
        print(f"✅ Loaded {len(loaded_tasks)} tasks from {test_file}")

        # Clean up
        if os.path.exists(test_file):
            os.remove(test_file)
            print("✅ Cleaned up test file")

        return True

    except Exception as e:
        print(f"❌ Task Interface test failed: {e}")
        return False


def test_configuration():
    """Test configuration management"""
    print("\n⚙️ Testing Configuration...")

    try:
        # Try to load configuration
        config_path = "config/priorities_config.toml"
        if os.path.exists(config_path):
            config = config_manager.load_config(config_path)
            print("✅ Configuration loaded successfully")
            print(f"   System name: {config.system.get('name', 'Unknown')}")
            print(f"   Version: {config.system.get('version', 'Unknown')}")
            return True
        else:
            print(f"⚠️  Configuration file not found at {config_path}")
            print("   System will use defaults")
            return True

    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False


def create_sample_markdown_task_file():
    """Create a sample markdown task file for testing"""
    sample_content = """# Sample Tasks

## High Priority
- [ ] Critical Infrastructure Setup [critical, 8h, infrastructure]
- [x] Database Schema Design [high, 4h, infrastructure]
- [ ] Client Requirements Review [high, 6h, client]

## Medium Priority  
- [~] API Documentation [medium, 3h, documentation]
- [ ] Unit Tests Implementation [medium, 5h, quality]

## Low Priority
- [ ] Code Cleanup [low, 2h, workspace]
- [ ] Performance Optimization [low, 4h, infrastructure]
"""

    with open("examples/sample-tasks.md", "w") as f:
        f.write(sample_content)

    print("✅ Created sample markdown task file")


def test_markdown_parsing():
    """Test markdown task parsing"""
    print("\n📝 Testing Markdown Parsing...")

    try:
        # Ensure examples directory exists
        os.makedirs("examples", exist_ok=True)

        # Create sample file
        create_sample_markdown_task_file()

        # Load tasks from markdown
        interface = UniversalTaskInterface()
        adapter = interface.adapters["markdown"]

        tasks = adapter.load_tasks("examples/sample-tasks.md")
        print(f"✅ Parsed {len(tasks)} tasks from markdown")

        for task in tasks[:3]:  # Show first 3 tasks
            print(f"   📋 {task.title} [{task.priority.value}, {task.status.value}]")

        return True

    except Exception as e:
        print(f"❌ Markdown parsing test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("🚀 Starting Priorities Management System Tests\n")

    tests = [
        test_configuration,
        test_priority_engine,
        test_task_interface,
        test_markdown_parsing,
    ]

    results = []
    for test in tests:
        result = test()
        results.append(result)

    print(f"\n📊 Test Results Summary:")
    print(f"   ✅ Passed: {sum(results)}")
    print(f"   ❌ Failed: {len(results) - sum(results)}")
    print(f"   📈 Success Rate: {(sum(results) / len(results)) * 100:.1f}%")

    if all(results):
        print("\n🎉 All tests passed! System is ready for use.")
        return True
    else:
        print("\n⚠️  Some tests failed. Please check the issues above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
