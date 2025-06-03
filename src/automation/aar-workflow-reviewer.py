#!/usr/bin/env python3
"""
AAR Content Review & Workflow Improvement Engine

Automatically reviews unprocessed AAR content to identify:
- Lessons learned patterns
- Automation opportunities
- Workflow efficiency improvements
- New automation recommendations

Aligns with Avanade behavioral anchors:
- Create the Future: Proactive improvement through automation
- Inspire Greatness: Continuous improvement culture
- Accelerate Impact: Converting lessons into actionable improvements
"""

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass
import yaml

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class AARInsight:
    """Represents a lesson learned or automation opportunity from AAR content"""
    content: str
    category: str  # automation, process, quality, performance, etc.
    priority: str  # high, medium, low
    effort_estimate: str  # "1-2 hours", "half day", etc.
    source_file: str
    date_found: datetime
    patterns: List[str] = field(default_factory=list)
    related_insights: List[str] = field(default_factory=list)
    actionable: bool = True

@dataclass
class WorkflowRecommendation:
    """Specific workflow improvement recommendation"""
    title: str
    description: str
    category: str  # automation, process, tooling, quality
    impact: str  # high, medium, low
    effort: str
    implementation_steps: List[str]
    affected_workflows: List[str]
    success_metrics: List[str]
    supporting_evidence: List[str]

@dataclass
class ReviewContext:
    """Context for AAR review session"""
    timestamp: datetime
    workspace_path: Path
    review_status_file: Path
    last_review_date: Optional[datetime] = None
    insights_found: List[AARInsight] = field(default_factory=list)
    recommendations_generated: List[WorkflowRecommendation] = field(default_factory=list)
    files_processed: Set[str] = field(default_factory=set)
    errors: List[str] = field(default_factory=list)

