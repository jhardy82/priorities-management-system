# API Reference - Priorities Management System

## Overview

This document provides comprehensive API documentation for the Priorities Management System's core components and extension points.

## Core Classes

### PrioritiesManager

Main entry point for the priorities management system.

```python
from priorities_manager import PrioritiesManager

manager = PrioritiesManager(config_path="config/config.json")
```

#### Methods

##### `__init__(config_path: Optional[str] = None)`
Initialize the priorities management system.

**Parameters:**
- `config_path` (Optional[str]): Path to configuration file

**Raises:**
- `ConfigError`: If configuration cannot be loaded

##### `analyze_priorities(search_paths: List[str] = None) -> None`
Analyze and update task priorities with user interaction.

**Parameters:**
- `search_paths` (List[str], optional): Paths to search for task files

**Features:**
- Loads tasks from files or directories
- Generates priority recommendations
- Interactive confirmation for changes
- Automatic backup creation

##### `generate_report(search_paths: List[str] = None, output_path: Optional[str] = None) -> None`
Generate comprehensive priority analysis report.

**Parameters:**
- `search_paths` (List[str], optional): Paths to search for task files
- `output_path` (Optional[str]): Output file path for report

**Output:**
- Markdown report with analysis summary
- Priority distribution statistics
- Detailed recommendations

##### `demo_mode() -> None`
Run demonstration with sample data.

**Features:**
- Loads 10 demo tasks
- Shows priority analysis process
- Demonstrates dependency analysis
- Educational output formatting

##### `validate_system() -> None`
Validate system configuration and functionality.

**Validation Steps:**
1. Configuration validation
2. Directory structure verification
3. Task loading capability test
4. Priority engine functionality test

##### `interactive_mode() -> None`
Run interactive menu-driven interface.

**Menu Options:**
- Priority analysis
- Report generation
- Task display
- Configuration view
- Demo execution
- System validation

### ConfigManager

Handles system configuration loading and validation.

```python
from core.config_manager import ConfigManager

config_manager = ConfigManager()
config = config_manager.load_config("config/config.json")
```

#### Methods

##### `load_config(config_path: Optional[str] = None) -> Config`
Load and validate configuration.

**Parameters:**
- `config_path` (Optional[str]): Path to configuration file

**Returns:**
- `Config`: Validated configuration object

**Raises:**
- `ConfigError`: If configuration is invalid

### PriorityEngine

Core engine for priority analysis and recommendations.

```python
from core.priority_engine_standalone import PriorityEngine

engine = PriorityEngine(config)
recommendations = engine.analyze_priorities(tasks)
```

#### Methods

##### `analyze_priorities(tasks: List[TaskModel]) -> List[PriorityRecommendation]`
Generate priority recommendations for tasks.

**Parameters:**
- `tasks` (List[TaskModel]): Tasks to analyze

**Returns:**
- `List[PriorityRecommendation]`: Priority change recommendations

##### `generate_dependency_analysis(tasks: List[TaskModel]) -> List[DependencyGraph]`
Generate dependency analysis for tasks.

**Parameters:**
- `tasks` (List[TaskModel]): Tasks to analyze

**Returns:**
- `List[DependencyGraph]`: Dependency analysis for each task

### UniversalTaskInterface

Universal interface for loading tasks from various sources.

```python
from core.task_interface import UniversalTaskInterface

interface = UniversalTaskInterface(config)
tasks = interface.load_all_tasks(["path/to/tasks/"])
```

#### Methods

##### `load_all_tasks(search_paths: List[str]) -> List[TaskModel]`
Load tasks from multiple paths.

**Parameters:**
- `search_paths` (List[str]): Directories to search for task files

**Returns:**
- `List[TaskModel]`: Loaded and validated tasks

### MarkdownTaskAdapter

Specialized adapter for loading tasks from markdown files.

```python
from core.task_interface import MarkdownTaskAdapter

adapter = MarkdownTaskAdapter()
tasks = adapter.load_tasks("tasks.md")
```

#### Methods

##### `load_tasks(file_path: str) -> List[TaskModel]`
Load tasks from a single markdown file.

**Parameters:**
- `file_path` (str): Path to markdown file

**Returns:**
- `List[TaskModel]`: Parsed tasks from file

## Data Models

### TaskModel

Core task representation.

```python
@dataclass
class TaskModel:
    id: str
    title: str
    description: str
    priority: TaskPriority
    category: TaskCategory
    status: TaskStatus
    created_date: datetime
    due_date: Optional[datetime] = None
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
```

### TaskPriority

Priority levels for tasks.

```python
class TaskPriority(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
```

### TaskCategory

Task categorization system.

```python
class TaskCategory(Enum):
    INFRASTRUCTURE = "INFRASTRUCTURE"
    CLIENT_DELIVERABLE = "CLIENT_DELIVERABLE"
    QUALITY_AUTOMATION = "QUALITY_AUTOMATION"
    WORKSPACE_MANAGEMENT = "WORKSPACE_MANAGEMENT"
    DOCUMENTATION = "DOCUMENTATION"
    RESEARCH_ANALYSIS = "RESEARCH_ANALYSIS"
```

### TaskStatus

Task completion status.

```python
class TaskStatus(Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
```

### PriorityRecommendation

Priority change recommendation.

