#!/usr/bin/env python3
"""
AAR Type Manager - Main Orchestrator for Type-Based AAR System
Comprehensive AAR management with intelligent type classification and workflow automation

This module provides:
- Unified interface for all AAR type operations
- Integration with existing AAR automation system
- Command-line interface for manual and automated usage
- Template management and directory organization
- GitHub issue integration based on AAR type
- Workflow triggering and management

Aligns with Avanade Behavioral Anchors:
- Create the Future: Advanced AAR automation and classification
- Inspire Greatness: Comprehensive learning capture and knowledge sharing
- Accelerate Impact: Efficient, type-aware AAR workflows
"""

import argparse
import json
import sys
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

# Rich console for beautiful output
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.text import Text

# Import our AAR classification system
from aar_type_classifier import AARTypeClassifier, AARWorkflowManager, AARContent, ClassificationAction

console = Console()


class AARTypeManager:
    """
    Main orchestrator for type-based AAR system

    Provides unified interface for:
    - Creating AARs with automatic type detection
    - Managing AAR workflows based on type
    - Integrating with existing AAR automation
    - Template management and customization
    - Workflow triggering and scheduling
    """

    def __init__(self, workspace_path: Optional[Path] = None):
        """Initialize AAR Type Manager"""
        self.workspace_path = workspace_path or Path.cwd()
        self.aar_automation_path = self.workspace_path / "tools" / "aar-automation"
        self.config_path = self.aar_automation_path / "config" / "aar-types-config.yaml"

        # Initialize components
        self.classifier = AARTypeClassifier(self.config_path)
        self.workflow_manager = AARWorkflowManager(self.classifier, self.workspace_path)

        # Setup logging
        self.logger = self._setup_logging()

        # Load configuration
        self.config = self._load_config()

    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # File handler
        log_file = self.aar_automation_path / "logs" / "aar-type-manager.log"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        return logger

    def _load_config(self) -> Dict[str, Any]:
        """Load AAR types configuration"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
            return {}

    def create_aar(self,
                   title: str,
                   content: str = "",
                   aar_type: Optional[str] = None,
                   metadata: Optional[Dict[str, Any]] = None,
                   interactive: bool = True) -> Dict[str, Any]:
        """
        Create a new AAR with automatic type detection and workflow execution

        Args:
            title: AAR title
            content: AAR content (can be empty for template-based creation)
            aar_type: Force specific AAR type (skips classification)
            metadata: Additional metadata
            interactive: Whether to prompt user for decisions

        Returns:
            Dict with creation results and next steps
        """
        try:
            console.print(Panel.fit(f"🎯 Creating AAR: {title}", style="bold blue"))

            # Prepare AAR content for analysis
            aar_content = AARContent(
                title=title,
                content=content,
                metadata=metadata or {},
                timing_context=self._get_timing_context(),
                user_history=self._get_user_history()
            )

            # Process through workflow manager
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
                task = progress.add_task("Analyzing AAR content...", total=None)

                workflow_result = self.workflow_manager.process_aar_request(
                    aar_content,
                    force_type=aar_type
                )

                progress.update(task, description="Classification complete!")

            # Handle the result based on classification
            if workflow_result["status"] == "error":
                console.print(f"[bold red]Error:[/bold red] {workflow_result['message']}")
                return workflow_result

            classification = workflow_result["workflow_results"]["classification"]
            type_def = workflow_result["workflow_results"]["type_definition"]

            # Display classification results
            self._display_classification_results(classification, type_def)

            # Handle different classification actions
            if interactive and workflow_result["requires_manual_action"]:
                confirmed_type = self._handle_interactive_classification(classification, type_def)
                if confirmed_type != classification.aar_type:
                    # Re-process with confirmed type
                    workflow_result = self.workflow_manager.process_aar_request(
                        aar_content,
                        force_type=confirmed_type
                    )
                    classification = workflow_result["workflow_results"]["classification"]
                    type_def = workflow_result["workflow_results"]["type_definition"]

            # Create the AAR file
            aar_file_path = self._create_aar_file(
                aar_content,
                classification,
                type_def,
                workflow_result["workflow_results"]["output_paths"]
            )

            # Execute type-specific workflows
            workflow_outputs = self._execute_type_workflows(classification, type_def, aar_file_path)

            # Display success summary
            self._display_success_summary(classification, type_def, aar_file_path, workflow_outputs)

            return {
                "status": "success",
                "aar_file": str(aar_file_path),
                "aar_type": classification.aar_type,
                "classification": classification,
                "workflow_outputs": workflow_outputs
            }

        except Exception as e:
            self.logger.error(f"Error creating AAR: {e}")
            console.print(f"[bold red]Error creating AAR:[/bold red] {e}")
            return {"status": "error", "message": str(e)}

    def list_aar_types(self) -> None:
        """Display all available AAR types with descriptions"""
        console.print(Panel.fit("📋 Available AAR Types", style="bold blue"))

        types_table = Table(title="AAR Type Definitions")
        types_table.add_column("Type", style="cyan", width=20)
        types_table.add_column("Display Name", style="green", width=25)
        types_table.add_column("Description", style="white", width=50)
        types_table.add_column("Auto Issues", style="yellow", width=10)

        for type_name in self.classifier.list_available_types():
            type_def = self.classifier.get_type_definition(type_name)
            types_table.add_row(
                type_name,
                type_def.display_name,
                type_def.description[:47] + "..." if len(type_def.description) > 50 else type_def.description,
                "✅" if type_def.auto_create_issues else "❌"
            )

        console.print(types_table)

    def analyze_general_aars(self) -> Dict[str, Any]:
        """
        Analyze General AARs for reclassification opportunities and new type suggestions

        Returns:
            Dict with analysis results and recommendations
        """
        console.print(Panel.fit("🔍 Analyzing General AARs for Classification Improvements", style="bold blue"))

        # Find General AARs
        general_aar_dir = self.aar_automation_path / "reports" / "general"
        general_aars = []

        if general_aar_dir.exists():
            for aar_file in general_aar_dir.glob("*.md"):
                try:
                    content = aar_file.read_text(encoding='utf-8')
                    title = aar_file.stem.replace('_AAR', '').replace('_', ' ')

                    general_aars.append(AARContent(
                        title=title,
                        content=content,
                        metadata={"file_path": str(aar_file)}
                    ))
                except Exception as e:
                    self.logger.warning(f"Could not read {aar_file}: {e}")

        console.print(f"Found {len(general_aars)} General AARs to analyze")

        if len(general_aars) == 0:
            console.print("[yellow]No General AARs found to analyze[/yellow]")
            return {"status": "no_data", "message": "No General AARs found"}

        # Analyze each for reclassification
        reclassification_candidates = []

        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            task = progress.add_task("Analyzing AARs...", total=len(general_aars))

            for aar in general_aars:
                classification = self.classifier.classify_aar(aar)

                if (classification.aar_type != "general" and
                    classification.confidence > 0.5):
                    reclassification_candidates.append({
                        "aar": aar,
                        "suggested_type": classification.aar_type,
                        "confidence": classification.confidence,
                        "reasoning": classification.reasoning
                    })

                progress.advance(task)

        # Suggest new types
        new_type_suggestion = self.classifier.suggest_new_type(general_aars)

        # Display results
        if reclassification_candidates:
            self._display_reclassification_candidates(reclassification_candidates)

        if new_type_suggestion:
            self._display_new_type_suggestion(new_type_suggestion)

        return {
            "status": "success",
            "reclassification_candidates": len(reclassification_candidates),
            "new_type_suggestion": new_type_suggestion,
            "total_analyzed": len(general_aars)
        }

    def reclassify_aar(self, aar_file_path: Path, new_type: str) -> Dict[str, Any]:
        """
        Reclassify an existing AAR to a different type

        Args:
            aar_file_path: Path to existing AAR file
            new_type: New AAR type to assign

        Returns:
            Dict with reclassification results
        """
        try:
            # Validate new type
            type_def = self.classifier.get_type_definition(new_type)
            if not type_def:
                return {"status": "error", "message": f"Unknown AAR type: {new_type}"}

            # Read existing AAR
            content = aar_file_path.read_text(encoding='utf-8')
            title = aar_file_path.stem.replace('_AAR', '').replace('_', ' ')

            # Create new location
            new_dir = self.aar_automation_path / "reports" / type_def.directory.replace("reports/", "")
            new_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
            new_file_path = new_dir / f"{timestamp}_{new_type}_AAR_reclassified.md"

            # Update content with reclassification note
            reclassification_note = f"""
