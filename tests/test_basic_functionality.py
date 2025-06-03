#!/usr/bin/env python3
"""
Test the Priorities Management System basic functionality
"""

import sys
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


def test_config_loading():
    """Test configuration loading"""
    print("🧪 Testing configuration loading...")

    try:
        from core.config_manager import ConfigManager

        config_manager = ConfigManager()

        # Try to load config
        config_path = Path(__file__).parent.parent / "config" / "priorities_config.toml"
        config = config_manager.load_config(str(config_path))

        print(f"✅ Config loaded: {config.system.get('name', 'Unknown')}")
        print(f"   Data directory: {config.paths.data_directory}")
        print(f"   Enabled sources: {list(config.get_enabled_task_sources().keys())}")

        return True

    except Exception as e:
        print(f"❌ Config loading failed: {e}")
        return False


def test_task_interface():
    """Test task loading interface"""
    print("\n🧪 Testing task interface...")

    try:
        from core.task_interface import UniversalTaskInterface
        from core.config_manager import ConfigManager

        config_manager = ConfigManager()
        config_path = Path(__file__).parent.parent / "config" / "priorities_config.toml"
        config = config_manager.load_config(str(config_path))

        interface = UniversalTaskInterface(config)

        # Try to load sample tasks
        examples_dir = Path(__file__).parent.parent / "examples"
        tasks = interface.load_all_tasks([str(examples_dir)])

        print(f"✅ Found {len(tasks)} tasks")

        if tasks:
            for i, task in enumerate(tasks[:3]):  # Show first 3
                print(f"   {i+1}. {task.title} [{task.priority.value}]")

        return True

    except Exception as e:
        print(f"❌ Task interface failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_priority_engine():
    """Test priority analysis engine"""
    print("\n🧪 Testing priority engine...")

    try:
        from core.priority_engine_standalone import PriorityEngine
        from core.task_models import TaskModel, TaskPriority, TaskStatus
        from datetime import datetime

        # Create sample tasks
        tasks = [
            TaskModel(
                id="test_1",
                title="Critical infrastructure setup",
                description="Set up core infrastructure",
                status=TaskStatus.PENDING,
                priority=TaskPriority.HIGH,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
            TaskModel(
                id="test_2",
                title="Client documentation update",
                description="Update client-facing documentation",
                status=TaskStatus.PENDING,
                priority=TaskPriority.MEDIUM,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
        ]

        # Test priority engine
        engine = PriorityEngine()
        recommendations = engine.analyze_priorities(tasks)

        print(f"✅ Generated {len(recommendations)} recommendations")

        for rec in recommendations:
            task = next(t for t in tasks if t.id == rec.task_id)
            print(
                f"   {task.title}: {rec.current_priority.value} -> {rec.recommended_priority.value}"
            )
            print(f"      Reasoning: {', '.join(rec.reasoning)}")

        return True

    except Exception as e:
        print(f"❌ Priority engine failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("🚀 Testing Priorities Management System")
    print("=" * 50)

    tests = [test_config_loading, test_task_interface, test_priority_engine]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1

    print(f"\n📊 Test Results: {passed}/{total} passed")

    if passed == total:
        print("🎉 All tests passed! System is ready.")
        return 0
    else:
        print("❌ Some tests failed. Check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
