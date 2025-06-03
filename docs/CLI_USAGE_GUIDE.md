# CLI Usage Guide - Priorities Management System

## Overview

The Priorities Management System provides a comprehensive CLI interface for task analysis, priority management, and reporting. This guide covers all available commands and usage patterns.

## Quick Start

```bash
# Run demo mode to see the system in action
python3 priorities_manager.py --demo

# Validate system configuration
python3 priorities_manager.py --validate

# Run in interactive mode
python3 priorities_manager.py --interactive
```

## Command Line Options

### Core Commands

#### `--demo`
Run demonstration mode with sample tasks
```bash
python3 priorities_manager.py --demo
```
- Loads 10 sample tasks from `examples/sample-tasks.md`
- Shows priority analysis and recommendations
- Demonstrates dependency analysis
- Perfect for testing and evaluation

#### `--validate`
Validate system configuration and functionality
```bash
python3 priorities_manager.py --validate
```
- Tests configuration loading
- Verifies directory structure
- Validates task loading capabilities
- Tests priority engine functionality

#### `--analyze`
Analyze task priorities and generate recommendations
```bash
# Analyze tasks in default directory
python3 priorities_manager.py --analyze

# Analyze specific files or directories
python3 priorities_manager.py --analyze --search-paths tasks/ project.md
```
- Loads tasks from specified paths
- Generates priority recommendations
- Offers to apply changes (interactive mode)
- Creates backups before modifications

#### `--report`
Generate comprehensive priority analysis report
```bash
# Generate report from default directory
python3 priorities_manager.py --report

# Generate report from specific paths
python3 priorities_manager.py --report --search-paths examples/sample-tasks.md

# Specify output location
python3 priorities_manager.py --report --output reports/custom_report.md
```
- Creates markdown report with priority analysis
- Includes task distribution statistics
- Shows recommendations with confidence scores
- Saved to `reports/` directory with timestamp

#### `--interactive`
Run interactive menu-driven interface
```bash
python3 priorities_manager.py --interactive
```
Interactive menu options:
1. **Analyze priorities** - Run priority analysis
2. **Generate report** - Create analysis report
3. **Show loaded tasks** - Display current tasks
4. **Show configuration** - View system settings
5. **Run demo** - Execute demo mode
6. **Validate system** - Run system validation
7. **Create sample tasks** - Generate demo data
8. **Exit** - Quit the application

### Additional Options

#### `--search-paths` / `-s`
Specify paths to search for task files
```bash
# Multiple paths
python3 priorities_manager.py --analyze -s tasks/ projects/ documentation.md

# Single file
python3 priorities_manager.py --report -s examples/sample-tasks.md
```
- Supports both files and directories
- Automatically detects `.md` files in directories
- Can process individual markdown files

#### `--output` / `-o`
Specify output file for reports
```bash
python3 priorities_manager.py --report -o custom_report.md
```

#### `--config` / `-c`
Use custom configuration file
```bash
python3 priorities_manager.py --config my_config.json --analyze
```

## Usage Patterns

### Enterprise Workflow

1. **Initial Setup**
   ```bash
   # Validate system configuration
   python3 priorities_manager.py --validate
   ```

2. **Regular Analysis**
   ```bash
   # Analyze project tasks
   python3 priorities_manager.py --analyze --search-paths projects/
   ```

3. **Reporting**
   ```bash
   # Generate monthly report
   python3 priorities_manager.py --report --output reports/monthly_$(date +%Y%m).md
   ```

### Development Workflow

1. **Testing**
   ```bash
   # Run demo to verify functionality
   python3 priorities_manager.py --demo
   ```

2. **Interactive Development**
   ```bash
   # Use interactive mode for exploration
   python3 priorities_manager.py --interactive
   ```

### CI/CD Integration

```bash
# Automated validation
python3 priorities_manager.py --validate

# Generate reports for review
python3 priorities_manager.py --report --search-paths src/ docs/
```

## File Support

### Supported Formats
- **Markdown (.md)** - Primary format for task files
- **JSON** - Configuration and backup files

### Task File Structure
Tasks should be formatted as markdown with frontmatter:
```markdown
---
title: "Task Title"
priority: "high"
category: "INFRASTRUCTURE"
status: "in_progress"
---

# Task Description
Task details and requirements...
```

## Output Files

### Reports
- **Location**: `./reports/`
- **Format**: `priority_report_YYYYMMDD_HHMMSS.md`
- **Content**: Analysis summary, recommendations, statistics

### Backups
- **Location**: `./backups/`
- **Format**: Timestamped task snapshots
- **Purpose**: Recovery before applying changes

### Updated Tasks
- **Location**: `./reports/`
- **Format**: `updated_tasks_YYYYMMDD_HHMMSS.json`
- **Content**: Tasks with applied priority changes

## Error Handling

The system provides graceful error handling:
- **Configuration errors** - Clear error messages with suggestions
- **File not found** - Helpful guidance on path resolution
- **Task parsing errors** - Detailed error context
- **Dependency analysis failures** - Graceful degradation

## Configuration

Default configuration is loaded from `config/config.json`. Key settings:
- **Data directories** - Where to find task files
- **Automation settings** - Confidence thresholds, dry-run mode
- **Output paths** - Report and backup locations

## Best Practices

1. **Start with validation** - Always run `--validate` in new environments
2. **Use demo mode** - Test changes with `--demo` before production
3. **Regular backups** - System creates automatic backups before changes
4. **Review recommendations** - Check confidence scores before applying
5. **Path specificity** - Use specific paths for better performance

## Troubleshooting

### Common Issues

**No tasks found**
```bash
# Check file paths
python3 priorities_manager.py --validate

# Use specific files instead of directories
python3 priorities_manager.py --analyze -s specific_file.md
```

**Configuration errors**
```bash
# Validate configuration
python3 priorities_manager.py --validate

# Use custom config
python3 priorities_manager.py --config path/to/config.json
```

**Import errors**
```bash
# Verify Python path and dependencies
pip install -r requirements.txt
```

## Examples

### Basic Usage
```bash
# Quick demo
python3 priorities_manager.py --demo

# Analyze current directory
python3 priorities_manager.py --analyze

# Generate report
python3 priorities_manager.py --report
```

### Advanced Usage
```bash
# Multi-path analysis with custom output
python3 priorities_manager.py --analyze \
  --search-paths projects/ docs/ tasks.md \
  --config production.json

# Batch reporting
for project in projects/*/; do
  python3 priorities_manager.py --report \
    --search-paths "$project" \
    --output "reports/$(basename $project)_report.md"
done
```

## Integration Examples

### Git Hook Integration
```bash
#!/bin/bash
# Pre-commit hook example
python3 priorities_manager.py --validate || exit 1
python3 priorities_manager.py --analyze --search-paths . || exit 1
```

### Automation Scripts
```bash
#!/bin/bash
# Daily report generation
cd /path/to/priorities-management-system
python3 priorities_manager.py --report \
  --search-paths /projects/ \
  --output "/reports/daily_$(date +%Y%m%d).md"
```

This CLI interface provides comprehensive task management capabilities suitable for both interactive use and automated workflows.
