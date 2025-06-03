#Requires -Version 5.1
<#
.SYNOPSIS
AAR Workflow Review Scheduler - Automates daily AAR content analysis

.DESCRIPTION
This script schedules and manages automated AAR workflow improvement reviews.
Aligns with Avanade behavioral anchors:
- Create the Future: Automated continuous improvement
- Inspire Greatness: Data-driven excellence
- Accelerate Impact: Proactive workflow optimization

.PARAMETER Mode
Review mode: 'Schedule', 'RunNow', 'Status', or 'Remove'

.PARAMETER TaskName
Name for the scheduled task (default: 'AAR-Workflow-Review')

.PARAMETER RunTime
Time to run daily review (default: '08:00')

.EXAMPLE
.\Invoke-AARWorkflowScheduler.ps1 -Mode Schedule -RunTime "09:00"
Schedules daily AAR workflow review at 9:00 AM

.EXAMPLE
.\Invoke-AARWorkflowScheduler.ps1 -Mode RunNow
Runs AAR workflow review immediately

.EXAMPLE
.\Invoke-AARWorkflowScheduler.ps1 -Mode Status
Shows status of scheduled AAR review task
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('Schedule', 'RunNow', 'Status', 'Remove')]
    [string]$Mode,

    [Parameter()]
    [string]$TaskName = 'AAR-Workflow-Review',

    [Parameter()]
    [string]$RunTime = '08:00',

    [Parameter()]
    [string]$WorkspacePath = '/workspaces/PowerCompany',

    [Parameter()]
    [switch]$Force
)

# Error handling
$ErrorActionPreference = 'Stop'

# Context object for this script
$Context = [PSCustomObject]@{
    Timestamp     = Get-Date
    Mode          = $Mode
    TaskName      = $TaskName
    RunTime       = $RunTime
    WorkspacePath = $WorkspacePath
    HasError      = $false
    Results       = @()
}

function Write-AARLog {
    param([string]$Message, [string]$Level = 'INFO')
    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    $logMessage = "[$timestamp] [$Level] [AAR-Scheduler] $Message"
    Write-Host $logMessage -ForegroundColor $(if ($Level -eq 'ERROR') { 'Red' } elseif ($Level -eq 'WARN') { 'Yellow' } else { 'Green' })
}

function Test-Prerequisites {
    """Check if required components are available"""
    Write-AARLog "🔍 Checking prerequisites..."

    # Check if Python is available
    try {
        $pythonVersion = python3 --version 2>$null
        if ($LASTEXITCODE -ne 0) {
            throw "Python3 not available"
        }
        Write-AARLog "✅ Python3 available: $pythonVersion"
    } catch {
        Write-AARLog "❌ Python3 not found. Please install Python 3.x" -Level 'ERROR'
        return $false
    }

    # Check if AAR reviewer script exists
    $reviewerScript = Join-Path $Context.WorkspacePath 'tools/aar-automation/aar-workflow-reviewer.py'
    if (-not (Test-Path $reviewerScript)) {
        Write-AARLog "❌ AAR reviewer script not found: $reviewerScript" -Level 'ERROR'
        return $false
    }
    Write-AARLog "✅ AAR reviewer script found"

    # Check if workspace directory exists
    if (-not (Test-Path $Context.WorkspacePath)) {
        Write-AARLog "❌ Workspace path not found: $($Context.WorkspacePath)" -Level 'ERROR'
        return $false
    }
    Write-AARLog "✅ Workspace path verified"

    return $true
}

