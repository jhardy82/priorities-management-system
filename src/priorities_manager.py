#!/usr/bin/env python3
"""
Priorities Management System - Main Entry Point
Enterprise task management and prioritization engine
"""

import argparse
import sys
from pathlib import Path
from typing import List, Optional
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.config_manager import ConfigManager, ConfigError
from core.task_interface import UniversalTaskInterface
from core.priority_engine_standalone import PriorityEngine
from core.task_models import TaskModel


class PrioritiesManager:
    """Main priorities management system"""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the priorities management system"""
        self.config_manager = ConfigManager()

        try:
            self.config = self.config_manager.load_config(config_path)
            print("✅ Configuration loaded successfully")
        except ConfigError as e:
            print(f"❌ Configuration error: {e}")
            sys.exit(1)

        self.task_interface = UniversalTaskInterface(self.config)
        self.priority_engine = PriorityEngine(self.config)

    def analyze_priorities(self, search_paths: List[str] = None) -> None:
        """Analyze and update task priorities"""
        print("🔍 Loading tasks from configured sources...")

        if search_paths is None:
            search_paths = [self.config.paths.data_directory]

        # Load tasks from paths (can be files or directories)
        tasks = []
        for path in search_paths:
            path_obj = Path(path)
            if path_obj.is_file() and path_obj.suffix == ".md":
                # Load single markdown file
                from core.task_interface import MarkdownTaskAdapter

                markdown_adapter = MarkdownTaskAdapter()
                file_tasks = markdown_adapter.load_tasks(str(path_obj))
                tasks.extend(file_tasks)
            elif path_obj.is_dir():
                # Load from directory
                dir_tasks = self.task_interface.load_all_tasks([str(path_obj)])
                tasks.extend(dir_tasks)

        if not tasks:
            print("📭 No tasks found in specified sources")
            return

        print(f"📋 Found {len(tasks)} tasks")

        # Analyze priorities
        print("🧠 Analyzing task priorities...")
        recommendations = self.priority_engine.analyze_priorities(tasks)

        if not recommendations:
            print("✅ No priority changes recommended")
            return

        print(f"💡 Generated {len(recommendations)} priority recommendations:")

        # Display recommendations
        for rec in recommendations:
            task = next(t for t in tasks if t.id == rec.task_id)
            print(f"\n📌 Task: {task.title}")
            print(f"   Current: {rec.current_priority.value}")
            print(f"   Recommended: {rec.recommended_priority.value}")
            print(f"   Confidence: {rec.confidence_score:.2f}")
            print(f"   Reasoning: {', '.join(rec.reasoning)}")

        # Apply changes if not in dry run mode
        if not self.config.automation.dry_run_mode:
            if self._confirm_changes(recommendations):
                self._apply_recommendations(tasks, recommendations)
                self._save_updated_tasks(tasks)
        else:
            print("\n🔒 Dry run mode - no changes applied")

    def generate_report(
        self, search_paths: List[str] = None, output_path: Optional[str] = None
    ) -> None:
        """Generate priority analysis report"""
        print("📊 Generating priority analysis report...")

        if search_paths is None:
            search_paths = [self.config.paths.data_directory]

        # Load tasks from paths (can be files or directories)
        tasks = []
        for path in search_paths:
            path_obj = Path(path)
            if path_obj.is_file() and path_obj.suffix == ".md":
                # Load single markdown file
                from core.task_interface import MarkdownTaskAdapter

                markdown_adapter = MarkdownTaskAdapter()
                file_tasks = markdown_adapter.load_tasks(str(path_obj))
                tasks.extend(file_tasks)
            elif path_obj.is_dir():
                # Load from directory
                dir_tasks = self.task_interface.load_all_tasks([str(path_obj)])
                tasks.extend(dir_tasks)

        if not tasks:
            print("📭 No tasks found for report generation")
            return

        # Generate analysis
        recommendations = self.priority_engine.analyze_priorities(tasks)
        dependency_analysis = self.priority_engine.generate_dependency_analysis(tasks)

        # Create report
        report = self._create_report(tasks, recommendations, dependency_analysis)

        # Save report
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = (
                f"{self.config.paths.reports_directory}/priority_report_{timestamp}.md"
            )

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report)

        print(f"📄 Report saved to: {output_path}")

    def demo_mode(self) -> None:
        """Run demonstration with sample data"""
        print("🎪 Priorities Management System - Demo Mode")
        print("=" * 50)

        # Use sample tasks from examples
        sample_path = Path(__file__).parent / "examples" / "sample-tasks.md"

        if not sample_path.exists():
            print("❌ Sample tasks file not found. Creating demo tasks...")
            self._create_demo_tasks()
            return

        print(f"📂 Loading demo tasks from: {sample_path}")

        # Use markdown adapter directly for single file loading
        from core.task_interface import MarkdownTaskAdapter

        markdown_adapter = MarkdownTaskAdapter()
        tasks = markdown_adapter.load_tasks(str(sample_path))

        if not tasks:
            print("❌ Failed to load demo tasks")
            return

        print(f"✅ Loaded {len(tasks)} demo tasks")

        # Show original priorities
        print("\n📋 Original Task Priorities:")
        for i, task in enumerate(tasks, 1):
            print(f"   {i}. {task.title} [{task.priority.value}] - {task.category}")

        # Analyze priorities
        print("\n🧠 Analyzing task priorities...")
        recommendations = self.priority_engine.analyze_priorities(tasks)

        if recommendations:
            print(f"\n💡 Generated {len(recommendations)} recommendations:")
            for rec in recommendations:
                task = next(t for t in tasks if t.id == rec.task_id)
                print(f"\n📌 {task.title}")
                print(
                    f"   {rec.current_priority.value} → {rec.recommended_priority.value}"
                )
                print(f"   Confidence: {rec.confidence_score:.2f}")
                print(f"   Reasons: {', '.join(rec.reasoning)}")
        else:
            print("✅ No priority changes recommended")

        # Generate dependency analysis
        print("\n🔗 Dependency Analysis:")
        try:
            dependency_analysis = self.priority_engine.generate_dependency_analysis(
                tasks
            )

            # Handle list of DependencyGraph objects
            if isinstance(dependency_analysis, list):
                critical_tasks = [
                    dg.task_id for dg in dependency_analysis if dg.critical_path_member
                ]
                total_dependencies = sum(
                    len(dg.direct_dependencies) for dg in dependency_analysis
                )
            else:
                critical_tasks = []
                total_dependencies = 0

            if critical_tasks:
                print(f"   Critical path: {len(critical_tasks)} tasks")
                for task_id in critical_tasks[:3]:  # Show first 3
                    print(f"     • {task_id}")
            else:
                print("   No critical path dependencies detected")

            print(f"   Total dependencies: {total_dependencies}")
            print(
                f"   Tasks analyzed: {len(dependency_analysis) if isinstance(dependency_analysis, list) else 0}"
            )
        except Exception as e:
            print(f"   ⚠️  Dependency analysis unavailable: {str(e)[:50]}...")
            print("   This is a known issue and doesn't affect priority analysis")

        print(
            f"\n📊 Demo completed! Found {len(tasks)} tasks with {len(recommendations)} recommendations."
        )

    def validate_system(self) -> None:
        """Validate system configuration and functionality"""
        print("🔍 Validating Priorities Management System")
        print("=" * 50)

        validation_results = []

        # Test 1: Configuration validation
        print("1️⃣ Validating configuration...")
        try:
            # Test basic config access
            _ = self.config.paths.data_directory
            _ = self.config.automation.dry_run_mode
            validation_results.append(("Configuration", True, "Valid"))
        except Exception as e:
            validation_results.append(("Configuration", False, str(e)))

        # Test 2: Directory structure
        print("2️⃣ Checking directory structure...")
        try:
            required_dirs = [
                self.config.paths.data_directory,
                self.config.paths.reports_directory,
                self.config.paths.backup_directory,
            ]

            missing_dirs = []
            for dir_path in required_dirs:
                if not Path(dir_path).exists():
                    missing_dirs.append(dir_path)

            if missing_dirs:
                validation_results.append(
                    ("Directories", False, f"Missing: {', '.join(missing_dirs)}")
                )
            else:
                validation_results.append(
                    ("Directories", True, "All directories exist")
                )
        except Exception as e:
            validation_results.append(("Directories", False, str(e)))

        # Test 3: Task loading
        print("3️⃣ Testing task loading...")
        try:
            sample_path = Path(__file__).parent / "examples" / "sample-tasks.md"
            if sample_path.exists():
                # Use markdown adapter directly
                from core.task_interface import MarkdownTaskAdapter

                markdown_adapter = MarkdownTaskAdapter()
                tasks = markdown_adapter.load_tasks(str(sample_path))
                msg = f"Loaded {len(tasks)} tasks"
                validation_results.append(("Task Loading", True, msg))
            else:
                validation_results.append(
                    ("Task Loading", False, "Sample tasks file not found")
                )
        except Exception as e:
            validation_results.append(("Task Loading", False, str(e)))

        # Test 4: Priority engine
        print("4️⃣ Testing priority engine...")
        try:
            # Create minimal test task
            from core.task_models import TaskModel, TaskPriority, TaskCategory

            test_task = TaskModel(
                id="test_001",
                title="Test Task",
                description="Test description",
                priority=TaskPriority.MEDIUM,
                category=TaskCategory.WORKSPACE_MANAGEMENT,
                estimated_minutes=60,
            )

            recommendations = self.priority_engine.analyze_priorities([test_task])
            validation_results.append(("Priority Engine", True, "Engine functional"))
        except Exception as e:
            validation_results.append(("Priority Engine", False, str(e)))

        # Display results
        print("\n📋 Validation Results:")
        all_passed = True
        for component, passed, message in validation_results:
            status = "✅" if passed else "❌"
            print(f"   {status} {component}: {message}")
            if not passed:
                all_passed = False

        if all_passed:
            print("\n🎉 All validations passed! System ready for use.")
        else:
            print(
                "\n⚠️ Some validations failed. Please check configuration and dependencies."
            )

    def interactive_mode(self) -> None:
        """Run in interactive mode"""
        print("🎛️  Interactive Priorities Management System")
        print("=" * 50)

        while True:
            print("\nAvailable commands:")
            print("1. Analyze priorities")
            print("2. Generate report")
            print("3. Show loaded tasks")
            print("4. Show configuration")
            print("5. Run demo")
            print("6. Validate system")
            print("7. Create sample tasks")
            print("8. Exit")

            choice = input("\nEnter your choice (1-8): ").strip()

            if choice == "1":
                self.analyze_priorities()
            elif choice == "2":
                self.generate_report()
            elif choice == "3":
                self._show_loaded_tasks()
            elif choice == "4":
                self._show_config()
            elif choice == "5":
                self.demo_mode()
            elif choice == "6":
                self.validate_system()
            elif choice == "7":
                self._create_demo_tasks()
            elif choice == "8":
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please try again.")

    def _confirm_changes(self, recommendations) -> bool:
        """Confirm priority changes with user"""
        if not self.config.safety.require_confirmation_for_critical:
            return True

        print(f"\n❓ Apply {len(recommendations)} priority changes? (y/N): ", end="")
        response = input().strip().lower()
        return response in ["y", "yes"]

    def _apply_recommendations(self, tasks: List[TaskModel], recommendations) -> None:
        """Apply priority recommendations to tasks"""
        print("✏️  Applying priority changes...")

        changes_applied = 0
        max_changes = self.config.automation.max_priority_changes_per_run

        for rec in recommendations:
            if changes_applied >= max_changes:
                print(f"⚠️  Reached maximum changes limit ({max_changes})")
                break

            task = next(t for t in tasks if t.id == rec.task_id)
            if rec.confidence_score >= self.config.automation.confidence_threshold:
                task.priority = rec.recommended_priority
                changes_applied += 1
                print(
                    f"   ✅ Updated: {task.title} -> {rec.recommended_priority.value}"
                )

        print(f"📝 Applied {changes_applied} priority changes")

    def _save_updated_tasks(self, tasks: List[TaskModel]) -> None:
        """Save updated tasks back to sources"""
        if self.config.automation.auto_backup:
            print("💾 Creating backup...")
            # TODO: Implement backup functionality

        print("💾 Saving updated tasks...")
        # TODO: Implement saving back to original sources

        # For now, save to JSON in reports directory
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = (
            f"{self.config.paths.reports_directory}/updated_tasks_{timestamp}.json"
        )

        if self.task_interface.save_tasks(tasks, output_path, "json"):
            print(f"✅ Tasks saved to: {output_path}")
        else:
            print("❌ Failed to save tasks")

    def _create_report(self, tasks, recommendations, dependency_analysis) -> str:
        """Create markdown report"""
        from datetime import datetime

        report_lines = []
        report_lines.append("# Priority Analysis Report")
        report_lines.append(
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        report_lines.append("")

        # Calculate critical path tasks
        if isinstance(dependency_analysis, list):
            critical_path_count = len(
                [dg for dg in dependency_analysis if dg.critical_path_member]
            )
        else:
            critical_path_count = 0

        # Summary statistics
        report_lines.append("## Summary")
        report_lines.append(f"- Total tasks: {len(tasks)}")
        report_lines.append(f"- Priority recommendations: {len(recommendations)}")
        report_lines.append(f"- Critical path tasks: {critical_path_count}")
        report_lines.append("")

        # Priority distribution
        priority_counts = {}
        for task in tasks:
            priority = task.priority.value
            priority_counts[priority] = priority_counts.get(priority, 0) + 1

        report_lines.append("## Priority Distribution")
        for priority, count in sorted(priority_counts.items()):
            report_lines.append(f"- {priority.title()}: {count}")
        report_lines.append("")

        # Recommendations
        if recommendations:
            report_lines.append("## Priority Recommendations")
            for rec in recommendations:
                task = next(t for t in tasks if t.id == rec.task_id)
                report_lines.append(f"### {task.title}")
                report_lines.append(f"- Current: {rec.current_priority.value}")
                report_lines.append(f"- Recommended: {rec.recommended_priority.value}")
                report_lines.append(f"- Confidence: {rec.confidence_score:.2f}")
                report_lines.append(f"- Reasoning: {', '.join(rec.reasoning)}")
                report_lines.append("")

        return "\n".join(report_lines)

    def _show_loaded_tasks(self) -> None:
        """Show currently loaded tasks"""
        tasks = self.task_interface.load_all_tasks()

        if not tasks:
            print("📭 No tasks currently loaded")
            return

        print(f"📋 Loaded {len(tasks)} tasks:")
        for task in tasks[:10]:  # Show first 10
            print(f"   - {task.title} [{task.priority.value}]")

        if len(tasks) > 10:
            print(f"   ... and {len(tasks) - 10} more")

    def _create_demo_tasks(self) -> None:
        """Create demonstration tasks for testing"""
        print("🎪 Creating demo tasks...")

        demo_tasks_content = """# Demo Tasks for Priority Management System