class AARContentReviewer:
    """Main engine for reviewing AAR content and generating workflow improvements"""

    def __init__(self, workspace_path: str):
        self.workspace_path = Path(workspace_path)
        self.context = ReviewContext(
            timestamp=datetime.now(),
            workspace_path=self.workspace_path,
            review_status_file=self.workspace_path / "tools" / "aar-automation" / "review-status.json"
        )

        # Patterns to identify valuable content
        self.automation_patterns = [
            r"automat[ie].*opportunit",
            r"could be automated",
            r"repetitive.*process",
            r"manual.*effort",
            r"workflow.*improvement",
            r"suggest.*automation"
        ]

        self.lesson_patterns = [
            r"lesson.*learned",
            r"what.*worked",
            r"what.*didn[''']t.*work",
            r"improvement.*discovered",
            r"insight",
            r"pattern.*analysis",
            r"success.*factor"
        ]

        self.process_improvement_patterns = [
            r"process.*improvement",
            r"efficiency.*gain",
            r"time.*saving",
            r"reduce.*effort",
            r"streamline",
            r"optimize"
        ]

    def run_daily_review(self) -> Dict[str, Any]:
        """Run the daily AAR content review process"""
        logger.info("🔍 Starting daily AAR content review...")

        try:
            # Load previous review status
            self._load_review_status()

            # Find unreviewed AAR files
            unreviewed_files = self._find_unreviewed_aar_files()
            logger.info(f"Found {len(unreviewed_files)} unreviewed AAR files")

            # Process each file for insights
            for file_path in unreviewed_files:
                self._process_aar_file(file_path)

            # Generate workflow recommendations from insights
            self._generate_workflow_recommendations()

            # Create reports
            report_data = self._generate_reports()

            # Update review status
            self._save_review_status()

            logger.info(f"✅ Review complete. Generated {len(self.context.recommendations_generated)} recommendations")
            return report_data

        except Exception as e:
            error_msg = f"AAR review failed: {str(e)}"
            logger.error(error_msg)
            self.context.errors.append(error_msg)
            return {"status": "error", "message": error_msg}

    def _load_review_status(self):
        """Load previous review status to track what's been processed"""
        if self.context.review_status_file.exists():
            try:
                with open(self.context.review_status_file, 'r') as f:
                    status = json.load(f)
                    if 'last_review_date' in status:
                        self.context.last_review_date = datetime.fromisoformat(status['last_review_date'])
                    self.context.files_processed = set(status.get('processed_files', []))
                    logger.info(f"Loaded review status: {len(self.context.files_processed)} files previously processed")
            except Exception as e:
                logger.warning(f"Could not load review status: {e}")

    def _find_unreviewed_aar_files(self) -> List[Path]:
        """Find AAR files that haven't been reviewed yet"""
        aar_patterns = [
            "**/reports/**/daily_aar_*.md",
            "**/reports/**/aar_completion_*.md",
            "**/reports/**/*_AAR.md",
            "**/reports/**/*automation-suggestions*.md",
            "**/docs/**/*CONVERSATION-ANALYSIS*.md"
        ]

        all_files = []
        for pattern in aar_patterns:
            all_files.extend(self.workspace_path.glob(pattern))

        # Filter to unreviewed files
        unreviewed = []
        cutoff_date = self.context.last_review_date or datetime.now() - timedelta(days=30)

        for file_path in all_files:
            file_str = str(file_path)
            if file_str not in self.context.files_processed:
                # Check if file is newer than last review or within reasonable timeframe
                if file_path.stat().st_mtime > cutoff_date.timestamp():
                    unreviewed.append(file_path)

        return unreviewed

    def _process_aar_file(self, file_path: Path):
        """Extract insights from a single AAR file"""
        logger.info(f"📄 Processing: {file_path.name}")

        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')

            # Extract automation opportunities
            self._extract_automation_insights(content, file_path)

            # Extract lessons learned
            self._extract_lesson_insights(content, file_path)

            # Extract process improvements
            self._extract_process_insights(content, file_path)

            self.context.files_processed.add(str(file_path))

        except Exception as e:
            error_msg = f"Error processing {file_path}: {e}"
            logger.error(error_msg)
            self.context.errors.append(error_msg)

    def _extract_automation_insights(self, content: str, file_path: Path):
        """Extract automation opportunities from content"""
        lines = content.split('\n')

        for i, line in enumerate(lines):
            for pattern in self.automation_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    # Get context around the match
                    context_lines = lines[max(0, i-2):min(len(lines), i+3)]
                    context_text = '\n'.join(context_lines).strip()

                    insight = AARInsight(
                        content=context_text,
                        category="automation",
                        priority=self._assess_priority(context_text),
                        effort_estimate=self._estimate_effort(context_text),
                        source_file=str(file_path),
                        date_found=datetime.now(),
                        patterns=[pattern]
                    )

                    self.context.insights_found.append(insight)

    def _extract_lesson_insights(self, content: str, file_path: Path):
        """Extract lessons learned from content"""
        lines = content.split('\n')

        for i, line in enumerate(lines):
            for pattern in self.lesson_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    # Get larger context for lessons learned
                    context_lines = lines[max(0, i-1):min(len(lines), i+5)]
                    context_text = '\n'.join(context_lines).strip()

                    insight = AARInsight(
                        content=context_text,
                        category="lesson_learned",
                        priority=self._assess_priority(context_text),
                        effort_estimate="varies",
                        source_file=str(file_path),
                        date_found=datetime.now(),
                        patterns=[pattern]
                    )

                    self.context.insights_found.append(insight)

    def _extract_process_insights(self, content: str, file_path: Path):
        """Extract process improvement opportunities"""
        lines = content.split('\n')

        for i, line in enumerate(lines):
            for pattern in self.process_improvement_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    context_lines = lines[max(0, i-2):min(len(lines), i+4)]
                    context_text = '\n'.join(context_lines).strip()

                    insight = AARInsight(
                        content=context_text,
                        category="process_improvement",
                        priority=self._assess_priority(context_text),
                        effort_estimate=self._estimate_effort(context_text),
                        source_file=str(file_path),
                        date_found=datetime.now(),
                        patterns=[pattern]
                    )

                    self.context.insights_found.append(insight)

    def _assess_priority(self, content: str) -> str:
        """Assess priority based on content keywords"""
        high_priority_keywords = ["critical", "blocking", "urgent", "high priority", "immediate"]
        medium_priority_keywords = ["important", "should", "recommended", "medium"]

        content_lower = content.lower()

        if any(keyword in content_lower for keyword in high_priority_keywords):
            return "high"
        elif any(keyword in content_lower for keyword in medium_priority_keywords):
            return "medium"
        else:
            return "low"

    def _estimate_effort(self, content: str) -> str:
        """Estimate effort based on content context"""
        content_lower = content.lower()

        if any(phrase in content_lower for phrase in ["quick", "simple", "easy", "minutes"]):
            return "1-2 hours"
        elif any(phrase in content_lower for phrase in ["moderate", "several hours", "half day"]):
            return "half day"
        elif any(phrase in content_lower for phrase in ["complex", "significant", "full day", "multiple days"]):
            return "1-3 days"
        else:
            return "2-4 hours"

    def _generate_workflow_recommendations(self):
        """Generate specific workflow improvement recommendations from insights"""

        # Group insights by category and patterns
        automation_insights = [i for i in self.context.insights_found if i.category == "automation"]
        lesson_insights = [i for i in self.context.insights_found if i.category == "lesson_learned"]
        process_insights = [i for i in self.context.insights_found if i.category == "process_improvement"]

        # Generate automation workflow recommendations
        if automation_insights:
            self._generate_automation_recommendations(automation_insights)

        # Generate process improvement recommendations
        if process_insights:
            self._generate_process_recommendations(process_insights)

        # Generate quality workflow recommendations
        self._generate_quality_recommendations(lesson_insights)

        # Generate monitoring and feedback recommendations
        self._generate_monitoring_recommendations()

    def _generate_automation_recommendations(self, insights: List[AARInsight]):
        """Generate automation-specific workflow recommendations"""

        # Identify common automation themes
        themes = {}
        for insight in insights:
            if "quality" in insight.content.lower() or "warning" in insight.content.lower():
                themes.setdefault("quality_automation", []).append(insight)
            elif "git" in insight.content.lower() or "commit" in insight.content.lower():
                themes.setdefault("git_automation", []).append(insight)
            elif "test" in insight.content.lower():
                themes.setdefault("testing_automation", []).append(insight)
            else:
                themes.setdefault("general_automation", []).append(insight)

        for theme, theme_insights in themes.items():
            if len(theme_insights) >= 2:  # Only recommend if multiple sources suggest it
                self._create_automation_recommendation(theme, theme_insights)

    def _create_automation_recommendation(self, theme: str, insights: List[AARInsight]):
        """Create specific automation recommendation"""

        theme_configs = {
            "quality_automation": {
                "title": "Enhanced Quality Automation Pipeline",
                "description": "Implement comprehensive quality gates based on recurring quality issues identified in AARs",
                "workflows": ["pre-commit hooks", "CI/CD quality gates", "automated fix workflows"],
                "steps": [
                    "Analyze most frequent quality violations from AAR patterns",
                    "Create automated fix scripts for top 3 violation types",
                    "Implement pre-commit hooks to prevent regressions",
                    "Add CI/CD quality gates with automated notifications",
                    "Create quality dashboard for real-time monitoring"
                ]
            },
            "git_automation": {
                "title": "Git Workflow Automation Enhancement",
                "description": "Automate repetitive git workflows identified in AAR patterns",
                "workflows": ["commit automation", "branch management", "PR workflows"],
                "steps": [
                    "Identify repetitive commit patterns from AAR data",
                    "Create GitHub Actions for common commit scenarios",
                    "Implement automated branch cleanup workflows",
                    "Add PR template automation based on change types",
                    "Create commit message standardization tools"
                ]
            },
            "testing_automation": {
                "title": "Testing Workflow Optimization",
                "description": "Enhance testing automation based on AAR testing insights",
                "workflows": ["test execution", "result reporting", "failure analysis"],
                "steps": [
                    "Analyze testing bottlenecks from AAR reports",
                    "Implement parallel test execution strategies",
                    "Create automated test result analysis",
                    "Add failure pattern detection and auto-fixing",
                    "Implement test coverage monitoring automation"
                ]
            }
        }

        if theme in theme_configs:
            config = theme_configs[theme]

            recommendation = WorkflowRecommendation(
                title=config["title"],
                description=config["description"],
                category="automation",
                impact="high" if len(insights) > 3 else "medium",
                effort=self._calculate_combined_effort(insights),
                implementation_steps=config["steps"],
                affected_workflows=config["workflows"],
                success_metrics=[
                    f"Reduce manual effort by 50%+ in {theme.replace('_', ' ')}",
                    "Decrease related AAR issues by 75%",
                    "Improve workflow consistency scores"
                ],
                supporting_evidence=[f"{len(insights)} AAR insights support this recommendation"]
            )

            self.context.recommendations_generated.append(recommendation)

    def _generate_process_recommendations(self, insights: List[AARInsight]):
        """Generate process improvement recommendations"""

        if len(insights) >= 2:
            recommendation = WorkflowRecommendation(
                title="Process Efficiency Enhancement Program",
                description="Systematic improvements to identified process bottlenecks from AAR analysis",
                category="process",
                impact="medium",
                effort=self._calculate_combined_effort(insights),
                implementation_steps=[
                    "Document current process pain points from AAR data",
                    "Design improved process flows for top 3 issues",
                    "Create process automation where applicable",
                    "Implement process metrics and monitoring",
                    "Train team on new process improvements"
                ],
                affected_workflows=["daily workflows", "task management", "review processes"],
                success_metrics=[
                    "30% reduction in process-related AAR issues",
                    "Improved task completion rates",
                    "Reduced time-to-resolution for common issues"
                ],
                supporting_evidence=[f"{len(insights)} process improvement opportunities identified"]
            )

            self.context.recommendations_generated.append(recommendation)

    def _generate_quality_recommendations(self, insights: List[AARInsight]):
        """Generate quality-focused workflow recommendations"""

        quality_insights = [i for i in insights if any(word in i.content.lower()
                           for word in ["quality", "warning", "error", "bug", "fix"])]

        if quality_insights:
            recommendation = WorkflowRecommendation(
                title="Quality-First Development Workflow",
                description="Implement proactive quality measures based on lessons learned from AARs",
                category="quality",
                impact="high",
                effort="1-2 weeks",
                implementation_steps=[
                    "Implement real-time quality feedback in development environment",
                    "Create quality metrics dashboard based on AAR patterns",
                    "Add automated quality gates at key workflow points",
                    "Establish quality review checkpoints in all workflows",
                    "Create quality pattern library from AAR lessons"
                ],
                affected_workflows=["development", "testing", "deployment", "review"],
                success_metrics=[
                    "90% reduction in quality-related AAR issues",
                    "Zero-defect deployment rate above 95%",
                    "Quality review cycle time reduced by 50%"
                ],
                supporting_evidence=[f"{len(quality_insights)} quality-related lessons learned"]
            )

            self.context.recommendations_generated.append(recommendation)

    def _generate_monitoring_recommendations(self):
        """Generate monitoring and feedback workflow recommendations"""

        recommendation = WorkflowRecommendation(
            title="Enhanced AAR Monitoring & Feedback Loop",
            description="Improve the AAR process itself based on review insights",
            category="monitoring",
            impact="medium",
            effort="1 week",
            implementation_steps=[
                "Implement automated AAR content analysis (this workflow)",
                "Create AAR insight trending and pattern detection",
                "Add proactive notification for recurring issues",
                "Implement AAR recommendation tracking and follow-up",
                "Create AAR effectiveness metrics and reporting"
            ],
            affected_workflows=["AAR process", "continuous improvement", "team feedback"],
            success_metrics=[
                "100% of AAR recommendations tracked to completion",
                "50% improvement in issue recurrence prevention",
                "Automated detection of workflow improvement opportunities"
            ],
            supporting_evidence=["Analysis of AAR review patterns and effectiveness"]
        )

        self.context.recommendations_generated.append(recommendation)

    def _calculate_combined_effort(self, insights: List[AARInsight]) -> str:
        """Calculate effort estimate for multiple insights"""
        effort_map = {"1-2 hours": 1, "2-4 hours": 3, "half day": 4, "1-3 days": 16}

        total_hours = sum(effort_map.get(insight.effort_estimate, 3) for insight in insights)

        if total_hours <= 8:
            return "1-2 days"
        elif total_hours <= 24:
            return "3-5 days"
        else:
            return "1-2 weeks"

    def _generate_reports(self) -> Dict[str, Any]:
        """Generate comprehensive reports from the review"""

        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
        reports_dir = self.workspace_path / "tools" / "aar-automation" / "reports" / "workflow-improvements"
        reports_dir.mkdir(parents=True, exist_ok=True)

        # Generate main workflow improvement report
        main_report_path = reports_dir / f"{timestamp}_workflow_improvements.md"
        self._generate_main_report(main_report_path)

        # Generate JSON data for integration
        data_report_path = reports_dir / f"{timestamp}_improvement_data.json"
        self._generate_data_report(data_report_path)

        # Generate executive summary
        summary_path = reports_dir / f"{timestamp}_executive_summary.md"
        self._generate_executive_summary(summary_path)

        return {
            "status": "success",
            "insights_found": len(self.context.insights_found),
            "recommendations_generated": len(self.context.recommendations_generated),
            "files_processed": len(self.context.files_processed),
            "main_report": str(main_report_path),
            "data_report": str(data_report_path),
            "summary_report": str(summary_path)
        }

    def _generate_main_report(self, output_path: Path):
        """Generate the main workflow improvement report"""

        content = f"""# 🚀 Workflow Improvement Recommendations
**Generated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Review Period**: {len(self.context.files_processed)} AAR files analyzed
**Insights Found**: {len(self.context.insights_found)}

## 📊 Executive Summary

This report analyzes AAR content to identify patterns and recommend workflow improvements that will:
- **Create the Future** through proactive automation
- **Inspire Greatness** via continuous improvement culture
- **Accelerate Impact** by converting lessons into actionable improvements

### Key Findings
- **{len([i for i in self.context.insights_found if i.category == "automation"])} automation opportunities** identified
- **{len([i for i in self.context.insights_found if i.category == "process_improvement"])} process improvements** discovered
- **{len([i for i in self.context.insights_found if i.category == "lesson_learned"])} lessons learned** analyzed
- **{len(self.context.recommendations_generated)} workflow recommendations** generated

---

## 🎯 Priority Workflow Recommendations

"""

        # Sort recommendations by impact and add to report
        high_impact = [r for r in self.context.recommendations_generated if r.impact == "high"]
        medium_impact = [r for r in self.context.recommendations_generated if r.impact == "medium"]

        for recommendations, impact_level in [(high_impact, "High Impact"), (medium_impact, "Medium Impact")]:
            if recommendations:
                content += f"### {impact_level} Recommendations\n\n"

                for i, rec in enumerate(recommendations, 1):
                    content += f"#### {i}. {rec.title}\n"
                    content += f"**Category**: {rec.category.title()}\n"
                    content += f"**Effort Estimate**: {rec.effort}\n"
                    content += f"**Affected Workflows**: {', '.join(rec.affected_workflows)}\n\n"
                    content += f"{rec.description}\n\n"

                    content += "**Implementation Steps**:\n"
                    for step in rec.implementation_steps:
                        content += f"- {step}\n"

                    content += "\n**Success Metrics**:\n"
                    for metric in rec.success_metrics:
                        content += f"- {metric}\n"

                    content += f"\n**Supporting Evidence**: {', '.join(rec.supporting_evidence)}\n\n---\n\n"

        content += """## 📈 Implementation Roadmap

### Phase 1: Quick Wins (Week 1-2)
- Implement highest-impact, lowest-effort recommendations
- Focus on automation opportunities with immediate ROI
- Establish success metrics and monitoring

### Phase 2: Process Improvements (Week 3-4)
- Deploy process enhancement recommendations
- Train team on new workflows
- Implement feedback mechanisms

### Phase 3: Advanced Automation (Month 2)
- Complex automation implementations
- Integration testing and validation
- Comprehensive monitoring and alerting

---

## 🔍 Detailed Insights Analysis

### Automation Opportunities by Category
"""

        # Add insights analysis
        categories = {}
        for insight in self.context.insights_found:
            categories.setdefault(insight.category, []).append(insight)

        for category, insights in categories.items():
            content += f"\n#### {category.replace('_', ' ').title()}\n"
            content += f"**Count**: {len(insights)}\n"
            content += f"**Priority Distribution**: "

            priority_counts = {}
            for insight in insights:
                priority_counts[insight.priority] = priority_counts.get(insight.priority, 0) + 1

            content += ", ".join([f"{p}: {c}" for p, c in priority_counts.items()]) + "\n\n"

            # Show top insights for this category
            high_priority_insights = [i for i in insights if i.priority == "high"][:3]
            if high_priority_insights:
                content += "**Top Insights**:\n"
                for insight in high_priority_insights:
                    content += f"- {insight.content[:100]}... (from {Path(insight.source_file).name})\n"
                content += "\n"

        content += f"""
---

## 📋 Next Steps

1. **Review Recommendations**: Team review of proposed workflow improvements
2. **Prioritize Implementation**: Select recommendations for immediate implementation
3. **Assign Ownership**: Assign recommendation implementation to team members
4. **Track Progress**: Monitor implementation progress and measure success metrics
5. **Iterate Process**: Refine this AAR review process based on results

---

## 🔄 Continuous Improvement

This automated AAR review process will run daily to:
- Track implementation progress of recommendations
- Identify new patterns as they emerge
- Measure effectiveness of implemented improvements
- Generate follow-up recommendations

---

*Generated by PowerCompany AAR Workflow Improvement Engine*
*Next Review**: {(datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")}*
"""

        output_path.write_text(content, encoding='utf-8')
        logger.info(f"📄 Main report generated: {output_path}")

    def _generate_data_report(self, output_path: Path):
        """Generate JSON data report for integration with other tools"""

        data = {
            "review_metadata": {
                "timestamp": self.context.timestamp.isoformat(),
                "workspace_path": str(self.context.workspace_path),
                "files_processed": list(self.context.files_processed),
                "insights_count": len(self.context.insights_found),
                "recommendations_count": len(self.context.recommendations_generated)
            },
            "insights": [
                {
                    "content": insight.content,
                    "category": insight.category,
                    "priority": insight.priority,
                    "effort_estimate": insight.effort_estimate,
                    "source_file": insight.source_file,
                    "date_found": insight.date_found.isoformat(),
                    "patterns": insight.patterns
                }
                for insight in self.context.insights_found
            ],
            "recommendations": [
                {
                    "title": rec.title,
                    "description": rec.description,
                    "category": rec.category,
                    "impact": rec.impact,
                    "effort": rec.effort,
                    "implementation_steps": rec.implementation_steps,
                    "affected_workflows": rec.affected_workflows,
                    "success_metrics": rec.success_metrics,
                    "supporting_evidence": rec.supporting_evidence
                }
                for rec in self.context.recommendations_generated
            ]
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"📊 Data report generated: {output_path}")

    def _generate_executive_summary(self, output_path: Path):
        """Generate executive summary for leadership review"""

        content = f"""# 📋 AAR Workflow Improvement - Executive Summary
**Date**: {datetime.now().strftime("%Y-%m-%d")}

## 🎯 Key Outcomes

### Insights Discovered
- **{len(self.context.insights_found)} total insights** extracted from AAR content
- **{len([i for i in self.context.insights_found if i.priority == "high"])} high-priority opportunities** identified
- **{len(self.context.files_processed)} AAR files** analyzed for patterns

### Recommendations Generated
- **{len([r for r in self.context.recommendations_generated if r.impact == "high"])} high-impact workflow improvements**
- **{len([r for r in self.context.recommendations_generated if r.impact == "medium"])} medium-impact enhancements**

## 💼 Business Impact

### Efficiency Gains
- **Automation opportunities** could reduce manual effort by 50-75%
- **Process improvements** will accelerate delivery cycles
- **Quality enhancements** will reduce rework and technical debt

### Strategic Value
- **Proactive improvement culture** established through automated AAR analysis
- **Data-driven decisions** based on actual patterns and lessons learned
- **Continuous optimization** ensures workflows evolve with needs

## 🚀 Recommended Next Actions

1. **Immediate (This Week)**
   - Review high-impact recommendations with team
   - Select 2-3 quick wins for implementation
   - Assign ownership for priority improvements

2. **Short-term (Next Month)**
   - Implement automation opportunities
   - Deploy process improvements
   - Establish success metrics monitoring

3. **Ongoing**
   - Daily automated AAR review process
   - Quarterly workflow effectiveness assessment
   - Continuous refinement based on results

## 📊 Success Metrics

- **50% reduction** in recurring AAR issues
- **75% improvement** in workflow automation coverage
- **90% faster** identification of improvement opportunities
- **100% tracking** of recommendation implementation

---

*This automated analysis represents a proactive approach to continuous improvement, aligning with Avanade's commitment to creating the future through data-driven excellence.*
"""

        output_path.write_text(content, encoding='utf-8')
        logger.info(f"📋 Executive summary generated: {output_path}")

    def _save_review_status(self):
        """Save review status for next run"""
        status = {
            "last_review_date": self.context.timestamp.isoformat(),
            "processed_files": list(self.context.files_processed),
            "insights_count": len(self.context.insights_found),
            "recommendations_count": len(self.context.recommendations_generated)
        }

        self.context.review_status_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.context.review_status_file, 'w') as f:
            json.dump(status, f, indent=2)

        logger.info(f"💾 Review status saved: {self.context.review_status_file}")

