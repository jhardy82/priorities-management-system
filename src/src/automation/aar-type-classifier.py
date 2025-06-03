#!/usr/bin/env python3
"""
AAR Type Classification System
Comprehensive AAR type detection, classification, and workflow management

This module provides:
- Automatic AAR type detection based on content analysis
- Confidence scoring for classifications
- Workflow management for different AAR types
- Template selection and directory management
- Integration with existing AAR automation system

Aligns with Avanade Behavioral Anchors:
- Create the Future: Innovative classification and automation
- Inspire Greatness: Comprehensive learning capture across all activities
- Accelerate Impact: Efficient categorization and automated workflows
"""

import re
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import logging
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


class ConfidenceLevel(Enum):
    """Classification confidence levels"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


class ClassificationAction(Enum):
    """Actions to take based on classification confidence"""
    AUTO_CLASSIFY = "auto_classify"
    SUGGEST_WITH_CONFIRMATION = "suggest_with_confirmation"
    MANUAL_CLASSIFICATION = "manual_classification"
    CREATE_GENERAL_AAR = "create_general_aar"


@dataclass
class AARTypeDefinition:
    """Definition of an AAR type"""
    name: str
    display_name: str
    description: str
    confidence_keywords: Dict[str, List[str]]
    triggers: List[Dict[str, Any]]
    template: str
    required_sections: List[str]
    auto_create_issues: bool
    directory: str
    special_workflows: Optional[List[str]] = None


@dataclass
class ClassificationResult:
    """Result of AAR type classification"""
    aar_type: str
    confidence: float
    confidence_level: ConfidenceLevel
    action: ClassificationAction
    reasoning: List[str]
    alternative_types: List[Tuple[str, float]]
    requires_review: bool


@dataclass
class AARContent:
    """Structured representation of AAR content for analysis"""
    title: str
    content: str
    metadata: Dict[str, Any]
    timing_context: Optional[str] = None
    user_history: Optional[List[str]] = None


class AARTypeClassifier:
    """
    Intelligent AAR type classification system

    Uses multi-factor analysis to determine appropriate AAR type:
    - Keyword matching with weighted scoring
    - Content structure analysis
    - Timing and context evaluation
    - User historical patterns
    """

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize classifier with configuration"""
        self.config_path = config_path or Path(__file__).parent / "config" / "aar-types-config.yaml"
        self.config = self._load_config()
        self.aar_types = self._parse_aar_types()
        self.classification_config = self.config.get('classification', {})
        self.logger = logging.getLogger(__name__)

    def _load_config(self) -> Dict[str, Any]:
        """Load AAR types configuration"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.error(f"Failed to load config from {self.config_path}: {e}")
            return {}

    def _parse_aar_types(self) -> Dict[str, AARTypeDefinition]:
        """Parse AAR type definitions from config"""
        types = {}
        for name, config in self.config.get('aar_types', {}).items():
            types[name] = AARTypeDefinition(
                name=name,
                display_name=config['display_name'],
                description=config['description'],
                confidence_keywords=config['confidence_keywords'],
                triggers=config['triggers'],
                template=config['template'],
                required_sections=config['required_sections'],
                auto_create_issues=config['auto_create_issues'],
                directory=config['directory'],
                special_workflows=config.get('special_workflows')
            )
        return types

    def classify_aar(self, content: AARContent) -> ClassificationResult:
        """
        Classify AAR content and determine appropriate type

        Args:
            content: AARContent object with title, content, and metadata

        Returns:
            ClassificationResult with type, confidence, and recommended action
        """
        # Analyze content for each AAR type
        type_scores = {}
        reasoning_details = {}

        for aar_type_name, aar_type in self.aar_types.items():
            score, reasoning = self._calculate_type_score(content, aar_type)
            type_scores[aar_type_name] = score
            reasoning_details[aar_type_name] = reasoning

        # Find best match
        best_type = max(type_scores.items(), key=lambda x: x[1])
        best_type_name, best_score = best_type

        # Sort alternatives
        sorted_scores = sorted(type_scores.items(), key=lambda x: x[1], reverse=True)
        alternatives = [(name, score) for name, score in sorted_scores[1:4]]  # Top 3 alternatives

        # Determine confidence level and action
        confidence_level = self._get_confidence_level(best_score)
        action = self._get_classification_action(confidence_level, best_score)

        # Build reasoning
        reasoning = reasoning_details.get(best_type_name, [])

        # Determine if review is required
        requires_review = (
            confidence_level in [ConfidenceLevel.LOW, ConfidenceLevel.NONE] or
            best_type_name == "general" or
            action == ClassificationAction.MANUAL_CLASSIFICATION
        )

        return ClassificationResult(
            aar_type=best_type_name,
            confidence=best_score,
            confidence_level=confidence_level,
            action=action,
            reasoning=reasoning,
            alternative_types=alternatives,
            requires_review=requires_review
        )

    def _calculate_type_score(self, content: AARContent, aar_type: AARTypeDefinition) -> Tuple[float, List[str]]:
        """Calculate confidence score for a specific AAR type"""
        scores = {}
        reasoning = []
        weights = self.classification_config.get('analysis_weights', {})

        # Keyword analysis
        keyword_score, keyword_reasoning = self._analyze_keywords(content, aar_type)
        scores['keywords'] = keyword_score * weights.get('keywords', 0.4)
        reasoning.extend(keyword_reasoning)

        # Content structure analysis
        structure_score, structure_reasoning = self._analyze_content_structure(content, aar_type)
        scores['content_structure'] = structure_score * weights.get('content_structure', 0.3)
        reasoning.extend(structure_reasoning)

        # Timing context analysis
        timing_score, timing_reasoning = self._analyze_timing_context(content, aar_type)
        scores['timing_context'] = timing_score * weights.get('timing_context', 0.2)
        reasoning.extend(timing_reasoning)

        # User history analysis
        history_score, history_reasoning = self._analyze_user_history(content, aar_type)
        scores['user_history'] = history_score * weights.get('user_history', 0.1)
        reasoning.extend(history_reasoning)

        total_score = sum(scores.values())

        return total_score, reasoning

    def _analyze_keywords(self, content: AARContent, aar_type: AARTypeDefinition) -> Tuple[float, List[str]]:
        """Analyze keyword matches for AAR type"""
        text = f"{content.title} {content.content}".lower()
        total_score = 0.0
        reasoning = []

        keywords = aar_type.confidence_keywords

        # High confidence keywords (weight: 1.0)
        high_matches = 0
        for keyword in keywords.get('high', []):
            if keyword.lower() in text:
                high_matches += 1
                reasoning.append(f"High confidence keyword found: '{keyword}'")

        # Medium confidence keywords (weight: 0.6)
        medium_matches = 0
        for keyword in keywords.get('medium', []):
            if keyword.lower() in text:
                medium_matches += 1
                reasoning.append(f"Medium confidence keyword found: '{keyword}'")

        # Low confidence keywords (weight: 0.3)
        low_matches = 0
        for keyword in keywords.get('low', []):
            if keyword.lower() in text:
                low_matches += 1
                reasoning.append(f"Low confidence keyword found: '{keyword}'")

        # Calculate weighted score
        total_score = (
            high_matches * 1.0 +
            medium_matches * 0.6 +
            low_matches * 0.3
        )

        # Normalize by maximum possible score
        max_possible = len(keywords.get('high', [])) * 1.0 + len(keywords.get('medium', [])) * 0.6 + len(keywords.get('low', [])) * 0.3
        if max_possible > 0:
            total_score = min(total_score / max_possible, 1.0)

        return total_score, reasoning

    def _analyze_content_structure(self, content: AARContent, aar_type: AARTypeDefinition) -> Tuple[float, List[str]]:
        """Analyze content structure against expected sections"""
        text = content.content.lower()
        reasoning = []
        matches = 0

        required_sections = aar_type.required_sections

        for section in required_sections:
            # Convert section names to potential headers
            section_patterns = [
                section.replace('_', ' '),
                section.replace('_', '-'),
                section,
                section.title(),
                section.upper()
            ]

            for pattern in section_patterns:
                if pattern.lower() in text:
                    matches += 1
                    reasoning.append(f"Found expected section: '{section}'")
                    break

        # Calculate score as percentage of required sections found
        score = matches / len(required_sections) if required_sections else 0.0

        return score, reasoning

    def _analyze_timing_context(self, content: AARContent, aar_type: AARTypeDefinition) -> Tuple[float, List[str]]:
        """Analyze timing context for type appropriateness"""
        timing_context = content.timing_context
        reasoning = []
        score = 0.0

        if not timing_context:
            return score, reasoning

        # Check for timing-specific indicators
        timing_indicators = {
            'end_of_day': ['evening', 'end of day', '6pm', '18:00', 'eod'],
            'task_completion': ['completed', 'finished', 'done', 'delivered'],
            'incident_problem': ['urgent', 'critical', 'outage', 'down'],
            'project_sprint': ['sprint end', 'iteration', 'milestone'],
            'team_collaboration': ['team meeting', 'retrospective', 'standup'],
            'deployment_release': ['deployed', 'released', 'production', 'go-live']
        }

        type_indicators = timing_indicators.get(aar_type.name, [])
        context_lower = timing_context.lower()

        for indicator in type_indicators:
            if indicator in context_lower:
                score += 0.3  # Each matching indicator adds 0.3
                reasoning.append(f"Timing context matches: '{indicator}'")

        return min(score, 1.0), reasoning

    def _analyze_user_history(self, content: AARContent, aar_type: AARTypeDefinition) -> Tuple[float, List[str]]:
        """Analyze user's historical AAR patterns"""
        user_history = content.user_history
        reasoning = []
        score = 0.0

        if not user_history:
            return score, reasoning

        # Count previous AARs of this type
        type_count = user_history.count(aar_type.name)
        total_aars = len(user_history)

        if total_aars > 0:
            # Users tend to create similar types of AARs
            type_frequency = type_count / total_aars
            score = type_frequency * 0.5  # Max contribution is 0.5

            if type_frequency > 0.3:
                reasoning.append(f"User frequently creates {aar_type.display_name} AARs ({type_frequency:.1%})")

        return score, reasoning

    def _get_confidence_level(self, score: float) -> ConfidenceLevel:
        """Determine confidence level from score"""
        thresholds = self.classification_config.get('confidence_thresholds', {})

        if score >= thresholds.get('auto_classify', 0.8):
            return ConfidenceLevel.HIGH
        elif score >= thresholds.get('suggest_type', 0.6):
            return ConfidenceLevel.MEDIUM
        elif score >= thresholds.get('manual_review', 0.4):
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.NONE

    def _get_classification_action(self, confidence_level: ConfidenceLevel, score: float) -> ClassificationAction:
        """Determine action based on confidence level"""
        workflows = self.classification_config.get('workflows', {})

        if confidence_level == ConfidenceLevel.HIGH:
            return ClassificationAction.AUTO_CLASSIFY
        elif confidence_level == ConfidenceLevel.MEDIUM:
            return ClassificationAction.SUGGEST_WITH_CONFIRMATION
        elif confidence_level == ConfidenceLevel.LOW:
            return ClassificationAction.MANUAL_CLASSIFICATION
        else:
            return ClassificationAction.CREATE_GENERAL_AAR

    def get_type_definition(self, aar_type: str) -> Optional[AARTypeDefinition]:
        """Get definition for a specific AAR type"""
        return self.aar_types.get(aar_type)

    def list_available_types(self) -> List[str]:
        """List all available AAR types"""
        return list(self.aar_types.keys())

    def suggest_new_type(self, general_aars: List[AARContent]) -> Optional[Dict[str, Any]]:
        """
        Analyze patterns in general AARs to suggest new type definitions

        Args:
            general_aars: List of AARContent objects classified as 'general'

        Returns:
            Dict with suggested new type definition or None
        """
        if len(general_aars) < 3:  # Need at least 3 examples
            return None

        # Analyze common keywords
        all_text = " ".join([f"{aar.title} {aar.content}" for aar in general_aars])
        words = re.findall(r'\b\w+\b', all_text.lower())

        # Find most common words (excluding common English words)
        common_stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those'}
        filtered_words = [word for word in words if word not in common_stopwords and len(word) > 3]

        from collections import Counter
        word_counts = Counter(filtered_words)
        top_keywords = [word for word, count in word_counts.most_common(10) if count >= 2]

        if len(top_keywords) >= 3:
            suggested_name = "_".join(top_keywords[:2])

            return {
                "suggested_name": suggested_name,
                "display_name": " ".join(word.title() for word in top_keywords[:2]) + " AAR",
                "description": f"AAR type for {' and '.join(top_keywords[:3])} related activities",
                "confidence_keywords": {
                    "high": top_keywords[:3],
                    "medium": top_keywords[3:6],
                    "low": top_keywords[6:10]
                },
                "sample_count": len(general_aars),
                "common_patterns": top_keywords
            }

        return None


