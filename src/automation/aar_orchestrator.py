#!/usr/bin/env python3
"""
AAR Auto-Update Protocol - Main Orchestrator
Task #5 Implementation: Automated task management system

This is the main automation controller that orchestrates:
- Task parsing and analysis
- Priority recommendations
- AAR updates
- File modifications with safety checks
"""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
import re

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import yaml

from task_models import TaskModel, WorkspaceSnapshot, WorkspaceMetrics
from task_parser import TaskParser, Task
from priority_engine import PriorityEngine
from dependency_analyzer import DependencyGraph, DependencyAnalyzer

app = typer.Typer(help="🎯 AAR Auto-Update Protocol - Intelligent Task Management")
console = Console()


class AAROrchestrator:
    """Main orchestrator for AAR automation"""

    def __init__(self, workspace_path: str):
        self.workspace_path = Path(workspace_path)
        self.parser = TaskParser(self.workspace_path)
        self.priority_engine = PriorityEngine()
        self.dependency_analyzer = DependencyAnalyzer()
        self.config_path = (
            self.workspace_path / "tools" / "aar-automation" / "config.yml"
        )
        self.backup_dir = self.workspace_path / "tools" / "aar-automation" / "backups"
        self.reports_dir = self.workspace_path / "tools" / "aar-automation" / "reports"

        # Ensure directories exist
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        self.load_config()

    def load_config(self) -> None:
        """Load configuration or create default"""
        if self.config_path.exists():
            with open(self.config_path, "r") as f:
                self.config = yaml.safe_load(f)
        else:
            self.config = self.get_default_config()
            self.save_config()

    def get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "automation": {
                "auto_backup": True,
                "auto_priority_update": True,
                "confidence_threshold": 0.7,
            },
            "notification": {"console_output": True, "generate_reports": True},
            "safety": {
                "dry_run_mode": False,
                "backup_retention_days": 30,
                "max_priority_changes_per_run": 3,
            },
            "analysis": {
                "enable_ml_predictions": False,  # Future feature
                "historical_analysis_days": 30,
            },
        }

    def save_config(self) -> None:
        """Save current configuration"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w") as f:
            yaml.dump(self.config, f, default_flow_style=False)

    def create_backup(self) -> Path:
        """Create backup of current task file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"WORKSPACE-TOP-25-TASKS_{timestamp}.md"

        tasks_file = self.workspace_path / "WORKSPACE-TOP-25-TASKS.md"
        if tasks_file.exists():
            shutil.copy2(tasks_file, backup_file)
            console.print(f"✅ Backup created: {backup_file.name}")
            return backup_file
        else:
            raise FileNotFoundError("Task file not found for backup (legacy Top 10 tasks archived)")

    def analyze_workspace(self) -> WorkspaceSnapshot:
        """Perform comprehensive workspace analysis"""
        console.print("🔍 Analyzing workspace tasks...")

        # Parse current tasks
        tasks = self.parser.parse_tasks()
        console.print("[bold yellow]Raw parsed tasks:[/bold yellow]")
        console.print(tasks)
        console.print(f"📋 Found {len(tasks)} tasks")

        # Convert to TaskModel for analysis
        task_models = self._convert_to_task_models(tasks)

        # Generate enhanced dependency analysis
        dependency_graph = self.dependency_analyzer.analyze_dependencies(tasks)

        # Display dependency insights
        self._display_dependency_insights(dependency_graph)

        # Generate priority recommendations
        priority_recommendations = self.priority_engine.analyze_priorities(task_models)

        # Calculate metrics
        metrics = self._calculate_workspace_metrics(task_models)

        snapshot = WorkspaceSnapshot(
            tasks=task_models,
            metrics=metrics,
            dependency_graph=[dependency_graph],  # Wrap in list
            priority_recommendations=priority_recommendations,
        )

        return snapshot

    def _convert_to_task_models(self, tasks: List[Task]) -> List[TaskModel]:
        """Convert parser tasks to full TaskModel objects"""
        task_models = []

        for task in tasks:
            # Map parser model to full model
            model = TaskModel(
                id=task.id,
                title=task.title,
                status=task.status.value,  # Convert enum
                estimated_minutes=int(task.estimated_hours * 60),
                actual_minutes=(
                    int(task.actual_hours * 60) if task.actual_hours else None
                ),
                completion_date=task.completed_date,
                dependencies=task.dependencies,
                description=task.description,
                project=task.project,
                aar_notes=None,  # Will be populated from AAR section
            )

            # Extract AAR notes if available
            if task.aar_notes:
                model.aar_notes = self._parse_aar_notes(task.aar_notes)

            task_models.append(model)

        return task_models

    def _parse_aar_notes(self, aar_text: str) -> Dict[str, Any]:
        """Parse AAR notes into structured format"""
        # Simple parsing - could be enhanced with NLP
        aar_data = {}

        # Extract key fields
        patterns = {
            "root_cause": r"Root Cause[:\s]*([^\n]+)",
            "fix_applied": r"Fix Applied[:\s]*([^\n]+)",
            "quality_impact": r"Quality Impact[:\s]*([^\n]+)",
            "next_steps": r"Next[:\s]*([^\n]+)",
        }

        for key, pattern in patterns.items():
            match = re.search(pattern, aar_text, re.IGNORECASE)
            if match:
                aar_data[key] = match.group(1).strip()

        return aar_data

    def _calculate_workspace_metrics(self, tasks: List[TaskModel]) -> WorkspaceMetrics:
        """Calculate comprehensive workspace metrics"""
        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t.is_completed])
        pending_tasks = total_tasks - completed_tasks
        blocked_tasks = 0  # Could enhance with blocked status detection

        total_estimated_hours = sum(t.estimated_minutes / 60.0 for t in tasks)
        total_actual_hours = (
            sum(t.actual_minutes / 60.0 for t in tasks if t.actual_minutes is not None)
            if any(t.actual_minutes for t in tasks)
            else None
        )

        completion_rate = completed_tasks / total_tasks if total_tasks > 0 else 0

        # Calculate time estimate accuracy
        accuracy_data = [
            abs(t.time_variance_percent or 0)
            for t in tasks
            if t.time_variance_percent is not None
        ]
        time_estimate_accuracy = (
            100 - (sum(accuracy_data) / len(accuracy_data)) if accuracy_data else None
        )

        # Provide a default value for completion_velocity (tasks per day)
        completion_velocity = None
        if total_tasks > 0:
            # Teaching: This is a placeholder; you can refine this metric as needed
            completion_velocity = completed_tasks / max(
                1, (total_tasks / 5)
            )  # Example: 5 days window

        return WorkspaceMetrics(
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            pending_tasks=pending_tasks,
            blocked_tasks=blocked_tasks,
            total_estimated_hours=total_estimated_hours,
            total_actual_hours=total_actual_hours,
            average_completion_rate=completion_rate,
            completion_velocity=completion_velocity,
            time_estimate_accuracy=time_estimate_accuracy,
        )

    def generate_report(self, snapshot: WorkspaceSnapshot) -> Path:
        """Generate comprehensive analysis report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.reports_dir / f"workspace_analysis_{timestamp}.json"

        # Convert to JSON-serializable format
        completion_rate_str = (
            f"{snapshot.metrics.average_completion_rate * 100:.1f}%"
            if snapshot.metrics.average_completion_rate is not None
            else "N/A"
        )
        report_data = {
            "timestamp": snapshot.timestamp.isoformat(),
            "summary": {
                "total_tasks": snapshot.metrics.total_tasks,
                "completed_tasks": snapshot.metrics.completed_tasks,
                "completion_rate": completion_rate_str,
                "priority_recommendations": len(snapshot.priority_recommendations),
            },
            "metrics": snapshot.metrics.dict(),
            "recommendations": [
                rec.dict() for rec in snapshot.priority_recommendations
            ],
            "dependencies": [dep.dict() for dep in snapshot.dependency_graph],
        }

        with open(report_file, "w") as f:
            json.dump(report_data, f, indent=2, default=str)

        console.print(f"📊 Report generated: {report_file.name}")
        return report_file

    def display_analysis(self, snapshot: WorkspaceSnapshot) -> None:
        """Display analysis results in rich format"""
        # Workspace Overview
        metrics_table = Table(title="📊 Workspace Metrics")
        metrics_table.add_column("Metric", style="cyan")
        metrics_table.add_column("Value", style="green")

        metrics_table.add_row("Total Tasks", str(snapshot.metrics.total_tasks))
        metrics_table.add_row("Completed", str(snapshot.metrics.completed_tasks))
        metrics_table.add_row("Pending", str(snapshot.metrics.pending_tasks))
        completion_rate_str = (
            f"{snapshot.metrics.average_completion_rate * 100:.1f}%"
            if snapshot.metrics.average_completion_rate is not None
            else "N/A"
        )
        metrics_table.add_row("Completion Rate", completion_rate_str)

        if snapshot.metrics.time_estimate_accuracy:
            metrics_table.add_row(
                "Estimate Accuracy", f"{snapshot.metrics.time_estimate_accuracy:.1f}%"
            )

        console.print(metrics_table)
        console.print()

        # Priority Recommendations
        if snapshot.priority_recommendations:
            rec_table = Table(title="🎯 Priority Recommendations")
            rec_table.add_column("Task", style="cyan")
            rec_table.add_column("Current", style="yellow")
            rec_table.add_column("Recommended", style="green")
            rec_table.add_column("Confidence", style="blue")
            rec_table.add_column("Reasoning", style="white")

            for rec in snapshot.priority_recommendations[:5]:  # Top 5
                rec_table.add_row(
                    rec.task_id,
                    rec.current_priority.value,
                    rec.recommended_priority.value,
                    f"{rec.confidence_score:.1%}",
                    (
                        rec.reasoning[:50] + "..."
                        if len(rec.reasoning) > 50
                        else rec.reasoning
                    ),
                )

            console.print(rec_table)
        else:
            console.print("✅ No priority changes recommended")

    def apply_priority_updates(self, snapshot):
        """Apply priority recommendations to the markdown file and add AAR entries."""
        tasks_file = self.workspace_path / "WORKSPACE-TOP-25-TASKS.md"
        if not tasks_file.exists():
            console.print("❌ Task file not found for update (legacy Top 10 tasks archived)", style="red")
            return
        content = tasks_file.read_text(encoding="utf-8")
        updated_content = content
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        # For each recommendation, update the relevant task section
        for rec in snapshot.priority_recommendations:
            # Teaching: Use regex to find the task header and update the priority/status line
            pattern = re.compile(
                rf"^(### ?~?{rec.task_id[1:]}\. .*?\[)([A-Z]+)(\])", re.MULTILINE
            )
            updated_content = pattern.sub(
                rf"\1{rec.recommended_priority.value.upper()}\3", updated_content
            )
            # Optionally, add an AAR entry or update status line (for demo, just add a comment)
            aar_comment = f"<!-- AAR Update {timestamp}: Priority changed from {rec.current_priority.value} to {rec.recommended_priority.value} -->"
            updated_content = updated_content.replace(
                f"### {rec.task_id[1:]}.", f"{aar_comment}\n### {rec.task_id[1:]}."
            )
        # Write the updated content back to the file
        tasks_file.write_text(updated_content, encoding="utf-8")
        console.print(
            f"✅ Updated WORKSPACE-TOP-25-TASKS.md with new priorities and AAR entries."
        )

    def _display_dependency_insights(self, dependency_graph) -> None:
        """Display enhanced dependency analysis insights"""
        console.print("\n🔗 [bold cyan]Enhanced Dependency Analysis[/bold cyan]")

        # Show cycle detection results
        if dependency_graph.cycles:
            console.print(f"⚠️  [bold red]Dependency Cycles Detected: {len(dependency_graph.cycles)}[/bold red]")
            for i, cycle in enumerate(dependency_graph.cycles):
                console.print(f"   Cycle {i+1}: {' → '.join(cycle)} → {cycle[0]}")
        else:
            console.print("✅ [green]No dependency cycles detected[/green]")

        # Show critical path
        if dependency_graph.critical_path:
            console.print(f"\n🎯 [bold yellow]Critical Path ({len(dependency_graph.critical_path)} tasks):[/bold yellow]")
            for task_id in dependency_graph.critical_path:
                if task_id in dependency_graph.nodes:
                    task = dependency_graph.nodes[task_id]
                    console.print(f"   {task_id}: {task.title}")

        # Show blocked tasks
        if dependency_graph.blocked_tasks:
            console.print(f"\n🚫 [bold red]Blocked Tasks ({len(dependency_graph.blocked_tasks)}):[/bold red]")
            for task_id in dependency_graph.blocked_tasks:
                if task_id in dependency_graph.nodes:
                    task = dependency_graph.nodes[task_id]
                    console.print(f"   {task_id}: {task.title}")

        # Show ready tasks
        if dependency_graph.ready_tasks:
            console.print(f"\n🚀 [bold green]Ready Tasks ({len(dependency_graph.ready_tasks)}):[/bold green]")
            for task_id in dependency_graph.ready_tasks:
                if task_id in dependency_graph.nodes:
                    task = dependency_graph.nodes[task_id]
                    console.print(f"   {task_id}: {task.title}")

@app.command()
def analyze(
    workspace_path: str = typer.Option(".", help="Path to workspace"),
    generate_report: bool = typer.Option(True, help="Generate analysis report"),
    display_results: bool = typer.Option(True, help="Display results in console"),
):
    """🔍 Analyze workspace tasks and generate recommendations"""
    orchestrator = AAROrchestrator(workspace_path)

    try:
        snapshot = orchestrator.analyze_workspace()

        if display_results:
            orchestrator.display_analysis(snapshot)

        if generate_report:
            report_file = orchestrator.generate_report(snapshot)
            console.print(f"\n✅ Analysis complete! Report saved to: {report_file}")

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
            # Teaching: Apply updates to the markdown file and add AAR entries
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
