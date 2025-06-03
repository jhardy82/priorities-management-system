#!/usr/bin/env python3
"""
AAR Auto-Update Protocol - Main Orchestrator (SCF Version)
Task #5 Implementation: Automated task management system

This is the main automation controller that orchestrates:
- Task parsing and analysis
- Priority recommendations
- AAR updates
- File modifications with safety checks

Created following the Scripted Collaboration Framework.
"""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
import re

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import track
import yaml

from context_manager import create_context, Context, OperationType, SCFPhase
from task_models import TaskModel, WorkspaceSnapshot, WorkspaceMetrics
from task_parser import TaskParser, Task
from priority_engine import PriorityEngine

app = typer.Typer(help="🎯 AAR Auto-Update Protocol - Intelligent Task Management")
console = Console()


class AAROrchestrator:
    """
    Main orchestrator for AAR automation

    Implements the SCF pattern for Python to manage task analysis,
    prioritization, and updates in a structured manner.
    """

    def __init__(self, workspace_path: str):
        # Create context object for initialization
        self.context = create_context(
            operation_type=OperationType.ANALYSIS, scf_phase=SCFPhase.IDENTIFY_MISSION
        )

        try:
            # Setup phase
            self.workspace_path = Path(workspace_path)
            self.parser = TaskParser(self.workspace_path)
            self.priority_engine = PriorityEngine()
            self.config_path = (
                self.workspace_path / "tools" / "aar-automation" / "config.yml"
            )
            self.backup_dir = (
                self.workspace_path / "tools" / "aar-automation" / "backups"
            )
            self.reports_dir = (
                self.workspace_path / "tools" / "aar-automation" / "reports"
            )
            self.log_path = (
                self.workspace_path / "tools" / "aar-automation" / "aar_actions.log"
            )

            # Store configuration in context
            self.context.results["workspace_path"] = str(self.workspace_path)

            # Ensure directories exist
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            self.reports_dir.mkdir(parents=True, exist_ok=True)

            # CHECKPOINT: Directory setup
            self.context.log_checkpoint(
                "Initialization",
                "Created necessary directories and initialized components",
            )

            # Load configuration
            self.load_config()

        except Exception as e:
            self.context.set_error(f"Initialization failed: {str(e)}")
            console.print(f"❌ Failed to initialize orchestrator: {e}", style="red")

    def load_config(self) -> None:
        """Load configuration or create default"""
        try:
            self.context.scf_phase = SCFPhase.GATHER_CONTEXT

            if self.config_path.exists():
                with open(self.config_path, "r") as f:
                    self.config = yaml.safe_load(f)
                # CHECKPOINT: Configuration loaded
                self.context.log_checkpoint(
                    "Configuration", f"Loaded configuration from {self.config_path}"
                )
            else:
                self.config = self.get_default_config()
                self.save_config()
                # CHECKPOINT: Default configuration
                self.context.log_checkpoint(
                    "Configuration", "Created default configuration"
                )

            # Store config in context
            self.context.results["config"] = self.config

        except Exception as e:
            self.context.set_error(f"Failed to load configuration: {str(e)}")
            # Default config as fallback
            self.config = self.get_default_config()

    def get_default_config(self) -> Dict[str, Any]:
        """Return default configuration settings"""
        return {
            "analysis": {
                "enable_ml_predictions": False,
                "historical_analysis_days": 30,
            },
            "automation": {
                "auto_backup": True,
                "auto_priority_update": True,
                "confidence_threshold": 0.7,
            },
            "notification": {"console_output": True, "generate_reports": True},
            "safety": {
                "backup_retention_days": 30,
                "dry_run_mode": False,
                "max_priority_changes_per_run": 3,
            },
        }

    def save_config(self) -> None:
        """Save configuration to file"""
        try:
            with open(self.config_path, "w") as f:
                yaml.dump(self.config, f, default_flow_style=False)
            # CHECKPOINT: Configuration saved
            self.context.log_checkpoint(
                "Configuration", f"Saved configuration to {self.config_path}"
            )
        except Exception as e:
            self.context.set_error(f"Failed to save configuration: {str(e)}")

    def create_backup(self) -> Path:
        """Create a backup of the workspace tasks file"""
        try:
            self.context.scf_phase = SCFPhase.EXECUTE_IMPLEMENT

            # Define source and destination paths
            tasks_file = self.workspace_path / "WORKSPACE-TOP-25-TASKS.md"
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            backup_file = self.backup_dir / f"tasks-backup-{timestamp}.md"

            if tasks_file.exists():
                shutil.copy2(tasks_file, backup_file)
                # CHECKPOINT: Backup created
                self.context.log_checkpoint(
                    "Backup", f"Created backup at {backup_file}"
                )
                return backup_file
            else:
                self.context.log_checkpoint("Backup", "No tasks file found to backup")
                return None

        except Exception as e:
            self.context.set_error(f"Failed to create backup: {str(e)}")
            return None

    def analyze_workspace(self) -> WorkspaceSnapshot:
        """
        Analyze the workspace to create a snapshot of tasks and metrics

        Returns:
            WorkspaceSnapshot: Complete analysis of the workspace
        """
        try:
            # Update context
            self.context.scf_phase = SCFPhase.EXECUTE_IMPLEMENT
            self.context.operation_type = OperationType.ANALYSIS

            # CHECKPOINT: Analysis started
            self.context.log_checkpoint("Analysis", "Starting workspace analysis")

            # Parse tasks
            tasks = self.parser.extract_tasks()
            self.context.results["task_count"] = len(tasks)

            # Use priority engine to prioritize tasks
            metrics = self.calculate_metrics(tasks)
            priority_recommendations = self.priority_engine.generate_recommendations(
                tasks, metrics
            )

            # Create snapshot
            snapshot = WorkspaceSnapshot(
                tasks=tasks,
                metrics=metrics,
                timestamp=datetime.now(),
                priority_recommendations=priority_recommendations,
            )

            # CHECKPOINT: Analysis complete
            self.context.log_checkpoint(
                "Analysis",
                f"Completed analysis with {len(tasks)} tasks and {len(priority_recommendations)} recommendations",
            )

            # Log to file
            self.context.log_to_file(self.log_path)

            return snapshot

        except Exception as e:
            self.context.set_error(f"Analysis failed: {str(e)}")
            # Log to file
            self.context.log_to_file(self.log_path)
            # Return empty snapshot
            return WorkspaceSnapshot(
                tasks=[],
                metrics=WorkspaceMetrics(),
                timestamp=datetime.now(),
                priority_recommendations=[],
            )

    def calculate_metrics(self, tasks: List[Task]) -> WorkspaceMetrics:
        """Calculate workspace metrics based on tasks"""
        # Implementation remains the same
        return WorkspaceMetrics(
            total_tasks=len(tasks),
            completed_tasks=len([t for t in tasks if t.status == "completed"]),
            in_progress=len([t for t in tasks if t.status == "in-progress"]),
            not_started=len([t for t in tasks if t.status == "not-started"]),
            high_priority=len([t for t in tasks if t.priority == "HIGH"]),
            medium_priority=len([t for t in tasks if t.priority == "MEDIUM"]),
            low_priority=len([t for t in tasks if t.priority == "LOW"]),
        )

    def apply_priority_updates(self, snapshot: WorkspaceSnapshot) -> bool:
        """Apply priority updates to the tasks file"""
        try:
            # Update context
            self.context.scf_phase = SCFPhase.EXECUTE_IMPLEMENT
            self.context.operation_type = OperationType.UPDATE

            # CHECKPOINT: Updates started
            self.context.log_checkpoint(
                "Priority Updates",
                f"Starting to apply {len(snapshot.priority_recommendations)} priority updates",
            )

            # Read the current tasks file
            tasks_file = self.workspace_path / "WORKSPACE-TOP-25-TASKS.md"
            if not tasks_file.exists():
                self.context.set_error(f"Tasks file not found: {tasks_file} (legacy Top 10 tasks archived)")
                return False

            with open(tasks_file, "r") as f:
                content = f.read()

            # Apply each recommendation
            updates_applied = 0
            max_updates = self.config["safety"]["max_priority_changes_per_run"]

            for rec in snapshot.priority_recommendations:
                if updates_applied >= max_updates:
                    break

                # Update the priority in the content
                pattern = rf"(\[\s*\].*?{re.escape(rec.task.title)}.*?)(\bHIGH\b|\bMEDIUM\b|\bLOW\b)"
                replacement = f"\\1{rec.recommended_priority}"
                new_content = re.sub(pattern, replacement, content)

                if new_content != content:
                    content = new_content
                    updates_applied += 1
                    console.print(
                        f"✅ Updated: '{rec.task.title}' priority: {rec.task.priority} → {rec.recommended_priority}"
                    )

            # Write the updated content back
            with open(tasks_file, "w") as f:
                f.write(content)

            # CHECKPOINT: Updates complete
            self.context.log_checkpoint(
                "Priority Updates", f"Applied {updates_applied} priority updates"
            )

            # Store results
            self.context.results["updates_applied"] = updates_applied
            self.context.results["recommendations_count"] = len(
                snapshot.priority_recommendations
            )

            # Log to file
            self.context.log_to_file(self.log_path)

            return True

        except Exception as e:
            self.context.set_error(f"Failed to apply updates: {str(e)}")
            # Log to file
            self.context.log_to_file(self.log_path)
            return False

    def display_analysis(self, snapshot: WorkspaceSnapshot) -> None:
        """Display the analysis results in a rich format"""
        # Update context
        self.context.scf_phase = SCFPhase.REVIEW_DOCUMENT

        # Create recommendations table
        table = Table(title="🎯 Priority Recommendations")
        table.add_column("Task", style="cyan")
        table.add_column("Current", style="yellow")
        table.add_column("Recommended", style="green")
        table.add_column("Confidence", style="blue")

        for rec in snapshot.priority_recommendations:
            table.add_row(
                rec.task.title,
                rec.task.priority,
                rec.recommended_priority,
                f"{rec.confidence:.2f}",
            )

        console.print(table)

        # Display metrics
        metrics = snapshot.metrics
        console.print(
            Panel(
                f"Total Tasks: {metrics.total_tasks}\n"
                f"Completed: {metrics.completed_tasks}\n"
                f"In Progress: {metrics.in_progress}\n"
                f"Not Started: {metrics.not_started}\n"
                f"Priority Distribution: {metrics.high_priority} HIGH, {metrics.medium_priority} MEDIUM, {metrics.low_priority} LOW",
                title="📊 Workspace Metrics",
            )
        )


