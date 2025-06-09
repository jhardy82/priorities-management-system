# Quick Priority Reference - Work-Home Environment Management
# Usage: .\Get-CurrentPriorities.ps1 [-ShowHome] [-UpdateContext]

[CmdletBinding()]
param(
    [switch]$ShowHome,
    [switch]$UpdateContext,
    [ValidateSet("Auto", "Work", "Home")]
    [string]$ForceEnvironment = "Auto"
)

$WorkPrioritiesPath = "$PSScriptRoot\WORK-PRIORITIES.md"
$HomePrioritiesPath = "$PSScriptRoot\HOME-PRIORITIES.md"

function Get-CurrentEnvironmentContext {
    param([string]$ForceEnvironment = "Auto")

    $computerName = $env:COMPUTERNAME.ToLower()

    # Detect work vs home environment based on computer name patterns
    # Work devices typically have corporate naming conventions
    $isWorkDevice = $computerName -match "avanade|corp|work|laptop-\d+|pc-\d+|desktop-\d+" -or
                    $computerName -match "^[a-z]{2,4}-\d+$" -or  # Corporate naming patterns
                    $env:USERDNSDOMAIN -like "*avanade*"        # Domain check

    # Apply manual override if specified
    if ($ForceEnvironment -eq "Work") { $isWorkDevice = $true }
    elseif ($ForceEnvironment -eq "Home") { $isWorkDevice = $false }

    [PSCustomObject]@{
        CurrentTime = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        DayOfWeek = (Get-Date).DayOfWeek
        ComputerName = $env:COMPUTERNAME
        IsWorkDevice = $isWorkDevice
        EnvironmentType = if($isWorkDevice) { "WORK" } else { "HOME" }
        DetectionMethod = if($ForceEnvironment -ne "Auto") { "Manual Override ($ForceEnvironment)" } else { "Auto-Detected" }
        UserName = $env:USERNAME
        Domain = $env:USERDNSDOMAIN
        PowerShellVersion = $PSVersionTable.PSVersion.ToString()
        WorkingDirectory = $PWD.Path
    }
}

function Show-PriorityFile {
    param(
        [string]$FilePath,
        [string]$Environment
    )

    if (Test-Path $FilePath) {
        Write-Host "`n[TARGET] $Environment PRIORITIES" -ForegroundColor Cyan
        Write-Host ("=" * 50) -ForegroundColor Gray

        $content = Get-Content $FilePath -Raw

        # Extract current tasks (lines starting with - [ ])
        $currentTasks = $content -split "`n" | Where-Object { $_ -match "^- \[ \]" }

        if ($currentTasks) {
            Write-Host "`n[ACTIVE] CURRENT TASKS:" -ForegroundColor Yellow
            $currentTasks | ForEach-Object {
                $task = $_ -replace "^- \[ \] ", "  * "
                Write-Host $task -ForegroundColor White
            }
        }

        # Extract priority levels
        $p0Tasks = $content -split "`n" | Where-Object { $_ -match "P0|D0" }
        $p1Tasks = $content -split "`n" | Where-Object { $_ -match "P1|D1" }

        if ($p0Tasks) {
            Write-Host "`n[CRITICAL] P0/D0 PRIORITY:" -ForegroundColor Red
            $p0Tasks | ForEach-Object {
                if ($_ -match "- \[ \]") {
                    $task = $_ -replace "^.*- \[ \] ", "  * "
                    Write-Host $task -ForegroundColor Red
                }
            }
        }

        if ($p1Tasks) {
            Write-Host "`n[HIGH] P1/D1 PRIORITY:" -ForegroundColor Magenta
            $p1Tasks | ForEach-Object {
                if ($_ -match "- \[ \]") {
                    $task = $_ -replace "^.*- \[ \] ", "  * "
                    Write-Host $task -ForegroundColor Magenta
                }
            }
        }
    } else {
        Write-Warning "Priority file not found: $FilePath"
    }
}

# Main execution
Clear-Host
$context = Get-CurrentEnvironmentContext -ForceEnvironment $ForceEnvironment

Write-Host "[SYSTEM] PRIORITY MANAGEMENT SYSTEM" -ForegroundColor Green
Write-Host "Generated: $($context.CurrentTime)" -ForegroundColor Gray
Write-Host "Device: $($context.ComputerName) ($($context.EnvironmentType))" -ForegroundColor Gray
Write-Host "Detection: $($context.DetectionMethod)" -ForegroundColor Gray
Write-Host "Current Focus: $($context.EnvironmentType) MODE" -ForegroundColor $(if($context.IsWorkDevice){"Blue"}else{"Cyan"})

# Show work priorities
Show-PriorityFile -FilePath $WorkPrioritiesPath -Environment "WORK"

# Show home priorities if requested
if ($ShowHome) {
    Show-PriorityFile -FilePath $HomePrioritiesPath -Environment "HOME"

    Write-Host "`n[INTEGRATION] CROSS-PLATFORM OPPORTUNITIES:" -ForegroundColor Cyan
    Write-Host "  * Python-PowerShell bridge development" -ForegroundColor White
    Write-Host "  * COF integration examples for work projects" -ForegroundColor White
    Write-Host "  * Cross-platform automation tools" -ForegroundColor White
}

# Quick actions
Write-Host "`n[ACTIONS] QUICK COMMANDS:" -ForegroundColor Green
Write-Host "  * Edit work priorities: code `"$WorkPrioritiesPath`"" -ForegroundColor Gray
if ($ShowHome) {
    Write-Host "  * Edit home priorities: code `"$HomePrioritiesPath`"" -ForegroundColor Gray
}
Write-Host "  * Update contexts: Get-CurrentPriorities -UpdateContext" -ForegroundColor Gray
Write-Host "  * Show both environments: Get-CurrentPriorities -ShowHome" -ForegroundColor Gray
Write-Host "  * Force work mode: Get-CurrentPriorities -ForceEnvironment Work" -ForegroundColor Gray
Write-Host "  * Force home mode: Get-CurrentPriorities -ForceEnvironment Home" -ForegroundColor Gray

# Context switching support
if ($context.IsWorkDevice) {
    Write-Host "`n[WORK] ENTERPRISE FOCUS ACTIVATED" -ForegroundColor Blue
    Write-Host "Device: $($context.ComputerName)" -ForegroundColor Blue
    Write-Host "Recommended: Enterprise PowerShell, SCCM, Win11FUActions" -ForegroundColor Blue
} else {
    Write-Host "`n[HOME] LEARNING FOCUS AVAILABLE" -ForegroundColor Cyan
    Write-Host "Device: $($context.ComputerName)" -ForegroundColor Cyan
    Write-Host "Recommended: Python learning, COF development, universal tools" -ForegroundColor Cyan
}
