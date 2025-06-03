#!/usr/bin/env python3
"""
Configuration Manager for Priorities Management System
Handles loading, validation, and management of system configuration
"""

import os
import toml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class ConfigError(Exception):
    """Configuration-related errors"""

    pass


class TaskSourceType(Enum):
    """Supported task source types"""

    MARKDOWN = "markdown"
    JSON = "json"
    CSV = "csv"
    YAML = "yaml"


@dataclass
class TaskSourceConfig:
    """Configuration for task sources"""

    enabled: bool
    patterns: list[str]

    def __post_init__(self):
        if self.enabled and not self.patterns:
            raise ConfigError(f"Enabled task source must have at least one pattern")


@dataclass
class PathConfig:
    """File system path configuration"""

    data_directory: str = "./data"
    reports_directory: str = "./reports"
    logs_directory: str = "./logs"
    templates_directory: str = "./src/templates"
    backup_directory: str = "./backups"

    def __post_init__(self):
        # Expand environment variables
        for field_name in self.__dataclass_fields__:
            value = getattr(self, field_name)
            if isinstance(value, str):
                expanded = os.path.expandvars(os.path.expanduser(value))
                setattr(self, field_name, expanded)


@dataclass
class PriorityEngineConfig:
    """Priority engine configuration"""

    base_weights: Dict[str, float] = field(
        default_factory=lambda: {
            "dependency": 0.3,
            "time_sensitivity": 0.25,
            "impact": 0.25,
            "velocity": 0.2,
        }
    )
    enable_ml_predictions: bool = False
    historical_analysis_days: int = 30
    critical_path_multiplier: float = 1.5
    blocker_penalty_multiplier: float = 2.0

    def __post_init__(self):
        # Validate weights sum to 1.0
        weight_sum = sum(self.base_weights.values())
        if abs(weight_sum - 1.0) > 0.01:
            raise ConfigError(f"Priority weights must sum to 1.0, got {weight_sum}")


@dataclass
class AutomationConfig:
    """Automation behavior configuration"""

    auto_backup: bool = True
    auto_priority_update: bool = True
    confidence_threshold: float = 0.7
    max_priority_changes_per_run: int = 3
    dry_run_mode: bool = False


@dataclass
class ReportingConfig:
    """Report generation configuration"""

    generate_reports: bool = True
    report_formats: list[str] = field(default_factory=lambda: ["markdown", "json"])
    include_charts: bool = True
    include_dependency_graph: bool = True


@dataclass
class NotificationConfig:
    """Notification and output configuration"""

    console_output: bool = True
    verbose_logging: bool = False
    enable_email_notifications: bool = False
    enable_slack_notifications: bool = False


@dataclass
class SafetyConfig:
    """Safety and validation configuration"""

    backup_retention_days: int = 30
    validate_before_changes: bool = True
    require_confirmation_for_critical: bool = True
    enable_rollback: bool = True


@dataclass
class IntegrationConfig:
    """External system integration configuration"""

    enable_vscode_integration: bool = True
    enable_powershell_module: bool = True
    enable_git_hooks: bool = False


@dataclass
class SCFConfig:
    """Structured Conversation Framework configuration"""

    enable_scf_mode: bool = True
    conversation_step_validation: bool = True
    context_preservation: bool = True
    progress_tracking: bool = True