@app.command()
def analyze(workspace_path: str = typer.Option(".", help="Path to workspace")):
    """📊 Analyze workspace tasks and priorities"""
    orchestrator = AAROrchestrator(workspace_path)

    # Check for initialization errors
    if orchestrator.context.has_error:
        console.print(f"❌ {orchestrator.context.error_message}", style="red")
        raise typer.Exit(1)

    try:
        # Perform the analysis
        console.print("📈 Analyzing workspace tasks...")
        snapshot = orchestrator.analyze_workspace()

        # Display results
        orchestrator.display_analysis(snapshot)

        # Generate report if configured
        if orchestrator.config["notification"]["generate_reports"]:
            report_path = (
                orchestrator.reports_dir
                / f"analysis-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
            )
            with open(report_path, "w") as f:
                json.dump(snapshot.dict(), f, default=str, indent=2)
            console.print(f"✅ Analysis report saved to: {report_path}")

    except Exception as e:
        console.print(f"❌ Error during analysis: {e}", style="red")
        raise typer.Exit(1)


@app.command()
def update(
    workspace_path: str = typer.Option(".", help="Path to workspace"),
    dry_run: bool = typer.Option(True, help="Perform dry run without making changes"),
    backup: bool = typer.Option(True, help="Create backup before changes"),
):
    """🔄 Update task priorities based on analysis"""
    orchestrator = AAROrchestrator(workspace_path)

    # Check for initialization errors
    if orchestrator.context.has_error:
        console.print(f"❌ {orchestrator.context.error_message}", style="red")
        raise typer.Exit(1)

    try:
        if backup and not dry_run:
            orchestrator.create_backup()

        snapshot = orchestrator.analyze_workspace()

        if not snapshot.priority_recommendations:
            console.print("✅ No priority updates needed")
            return

        console.print(
            f"🎯 Found {len(snapshot.priority_recommendations)} priority recommendations"
        )

        if dry_run:
            console.print("\n🧪 DRY RUN MODE - No changes will be made")
            orchestrator.display_analysis(snapshot)
        else:
            # Apply updates to the markdown file and add AAR entries
            orchestrator.apply_priority_updates(snapshot)
            console.print(
                "\n✅ LIVE UPDATE MODE - Changes applied to WORKSPACE-TOP-25-TASKS.md"
            )

    except Exception as e:
        console.print(f"❌ Error during update: {e}", style="red")
        raise typer.Exit(1)


@app.command()
def config(
    show: bool = typer.Option(False, help="Show current configuration"),
    reset: bool = typer.Option(False, help="Reset to default configuration"),
):
    """⚙️ Manage AAR automation configuration"""
    orchestrator = AAROrchestrator(".")

    # Check for initialization errors
    if orchestrator.context.has_error:
        console.print(f"❌ {orchestrator.context.error_message}", style="red")
        raise typer.Exit(1)

    if reset:
        orchestrator.config = orchestrator.get_default_config()
        orchestrator.save_config()
        console.print("✅ Configuration reset to defaults")

    if show or reset:
        console.print(
            Panel(
                yaml.dump(orchestrator.config, default_flow_style=False),
                title="🔧 AAR Automation Configuration",
            )
        )


if __name__ == "__main__":
    app()