---
**RECLASSIFICATION NOTE**
- Original Type: General AAR
- New Type: {type_def.display_name}
- Reclassified: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- Original File: {aar_file_path.name}
---

"""
            updated_content = reclassification_note + content

            # Write new file
            new_file_path.write_text(updated_content, encoding='utf-8')

            # Archive original (don't delete)
            archive_dir = aar_file_path.parent / "archived"
            archive_dir.mkdir(exist_ok=True)
            archive_path = archive_dir / f"archived_{aar_file_path.name}"
            aar_file_path.rename(archive_path)

            console.print(f"[green]✅ Successfully reclassified AAR[/green]")
            console.print(f"New location: {new_file_path}")
            console.print(f"Original archived: {archive_path}")

            return {
                "status": "success",
                "new_file": str(new_file_path),
                "archived_file": str(archive_path),
                "new_type": new_type
            }

        except Exception as e:
            self.logger.error(f"Error reclassifying AAR: {e}")
            return {"status": "error", "message": str(e)}

    def _get_timing_context(self) -> str:
        """Get current timing context for classification"""
        now = datetime.now()
        hour = now.hour

        if 17 <= hour <= 19:
            return "end of day"
        elif 8 <= hour <= 10:
            return "start of day"
        elif 12 <= hour <= 14:
            return "midday"
        else:
            return "general"

    def _get_user_history(self) -> List[str]:
        """Get user's AAR history for pattern analysis"""
        # This is a simplified implementation
        # In a full system, this would query a database or file system
        history = []

        # Scan recent AARs in all directories
        reports_dir = self.aar_automation_path / "reports"
        if reports_dir.exists():
            for type_dir in reports_dir.iterdir():
                if type_dir.is_dir():
                    for aar_file in type_dir.glob("*.md"):
                        if "_AAR" in aar_file.name:
                            history.append(type_dir.name)

        return history[-10:]  # Last 10 AARs

    def _display_classification_results(self, classification, type_def):
        """Display classification results to user"""
        # Classification summary panel
        summary_text = f"""
[bold]Classified Type:[/bold] {type_def.display_name}
[bold]Confidence:[/bold] {classification.confidence:.1%} ({classification.confidence_level.value})
[bold]Action:[/bold] {classification.action.value.replace('_', ' ').title()}
[bold]Auto-create Issues:[/bold] {'Yes' if type_def.auto_create_issues else 'No'}
"""

        console.print(Panel(summary_text, title="🎯 Classification Results", border_style="green"))

        # Reasoning
        if classification.reasoning:
            reasoning_table = Table(title="Classification Reasoning")
            reasoning_table.add_column("Reasoning", style="white")
            for reason in classification.reasoning[:5]:  # Top 5 reasons
                reasoning_table.add_row(reason)
            console.print(reasoning_table)

        # Alternatives
        if classification.alternative_types:
            alt_table = Table(title="Alternative Types Considered")
            alt_table.add_column("Type", style="cyan")
            alt_table.add_column("Confidence", style="yellow")

            for alt_type, confidence in classification.alternative_types[:3]:
                alt_table.add_row(alt_type, f"{confidence:.1%}")
            console.print(alt_table)

    def _handle_interactive_classification(self, classification, type_def) -> str:
        """Handle interactive classification confirmation"""
        if classification.action == ClassificationAction.SUGGEST_WITH_CONFIRMATION:
            confirmed = Confirm.ask(f"Create {type_def.display_name}?")
            if not confirmed:
                # Show alternatives
                alternatives = [alt[0] for alt in classification.alternative_types[:3]]
                alternatives.append("general")

                choice = Prompt.ask(
                    "Select AAR type",
                    choices=alternatives,
                    default="general"
                )
                return choice

        elif classification.action == ClassificationAction.MANUAL_CLASSIFICATION:
            available_types = self.classifier.list_available_types()
            choice = Prompt.ask(
                "Classification confidence too low. Select AAR type",
                choices=available_types,
                default="general"
            )
            return choice

        return classification.aar_type

    def _create_aar_file(self, aar_content, classification, type_def, output_paths) -> Path:
        """Create AAR file using appropriate template"""
        template_path = Path(output_paths["template_path"])
        output_file = Path(output_paths["report_file"])

        # Read template
        if template_path.exists():
            template_content = template_path.read_text(encoding='utf-8')
        else:
            # Fallback to basic template
            template_content = f"""# {type_def.display_name}
**Date:** {datetime.now().strftime('%Y-%m-%d')}
**Type:** {type_def.display_name}

## Content
{aar_content.content}

## Generated
- **Timestamp:** {datetime.now().isoformat()}
- **Classification Confidence:** {classification.confidence:.1%}
- **AAR ID:** {output_file.stem}
"""

        # Basic template variable substitution
        template_vars = {
            "date": datetime.now().strftime('%Y-%m-%d'),
            "author": "User",  # Could be enhanced to get actual user
            "aar_id": output_file.stem,
            "generation_timestamp": datetime.now().isoformat(),
            "classification_confidence": f"{classification.confidence:.1%}",
            "suggested_type": classification.aar_type,
            "review_status": "pending" if classification.requires_review else "complete"
        }

        # Simple template substitution
        filled_template = template_content
        for var, value in template_vars.items():
            filled_template = filled_template.replace(f"{{{var}}}", str(value))

        # Write file
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(filled_template, encoding='utf-8')

        return output_file

    def _execute_type_workflows(self, classification, type_def, aar_file_path) -> Dict[str, Any]:
        """Execute type-specific workflows"""
        workflows = {}

        # Auto-create GitHub issues if configured
        if type_def.auto_create_issues:
            workflows["github_issues"] = "Would create GitHub issues (not implemented)"

        # Execute special workflows
        if type_def.special_workflows:
            for workflow in type_def.special_workflows:
                if workflow == "classification_review":
                    workflows["classification_review"] = "Scheduled for review"
                elif workflow == "type_suggestion":
                    workflows["type_suggestion"] = "Added to type suggestion analysis"

        return workflows

    def _display_success_summary(self, classification, type_def, aar_file_path, workflow_outputs):
        """Display success summary"""
        success_text = f"""
[bold green]✅ AAR Created Successfully![/bold green]

[bold]File:[/bold] {aar_file_path}
[bold]Type:[/bold] {type_def.display_name}
[bold]Directory:[/bold] {aar_file_path.parent}
"""

        if workflow_outputs:
            success_text += f"\n[bold]Workflows Executed:[/bold]\n"
            for workflow, result in workflow_outputs.items():
                success_text += f"  • {workflow}: {result}\n"

        console.print(Panel(success_text, title="🎉 Success", border_style="green"))

    def _display_reclassification_candidates(self, candidates):
        """Display reclassification candidates"""
        console.print("\n[bold yellow]📋 Reclassification Candidates[/bold yellow]")

        reclass_table = Table()
        reclass_table.add_column("AAR", style="cyan")
        reclass_table.add_column("Suggested Type", style="green")
        reclass_table.add_column("Confidence", style="yellow")
        reclass_table.add_column("Top Reason", style="white")

        for candidate in candidates:
            aar_title = candidate["aar"].title[:30] + "..." if len(candidate["aar"].title) > 30 else candidate["aar"].title
            top_reason = candidate["reasoning"][0] if candidate["reasoning"] else "No specific reason"

            reclass_table.add_row(
                aar_title,
                candidate["suggested_type"],
                f"{candidate['confidence']:.1%}",
                top_reason[:40] + "..." if len(top_reason) > 40 else top_reason
            )

        console.print(reclass_table)

    def _display_new_type_suggestion(self, suggestion):
        """Display new type suggestion"""
        console.print("\n[bold blue]💡 New AAR Type Suggestion[/bold blue]")

        suggestion_text = f"""
[bold]Suggested Name:[/bold] {suggestion['suggested_name']}
[bold]Display Name:[/bold] {suggestion['display_name']}
[bold]Description:[/bold] {suggestion['description']}
[bold]Based on:[/bold] {suggestion['sample_count']} General AARs
[bold]Common Keywords:[/bold] {', '.join(suggestion['common_patterns'])}
"""

        console.print(Panel(suggestion_text, title="New Type Suggestion", border_style="blue"))