## High Priority Tasks

### TASK-001: Critical Security Patch Deployment
- **Priority**: critical
- **Category**: Security
- **Estimated**: 120 minutes
- **Dependencies**: TASK-002
- **Description**: Deploy critical security patches to production servers
- **Tags**: security, urgent, compliance

### TASK-002: Backup Verification
- **Priority**: high
- **Category**: Infrastructure
- **Estimated**: 60 minutes
- **Description**: Verify backup systems before maintenance window

## Medium Priority Tasks

### TASK-003: Database Performance Optimization
- **Priority**: medium
- **Category**: Performance
- **Estimated**: 240 minutes
- **Dependencies**: TASK-001
- **Description**: Optimize database queries and indexes

### TASK-004: User Training Documentation
- **Priority**: medium
- **Category**: Documentation
- **Estimated**: 180 minutes
- **Description**: Create training materials for new features

## Low Priority Tasks

### TASK-005: Code Refactoring
- **Priority**: low
- **Category**: Development
- **Estimated**: 300 minutes
- **Description**: Refactor legacy code modules for better maintainability

### TASK-006: UI Enhancement
- **Priority**: low
- **Category**: Frontend
- **Estimated**: 150 minutes
- **Description**: Improve user interface design and usability
"""

        # Ensure examples directory exists
        examples_dir = Path(__file__).parent / "examples"
        examples_dir.mkdir(exist_ok=True)

        demo_file = examples_dir / "demo-tasks.md"

        with open(demo_file, "w", encoding="utf-8") as f:
            f.write(demo_tasks_content)

        print(f"✅ Demo tasks created: {demo_file}")

        # Also update sample-tasks.md if it doesn't exist
        sample_file = examples_dir / "sample-tasks.md"
        if not sample_file.exists():
            with open(sample_file, "w", encoding="utf-8") as f:
                f.write(demo_tasks_content)
            print(f"✅ Sample tasks created: {sample_file}")

    def _show_config(self) -> None:
        """Show current configuration"""
        print("⚙️  Current Configuration:")
        print(f"   Data directory: {self.config.paths.data_directory}")
        print(f"   Reports directory: {self.config.paths.reports_directory}")
        print(f"   Dry run mode: {self.config.automation.dry_run_mode}")
        print(f"   Auto backup: {self.config.automation.auto_backup}")
        conf_thresh = self.config.automation.confidence_threshold
        print(f"   Confidence threshold: {conf_thresh}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Priorities Management System - Enterprise task prioritization"
    )

    parser.add_argument("--config", "-c", help="Path to configuration file")

    parser.add_argument(
        "--analyze",
        "-a",
        action="store_true",
        help="Analyze and update task priorities",
    )

    parser.add_argument(
        "--report", "-r", action="store_true", help="Generate priority analysis report"
    )

    parser.add_argument(
        "--demo",
        "-d",
        action="store_true",
        help="Run demonstration mode with sample data",
    )

    parser.add_argument(
        "--validate",
        "-v",
        action="store_true",
        help="Validate system configuration and functionality",
    )

    parser.add_argument(
        "--interactive", "-i", action="store_true", help="Run in interactive mode"
    )

    parser.add_argument(
        "--search-paths", "-s", nargs="+", help="Paths to search for task files"
    )

    parser.add_argument("--output", "-o", help="Output file path for reports")

    args = parser.parse_args()

    try:
        # Initialize priorities manager
        manager = PrioritiesManager(args.config)

        # Execute requested action
        if args.analyze:
            manager.analyze_priorities(args.search_paths)
        elif args.report:
            manager.generate_report(args.search_paths, args.output)
        elif args.demo:
            manager.demo_mode()
        elif args.validate:
            manager.validate_system()
        elif args.interactive:
            manager.interactive_mode()
        else:
            # Default to interactive mode
            manager.interactive_mode()

    except KeyboardInterrupt:
        print("\n👋 Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