function Invoke-AARWorkflowReview {
    """Run AAR workflow review immediately"""
    Write-AARLog "🚀 Starting immediate AAR workflow review..."

    $reviewerScript = Join-Path $Context.WorkspacePath 'tools/aar-automation/aar-workflow-reviewer.py'
    $outputDir = Join-Path $Context.WorkspacePath 'reports/aar-workflow-review'

    # Ensure output directory exists
    if (-not (Test-Path $outputDir)) {
        New-Item -Path $outputDir -ItemType Directory -Force | Out-Null
        Write-AARLog "📁 Created output directory: $outputDir"
    }

    try {
        # Run the Python AAR reviewer
        $startTime = Get-Date

        Write-AARLog "🐍 Executing: python3 $reviewerScript --mode daily --output-dir $outputDir --auto-create-issues"

        $result = & python3 $reviewerScript --mode daily --output-dir $outputDir --auto-create-issues

        if ($LASTEXITCODE -eq 0) {
            $duration = (Get-Date) - $startTime
            Write-AARLog "✅ AAR workflow review completed successfully in $([Math]::Round($duration.TotalSeconds, 2)) seconds"

            # Parse results from output
            $insightsLine = $result | Where-Object { $_ -match "📊 Insights found: (\d+)" }
            $recommendationsLine = $result | Where-Object { $_ -match "🎯 Recommendations generated: (\d+)" }

            if ($insightsLine -and $insightsLine -match "(\d+)") {
                $Context.Results += "Insights found: $($Matches[1])"
            }
            if ($recommendationsLine -and $recommendationsLine -match "(\d+)") {
                $Context.Results += "Recommendations generated: $($Matches[1])"
            }

            Write-AARLog "📊 Review Results: $($Context.Results -join ', ')"
            return $true
        } else {
            Write-AARLog "❌ AAR workflow review failed with exit code: $LASTEXITCODE" -Level 'ERROR'
            Write-AARLog "Output: $($result -join "`n")" -Level 'ERROR'
            return $false
        }
    } catch {
        Write-AARLog "❌ Error running AAR workflow review: $($_.Exception.Message)" -Level 'ERROR'
        $Context.HasError = $true
        return $false
    }
}

function Register-AARScheduledTask {
    """Create scheduled task for daily AAR reviews"""
    Write-AARLog "📅 Setting up scheduled task: $($Context.TaskName)"

    # Check if running on Windows (scheduled tasks are Windows-specific)
    if ($PSVersionTable.Platform -and $PSVersionTable.Platform -ne 'Win32NT') {
        Write-AARLog "⚠️  Scheduled tasks are Windows-specific. Creating cron job suggestion instead..." -Level 'WARN'

        # Create a cron job suggestion for Linux/macOS
        $cronCommand = "0 8 * * * cd $($Context.WorkspacePath) && python3 tools/aar-automation/aar-workflow-reviewer.py --mode daily --auto-create-issues"
        $cronFile = Join-Path $Context.WorkspacePath 'tools/aar-automation/aar-cron-setup.sh'

        $cronScript = @"
#!/bin/bash
# AAR Workflow Review Cron Setup
# Add this line to your crontab (crontab -e):
# $cronCommand

echo "To schedule daily AAR workflow reviews, run:"
echo "crontab -e"
echo ""
echo "Then add this line:"
echo "$cronCommand"
echo ""
echo "This will run the AAR review daily at 8:00 AM"
"@

        Set-Content -Path $cronFile -Value $cronScript -Encoding UTF8
        Write-AARLog "📄 Cron setup script created: $cronFile"
        Write-AARLog "🔧 Run the script for cron installation instructions"
        return $true
    }

    # Windows Scheduled Task creation
    try {
        # Remove existing task if it exists
        $existingTask = Get-ScheduledTask -TaskName $Context.TaskName -ErrorAction SilentlyContinue
        if ($existingTask) {
            if ($Force) {
                Unregister-ScheduledTask -TaskName $Context.TaskName -Confirm:$false
                Write-AARLog "🗑️  Removed existing task: $($Context.TaskName)"
            } else {
                Write-AARLog "⚠️  Task already exists. Use -Force to replace it." -Level 'WARN'
                return $false
            }
        }

        # Create the scheduled task
        $action = New-ScheduledTaskAction -Execute 'python3' -Argument "--mode daily --auto-create-issues" -WorkingDirectory $Context.WorkspacePath
        $trigger = New-ScheduledTaskTrigger -Daily -At $Context.RunTime
        $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
        $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive

        $task = New-ScheduledTask -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description "Daily AAR Workflow Improvement Review"

        Register-ScheduledTask -TaskName $Context.TaskName -InputObject $task | Out-Null

        Write-AARLog "✅ Scheduled task created successfully"
        Write-AARLog "⏰ Will run daily at $($Context.RunTime)"
        return $true
    } catch {
        Write-AARLog "❌ Failed to create scheduled task: $($_.Exception.Message)" -Level 'ERROR'
        $Context.HasError = $true
        return $false
    }
}

function Get-AARTaskStatus {
    """Check status of AAR scheduled task"""
    Write-AARLog "📊 Checking AAR task status..."

    if ($PSVersionTable.Platform -and $PSVersionTable.Platform -ne 'Win32NT') {
        Write-AARLog "📋 Checking cron jobs for AAR workflow review..."
        try {
            $cronJobs = crontab -l 2>/dev/null | grep -i "aar-workflow-reviewer" 2>/dev/null
            if ($cronJobs) {
                Write-AARLog "✅ Found AAR cron job: $cronJobs"
            } else {
                Write-AARLog "❌ No AAR cron job found"
            }
        } catch {
            Write-AARLog "⚠️  Could not check cron jobs: $($_.Exception.Message)" -Level 'WARN'
        }
        return
    }

    # Windows scheduled task status
    try {
        $task = Get-ScheduledTask -TaskName $Context.TaskName -ErrorAction SilentlyContinue
        if ($task) {
            $taskInfo = Get-ScheduledTaskInfo -TaskName $Context.TaskName
            Write-AARLog "✅ Task found: $($Context.TaskName)"
            Write-AARLog "📅 State: $($task.State)"
            Write-AARLog "⏰ Next run: $($taskInfo.NextRunTime)"
            Write-AARLog "🏃 Last run: $($taskInfo.LastRunTime)"
            Write-AARLog "📊 Last result: $($taskInfo.LastTaskResult)"

            # Show task details
            $triggers = $task.Triggers
            foreach ($trigger in $triggers) {
                Write-AARLog "🕐 Schedule: $($trigger.StartBoundary)"
            }
        } else {
            Write-AARLog "❌ No scheduled task found with name: $($Context.TaskName)"
        }
    } catch {
        Write-AARLog "❌ Error checking task status: $($_.Exception.Message)" -Level 'ERROR'
        $Context.HasError = $true
    }
}

function Remove-AARScheduledTask {
    """Remove AAR scheduled task"""
    Write-AARLog "🗑️  Removing AAR scheduled task..."

    if ($PSVersionTable.Platform -and $PSVersionTable.Platform -ne 'Win32NT') {
        Write-AARLog "📋 To remove AAR cron job manually:" -Level 'WARN'
        Write-AARLog "1. Run: crontab -e"
        Write-AARLog "2. Remove lines containing 'aar-workflow-reviewer'"
        Write-AARLog "3. Save and exit"
        return
    }

    try {
        $task = Get-ScheduledTask -TaskName $Context.TaskName -ErrorAction SilentlyContinue
        if ($task) {
            Unregister-ScheduledTask -TaskName $Context.TaskName -Confirm:$false
            Write-AARLog "✅ Scheduled task removed successfully"
        } else {
            Write-AARLog "⚠️  No task found with name: $($Context.TaskName)" -Level 'WARN'
        }
    } catch {
        Write-AARLog "❌ Error removing scheduled task: $($_.Exception.Message)" -Level 'ERROR'
        $Context.HasError = $true
    }
}

# Main execution
try {
    Write-AARLog "🚀 Starting AAR Workflow Scheduler in $($Context.Mode) mode..."

    # Validate prerequisites
    if (-not (Test-Prerequisites)) {
        Write-AARLog "❌ Prerequisites check failed" -Level 'ERROR'
        exit 1
    }

    # Execute based on mode
    switch ($Context.Mode) {
        'Schedule' {
            $success = Register-AARScheduledTask
            if ($success) {
                Write-AARLog "🎯 Scheduled task setup completed successfully"
            }
        }
        'RunNow' {
            $success = Invoke-AARWorkflowReview
            if ($success) {
                Write-AARLog "🎯 Manual AAR review completed successfully"
            }
        }
        'Status' {
            Get-AARTaskStatus
        }
        'Remove' {
            Remove-AARScheduledTask
        }
    }

    # Final status
    if (-not $Context.HasError) {
        Write-AARLog "✅ AAR Workflow Scheduler operation completed successfully"
        Write-AARLog "📈 Creating the Future through automated continuous improvement"
        Write-AARLog "🌟 Inspiring Greatness via data-driven excellence"
        Write-AARLog "⚡ Accelerating Impact through proactive workflow optimization"
    } else {
        Write-AARLog "❌ Operation completed with errors" -Level 'ERROR'
        exit 1
    }
} catch {
    Write-AARLog "❌ Script execution failed: $($_.Exception.Message)" -Level 'ERROR'
    $Context.HasError = $true
    exit 1
} finally {
    # Cleanup and logging
    Write-AARLog "🧹 AAR Scheduler operation complete"

    if ($Context.Results.Count -gt 0) {
        Write-AARLog "📊 Results: $($Context.Results -join '; ')"
    }
}
