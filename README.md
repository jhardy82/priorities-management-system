# Priorities Management System

## Overview
Cross-platform priority management system for work-home environment separation with automatic device detection and context switching.

## Features
- **Device-Based Detection**: Automatically detects work vs home environment
- **Context Switching**: Different priority displays based on current environment
- **Cross-Platform**: Works on both work and home computers
- **Template System**: Standardized priority file templates
- **Integration Ready**: Easy integration with any PowerShell environment

## Quick Start
1. Copy `src/` contents to your local priorities folder
2. Update templates in `templates/` for your specific environments
3. Run: `.\Get-CurrentPriorities.ps1`

## Usage Examples
```powershell
# Show current environment priorities
.\Get-CurrentPriorities.ps1

# Show both work and home priorities
.\Get-CurrentPriorities.ps1 -ShowHome

# Force specific environment
.\Get-CurrentPriorities.ps1 -ForceEnvironment Work
```

## Integration
See `examples/` for corporate and personal setup scripts.
See `docs/` for detailed architecture and configuration guides.