@dataclass
class PrioritiesConfig:
    """Main configuration class for Priorities Management System"""

    system: Dict[str, Any] = field(default_factory=dict)
    paths: PathConfig = field(default_factory=PathConfig)
    task_sources: Dict[str, TaskSourceConfig] = field(default_factory=dict)
    priority_engine: PriorityEngineConfig = field(default_factory=PriorityEngineConfig)
    automation: AutomationConfig = field(default_factory=AutomationConfig)
    reporting: ReportingConfig = field(default_factory=ReportingConfig)
    notifications: NotificationConfig = field(default_factory=NotificationConfig)
    safety: SafetyConfig = field(default_factory=SafetyConfig)
    integration: IntegrationConfig = field(default_factory=IntegrationConfig)
    scf_compliance: SCFConfig = field(default_factory=SCFConfig)

    @classmethod
    def load_from_file(cls, config_path: str) -> "PrioritiesConfig":
        """Load configuration from TOML file"""
        try:
            config_file = Path(config_path)
            if not config_file.exists():
                raise ConfigError(f"Configuration file not found: {config_path}")

            with open(config_file, "r") as f:
                config_data = toml.load(f)

            return cls.from_dict(config_data)

        except Exception as e:
            raise ConfigError(f"Failed to load configuration: {e}")

    @classmethod
    def from_dict(cls, config_data: Dict[str, Any]) -> "PrioritiesConfig":
        """Create configuration from dictionary"""
        try:
            # Parse task sources
            task_sources = {}
            for source_type, source_config in config_data.get(
                "task_sources", {}
            ).items():
                task_sources[source_type] = TaskSourceConfig(
                    enabled=source_config.get("enabled", False),
                    patterns=source_config.get("patterns", []),
                )

            return cls(
                system=config_data.get("system", {}),
                paths=PathConfig(**config_data.get("paths", {})),
                task_sources=task_sources,
                priority_engine=PriorityEngineConfig(
                    **config_data.get("priority_engine", {})
                ),
                automation=AutomationConfig(**config_data.get("automation", {})),
                reporting=ReportingConfig(**config_data.get("reporting", {})),
                notifications=NotificationConfig(
                    **config_data.get("notifications", {})
                ),
                safety=SafetyConfig(**config_data.get("safety", {})),
                integration=IntegrationConfig(**config_data.get("integration", {})),
                scf_compliance=SCFConfig(**config_data.get("scf_compliance", {})),
            )

        except Exception as e:
            raise ConfigError(f"Failed to parse configuration: {e}")

    def validate(self) -> bool:
        """Validate configuration consistency"""
        errors = []

        # Validate paths exist or can be created
        for path_name in [
            "data_directory",
            "reports_directory",
            "logs_directory",
            "backup_directory",
        ]:
            path = getattr(self.paths, path_name)
            path_obj = Path(path)
            if not path_obj.exists():
                try:
                    path_obj.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    errors.append(f"Cannot create {path_name} at {path}: {e}")

        # Validate at least one task source is enabled
        enabled_sources = [
            source for source in self.task_sources.values() if source.enabled
        ]
        if not enabled_sources:
            errors.append("At least one task source must be enabled")

        # Validate automation thresholds
        if not 0.0 <= self.automation.confidence_threshold <= 1.0:
            errors.append("Confidence threshold must be between 0.0 and 1.0")

        if self.automation.max_priority_changes_per_run < 1:
            errors.append("Maximum priority changes per run must be at least 1")

        if errors:
            raise ConfigError(f"Configuration validation failed: {'; '.join(errors)}")

        return True

    def get_enabled_task_sources(self) -> Dict[str, TaskSourceConfig]:
        """Get only enabled task sources"""
        return {
            name: config for name, config in self.task_sources.items() if config.enabled
        }

    def get_task_patterns(self) -> list[str]:
        """Get all enabled task file patterns"""
        patterns = []
        for source_config in self.get_enabled_task_sources().values():
            patterns.extend(source_config.patterns)
        return patterns


class ConfigManager:
    """Configuration manager singleton"""

    _instance: Optional["ConfigManager"] = None
    _config: Optional[PrioritiesConfig] = None

    def __new__(cls) -> "ConfigManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def load_config(self, config_path: str = None) -> PrioritiesConfig:
        """Load configuration from file or use default"""
        if config_path is None:
            # Try to find config file in standard locations
            possible_paths = [
                "./config/priorities_config.toml",
                "./priorities_config.toml",
                "~/.priorities/config.toml",
                "/etc/priorities/config.toml",
            ]

            for path in possible_paths:
                expanded_path = os.path.expanduser(path)
                if Path(expanded_path).exists():
                    config_path = expanded_path
                    break

            if config_path is None:
                raise ConfigError("No configuration file found in standard locations")

        self._config = PrioritiesConfig.load_from_file(config_path)
        self._config.validate()
        return self._config

    @property
    def config(self) -> PrioritiesConfig:
        """Get current configuration"""
        if self._config is None:
            raise ConfigError("Configuration not loaded. Call load_config() first.")
        return self._config

    def reload_config(self, config_path: str = None) -> PrioritiesConfig:
        """Reload configuration"""
        self._config = None
        return self.load_config(config_path)


# Global configuration manager instance
config_manager = ConfigManager()