```python
@dataclass
class PriorityRecommendation:
    task_id: str
    current_priority: TaskPriority
    recommended_priority: TaskPriority
    reasoning: List[str]
    confidence_score: float
```

### DependencyGraph

Task dependency analysis.

```python
@dataclass
class DependencyGraph:
    task_id: str
    direct_dependencies: List[str]
    transitive_dependencies: List[str]
    blocks_directly: List[str]
    blocks_transitively: List[str]
    critical_path_member: bool = False
```

## Configuration Schema

### Config Structure

```python
@dataclass
class Config:
    paths: PathConfig
    automation: AutomationConfig
    priority_weights: PriorityWeights
```

### PathConfig

```python
@dataclass
class PathConfig:
    data_directory: str = "./data"
    reports_directory: str = "./reports"
    backup_directory: str = "./backups"
    config_directory: str = "./config"
```

### AutomationConfig

```python
@dataclass
class AutomationConfig:
    dry_run_mode: bool = True
    confidence_threshold: float = 0.7
    max_changes_per_run: int = 10
    backup_enabled: bool = True
```

### PriorityWeights

```python
@dataclass
class PriorityWeights:
    deadline_weight: float = 0.3
    dependency_weight: float = 0.25
    category_weight: float = 0.2
    urgency_weight: float = 0.15
    complexity_weight: float = 0.1
```

## Extension Points

### Custom Task Adapters

Implement custom task loading by extending the base adapter:

```python
from core.task_interface import BaseTaskAdapter
from typing import List

class CustomTaskAdapter(BaseTaskAdapter):
    def load_tasks(self, source_path: str) -> List[TaskModel]:
        # Custom loading logic
        tasks = []
        # ... implementation ...
        return tasks
    
    def can_handle(self, source_path: str) -> bool:
        # Return True if this adapter can handle the source
        return source_path.endswith('.custom')
```

### Custom Priority Algorithms

Extend priority analysis by implementing custom algorithms:

```python
from core.priority_engine_standalone import PriorityEngine

class CustomPriorityEngine(PriorityEngine):
    def _calculate_priority_score(self, task: TaskModel) -> float:
        # Custom scoring logic
        score = 0.0
        # ... implementation ...
        return score
```

### Custom Report Formats

Create custom report generators:

```python
def custom_report_generator(tasks, recommendations, dependency_analysis):
    # Custom report format
    report_content = "Custom Report Format\n"
    # ... implementation ...
    return report_content
```

## Usage Examples

### Basic Integration

```python
from priorities_manager import PrioritiesManager

# Initialize system
manager = PrioritiesManager()

# Load and analyze tasks
manager.analyze_priorities(["projects/", "tasks.md"])

# Generate report
manager.generate_report(output_path="analysis_report.md")
```

### Advanced Usage

```python
from core.config_manager import ConfigManager
from core.priority_engine_standalone import PriorityEngine
from core.task_interface import UniversalTaskInterface

# Custom configuration
config_manager = ConfigManager()
config = config_manager.load_config("custom_config.json")

# Initialize components
task_interface = UniversalTaskInterface(config)
priority_engine = PriorityEngine(config)

# Load tasks
tasks = task_interface.load_all_tasks(["src/", "docs/"])

# Analyze priorities
recommendations = priority_engine.analyze_priorities(tasks)

# Process recommendations
for rec in recommendations:
    if rec.confidence_score > 0.8:
        print(f"High confidence recommendation: {rec.task_id}")
```

### Integration with External Systems

```python
import json
from priorities_manager import PrioritiesManager

def export_to_external_system(tasks, recommendations):
    """Export analysis results to external project management system"""
    export_data = {
        "tasks": [task.to_dict() for task in tasks],
        "recommendations": [rec.to_dict() for rec in recommendations],
        "timestamp": datetime.now().isoformat()
    }
    
    # Send to external API
    # requests.post("https://api.external-system.com/priorities", json=export_data)
    
    return export_data

# Use in workflow
manager = PrioritiesManager()
manager.analyze_priorities(["projects/"])
# export_to_external_system(tasks, recommendations)
```

## Error Handling

### Exception Types

```python
from core.config_manager import ConfigError
from core.task_interface import TaskLoadingError

try:
    manager = PrioritiesManager("invalid_config.json")
except ConfigError as e:
    print(f"Configuration error: {e}")

try:
    tasks = interface.load_all_tasks(["nonexistent/"])
except TaskLoadingError as e:
    print(f"Task loading error: {e}")
```

### Best Practices

1. **Always validate configuration** before processing
2. **Handle missing files gracefully** with informative messages
3. **Provide fallback behavior** for analysis failures
4. **Log errors appropriately** for debugging
5. **Use confidence scores** to filter recommendations

## Performance Considerations

### Optimization Tips

1. **Batch processing** - Process multiple files together
2. **Caching** - Cache parsed tasks for repeated analysis
3. **Selective loading** - Only load necessary task fields
4. **Parallel processing** - Use threading for I/O operations

### Memory Management

```python
# Process large task sets in chunks
def process_large_dataset(task_paths, chunk_size=100):
    for i in range(0, len(task_paths), chunk_size):
        chunk = task_paths[i:i + chunk_size]
        tasks = load_tasks(chunk)
        recommendations = analyze_priorities(tasks)
        save_results(recommendations)
        # Clear memory
        del tasks, recommendations
```

This API reference provides the foundation for extending and integrating the Priorities Management System into larger enterprise workflows.
