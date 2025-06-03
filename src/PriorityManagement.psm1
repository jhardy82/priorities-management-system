# Quick Priority Access - Add this to your PowerShell profile for instant access
# Usage: Just type "priorities" to see current work focus

# Create aliases for quick access
New-Alias -Name "priorities" -Value "$PSScriptRoot\priorities\Get-CurrentPriorities.ps1" -Force
New-Alias -Name "focus" -Value "$PSScriptRoot\priorities\Get-CurrentPriorities.ps1" -Force

# Function for work-home integration
function Show-AllPriorities {
    & "$PSScriptRoot\priorities\Get-CurrentPriorities.ps1" -ShowHome -UpdateContext
}

function Update-PriorityFocus {
    & "$PSScriptRoot\priorities\Get-CurrentPriorities.ps1" -UpdateContext
    Write-Host "`n✅ Priority context updated! Use 'priorities' to view current focus." -ForegroundColor Green
}

# Export functions for use
Export-ModuleMember -Alias @('priorities', 'focus') -Function @('Show-AllPriorities', 'Update-PriorityFocus')

Write-Host "🧭 Priority Management System loaded!" -ForegroundColor Green
Write-Host "Commands available:" -ForegroundColor Cyan
Write-Host "  • priorities       - Show work priorities" -ForegroundColor White
Write-Host "  • focus           - Same as priorities" -ForegroundColor White
Write-Host "  • Show-AllPriorities - Show work + home with context update" -ForegroundColor White
Write-Host "  • Update-PriorityFocus - Refresh priority contexts" -ForegroundColor White