def main():
    """Command-line interface for AAR Type Manager"""
    parser = argparse.ArgumentParser(
        description="AAR Type Manager - Intelligent AAR creation and classification",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create end-of-day AAR (auto-detected)
  python aar-type-manager.py create --title "End of Day Review" --interactive

  # Create task completion AAR
  python aar-type-manager.py create --title "Auth System Complete" --type task_completion

  # List available AAR types
  python aar-type-manager.py list-types

  # Analyze General AARs for improvements
  python aar-type-manager.py analyze-general

  # Reclassify an AAR
  python aar-type-manager.py reclassify --file "path/to/aar.md" --type incident_problem
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Create AAR command
    create_parser = subparsers.add_parser('create', help='Create a new AAR')
    create_parser.add_argument('--title', required=True, help='AAR title')
    create_parser.add_argument('--content', default='', help='AAR content (optional)')
    create_parser.add_argument('--type', help='Force specific AAR type')
    create_parser.add_argument('--interactive', action='store_true', help='Interactive mode')
    create_parser.add_argument('--workspace', help='Workspace path')

    # List types command
    list_parser = subparsers.add_parser('list-types', help='List available AAR types')
    list_parser.add_argument('--workspace', help='Workspace path')

    # Analyze general AARs command
    analyze_parser = subparsers.add_parser('analyze-general', help='Analyze General AARs')
    analyze_parser.add_argument('--workspace', help='Workspace path')

    # Reclassify command
    reclass_parser = subparsers.add_parser('reclassify', help='Reclassify an existing AAR')
    reclass_parser.add_argument('--file', required=True, help='Path to AAR file')
    reclass_parser.add_argument('--type', required=True, help='New AAR type')
    reclass_parser.add_argument('--workspace', help='Workspace path')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Initialize manager
    workspace_path = Path(args.workspace) if hasattr(args, 'workspace') and args.workspace else None
    manager = AARTypeManager(workspace_path)

    # Execute commands
    try:
        if args.command == 'create':
            result = manager.create_aar(
                title=args.title,
                content=args.content,
                aar_type=args.type,
                interactive=args.interactive
            )

            if result["status"] == "error":
                sys.exit(1)

        elif args.command == 'list-types':
            manager.list_aar_types()

        elif args.command == 'analyze-general':
            result = manager.analyze_general_aars()
            console.print(f"\nAnalysis complete: {result}")

        elif args.command == 'reclassify':
            file_path = Path(args.file)
            if not file_path.exists():
                console.print(f"[red]Error: File not found: {file_path}[/red]")
                sys.exit(1)

            result = manager.reclassify_aar(file_path, args.type)
            if result["status"] == "error":
                console.print(f"[red]Error: {result['message']}[/red]")
                sys.exit(1)

    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