def main():
    """Main entry point for AAR workflow improvement review"""
    import argparse

    parser = argparse.ArgumentParser(description="AAR Content Review & Workflow Improvement Engine")
    parser.add_argument("--workspace-path", default="/workspaces/PowerCompany",
                       help="Path to workspace for AAR analysis")
    parser.add_argument("--mode", choices=["daily", "manual"], default="daily",
                       help="Review mode: daily (automated) or manual (on-demand)")
    parser.add_argument("--output-format", choices=["detailed", "summary"], default="detailed",
                       help="Output format preference")
    parser.add_argument("--output-dir",
                       help="Custom output directory for reports")
    parser.add_argument("--auto-create-issues", action="store_true",
                       help="Automatically create workflow improvement issues (daily mode)")

    args = parser.parse_args()

    # Initialize reviewer with custom output directory if provided
    workspace_path = args.workspace_path
    if args.output_dir:
        # Update the reviewer to use custom output path
        import os
        os.makedirs(args.output_dir, exist_ok=True)

    reviewer = AARContentReviewer(workspace_path)

    # Override output directory if specified
    if args.output_dir:
        reviewer.context.output_dir = Path(args.output_dir)

    # Run review
    mode_desc = "🔄 automated daily" if args.mode == "daily" else "🎯 manual"
    logger.info(f"🚀 Starting {mode_desc} AAR workflow improvement review...")

    result = reviewer.run_daily_review()

    if result["status"] == "success":
        print(f"✅ Review completed successfully!")
        print(f"📊 Insights found: {result['insights_found']}")
        print(f"🎯 Recommendations generated: {result['recommendations_generated']}")
        print(f"📄 Main report: {result['main_report']}")

        if args.output_format == "summary" or args.mode == "daily":
            print(f"📋 Executive summary: {result['summary_report']}")

        if args.auto_create_issues and result['recommendations_generated'] > 0:
            print(f"🎫 Would create {result['recommendations_generated']} workflow improvement issues")
            print("   (Issue creation integration pending)")
    else:
        print(f"❌ Review failed: {result['message']}")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())