class AARWorkflowManager:
    """
    Manages AAR workflows and automation based on type classification

    Handles:
    - Workflow triggering based on AAR type
    - Template selection and directory management
    - Integration with existing AAR automation
    - GitHub issue creation workflows
    """

    def __init__(self, classifier: AARTypeClassifier, workspace_path: Path):
        """Initialize workflow manager"""
        self.classifier = classifier
        self.workspace_path = workspace_path
        self.aar_base_path = workspace_path / "tools" / "aar-automation"
        self.templates_path = self.aar_base_path / "templates"
        self.logger = logging.getLogger(__name__)

    def process_aar_request(self, content: AARContent, force_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Process an AAR request with classification and workflow execution

        Args:
            content: AARContent to classify and process
            force_type: Optional type override (for manual classification)

        Returns:
            Dict with processing results and recommendations
        """
        # Classify AAR type
        if force_type:
            classification = ClassificationResult(
                aar_type=force_type,
                confidence=1.0,
                confidence_level=ConfidenceLevel.HIGH,
                action=ClassificationAction.AUTO_CLASSIFY,
                reasoning=[f"Manually specified type: {force_type}"],
                alternative_types=[],
                requires_review=False
            )
        else:
            classification = self.classifier.classify_aar(content)

        # Get type definition
        type_def = self.classifier.get_type_definition(classification.aar_type)
        if not type_def:
            return {
                "status": "error",
                "message": f"Unknown AAR type: {classification.aar_type}",
                "classification": classification
            }

        # Determine output paths
        report_dir = self.aar_base_path / "reports" / type_def.directory.replace("reports/", "")
        report_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
        report_file = report_dir / f"{timestamp}_{classification.aar_type}_AAR.md"

        # Select template
        template_path = self.templates_path / type_def.template

        # Prepare workflow execution
        workflow_results = {
            "classification": classification,
            "type_definition": type_def,
            "output_paths": {
                "report_file": str(report_file),
                "report_directory": str(report_dir),
                "template_path": str(template_path)
            },
            "recommendations": self._generate_recommendations(classification, type_def),
            "next_steps": self._determine_next_steps(classification, type_def)
        }

        return {
            "status": "success",
            "workflow_results": workflow_results,
            "requires_manual_action": classification.requires_review,
            "suggested_actions": self._get_suggested_actions(classification)
        }

    def _generate_recommendations(self, classification: ClassificationResult, type_def: AARTypeDefinition) -> List[str]:
        """Generate recommendations based on classification results"""
        recommendations = []

        # Confidence-based recommendations
        if classification.confidence_level == ConfidenceLevel.LOW:
            recommendations.append("Consider reviewing classification - confidence is low")
            recommendations.append(f"Alternative types to consider: {', '.join([alt[0] for alt in classification.alternative_types[:2]])}")

        # Type-specific recommendations
        if type_def.auto_create_issues:
            recommendations.append("This AAR type automatically creates GitHub issues for action items")

        if type_def.special_workflows:
            recommendations.append(f"Special workflows will be triggered: {', '.join(type_def.special_workflows)}")

        # Section recommendations
        if type_def.required_sections:
            recommendations.append(f"Include these required sections: {', '.join(type_def.required_sections)}")

        return recommendations

    def _determine_next_steps(self, classification: ClassificationResult, type_def: AARTypeDefinition) -> List[str]:
        """Determine next steps based on classification"""
        next_steps = []

        if classification.action == ClassificationAction.AUTO_CLASSIFY:
            next_steps.append(f"Create {type_def.display_name} using template: {type_def.template}")
            if type_def.auto_create_issues:
                next_steps.append("GitHub issues will be created automatically from action items")

        elif classification.action == ClassificationAction.SUGGEST_WITH_CONFIRMATION:
            next_steps.append(f"Confirm if this should be a {type_def.display_name}")
            next_steps.append(f"Alternative options: {', '.join([alt[0] for alt in classification.alternative_types[:2]])}")

        elif classification.action == ClassificationAction.MANUAL_CLASSIFICATION:
            next_steps.append("Manual classification required - confidence too low")
            next_steps.append(f"Suggested types: {', '.join([alt[0] for alt in classification.alternative_types[:3]])}")

        elif classification.action == ClassificationAction.CREATE_GENERAL_AAR:
            next_steps.append("Create General AAR - no specific type detected")
            next_steps.append("Review for potential new type creation")

        return next_steps

    def _get_suggested_actions(self, classification: ClassificationResult) -> List[str]:
        """Get user-actionable suggestions"""
        actions = []

        if classification.requires_review:
            actions.append("review_classification")

        if classification.confidence < 0.6:
            actions.append("consider_alternative_types")

        if classification.aar_type == "general":
            actions.append("suggest_reclassification")

        return actions


def main():
    """Demo the AAR type classification system"""
    console.print(Panel.fit("🎯 AAR Type Classification System Demo", style="bold blue"))

    # Initialize classifier
    classifier = AARTypeClassifier()
    workspace_path = Path("/workspaces/PowerCompany")
    workflow_manager = AARWorkflowManager(classifier, workspace_path)

    # Demo classification
    sample_contents = [
        AARContent(
            title="End of Day Review - Project Progress",
            content="Today's accomplishments include completing the authentication module and fixing three critical bugs. Tomorrow's priorities focus on the user interface components and integration testing. Lessons learned: early testing prevents last-minute issues.",
            metadata={"timestamp": "2024-12-30T18:00:00"},
            timing_context="end of day"
        ),
        AARContent(
            title="Task Completion - Authentication System Implementation",
            content="Successfully implemented OAuth 2.0 authentication system. Challenges included certificate configuration and user session management. Approach taken was incremental development with continuous testing. Impact: enables secure user access for the entire application.",
            metadata={"task_id": "AUTH-001"},
            timing_context="task completed"
        ),
        AARContent(
            title="System Outage Analysis",
            content="Critical database failure occurred at 2:00 PM causing 45-minute outage. Root cause identified as disk space exhaustion. Immediate resolution involved clearing logs and adding monitoring. Preventive measures include automated disk cleanup and alerting.",
            metadata={"severity": "high"},
            timing_context="incident resolved"
        )
    ]

    # Display available types
    types_table = Table(title="Available AAR Types")
    types_table.add_column("Type", style="cyan")
    types_table.add_column("Display Name", style="green")
    types_table.add_column("Description", style="white")

    for type_name in classifier.list_available_types():
        type_def = classifier.get_type_definition(type_name)
        types_table.add_row(type_name, type_def.display_name, type_def.description[:60] + "...")

    console.print(types_table)
    console.print()

    # Classify sample content
    for i, content in enumerate(sample_contents, 1):
        console.print(f"[bold yellow]Sample {i}: {content.title}[/bold yellow]")

        classification = classifier.classify_aar(content)
        workflow_result = workflow_manager.process_aar_request(content)

        # Display results
        result_table = Table()
        result_table.add_column("Property", style="cyan")
        result_table.add_column("Value", style="white")

        result_table.add_row("Classified Type", classification.aar_type)
        result_table.add_row("Confidence", f"{classification.confidence:.2%}")
        result_table.add_row("Confidence Level", classification.confidence_level.value)
        result_table.add_row("Action", classification.action.value)
        result_table.add_row("Requires Review", str(classification.requires_review))
        result_table.add_row("Top Reasoning", classification.reasoning[0] if classification.reasoning else "None")

        console.print(result_table)
        console.print()


if __name__ == "__main__":
    main()
