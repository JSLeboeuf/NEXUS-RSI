# NEXUS System Monitor - PowerShell Tools
# Advanced Windows integration for system monitoring

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("install", "start", "stop", "status", "logs", "service")]
    [string]$Action = "status",
    
    [Parameter(Mandatory=$false)]
    [switch]$AsService,
    
    [Parameter(Mandatory=$false)]
    [switch]$Force
)

# Configuration
$NEXUS_ROOT = "C:\Users\Jean-SamuelLeboeuf\NEXUS-RSI"
$SERVICE_NAME = "NEXUS System Monitor"
$TASK_NAME = "NEXUS-SystemMonitor"

function Write-StatusMessage {
    param([string]$Message, [string]$Type = "INFO")
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $color = switch ($Type) {
        "SUCCESS" { "Green" }
        "WARNING" { "Yellow" }
        "ERROR" { "Red" }
        default { "White" }
    }
    
    Write-Host "[$timestamp] [$Type] $Message" -ForegroundColor $color
}

function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Test-DockerRunning {
    try {
        $dockerStatus = docker version --format "{{.Server.Version}}" 2>$null
        if ($dockerStatus) {
            Write-StatusMessage "Docker daemon is running (version: $dockerStatus)" "SUCCESS"
            return $true
        }
    }
    catch {
        Write-StatusMessage "Docker daemon is not running or not accessible" "WARNING"
        return $false
    }
    return $false
}

function Get-SystemMonitorStatus {
    Write-StatusMessage "Checking NEXUS System Monitor status..."
    
    # Check if Python process is running
    $pythonProcesses = Get-Process python -ErrorAction SilentlyContinue | Where-Object {
        $_.CommandLine -like "*system_monitor.py*"
    }
    
    if ($pythonProcesses) {
        Write-StatusMessage "System Monitor is running (PID: $($pythonProcesses.Id -join ', '))" "SUCCESS"
        
        # Get process details
        foreach ($proc in $pythonProcesses) {
            $startTime = $proc.StartTime
            $uptime = (Get-Date) - $startTime
            $memory = [math]::Round($proc.WorkingSet / 1MB, 2)
            
            Write-StatusMessage "  Process ID: $($proc.Id)" "INFO"
            Write-StatusMessage "  Start Time: $startTime" "INFO"
            Write-StatusMessage "  Uptime: $($uptime.ToString('dd\.hh\:mm\:ss'))" "INFO"
            Write-StatusMessage "  Memory Usage: $memory MB" "INFO"
        }
    }
    else {
        Write-StatusMessage "System Monitor is not running" "WARNING"
    }
    
    # Check scheduled task
    try {
        $task = Get-ScheduledTask -TaskName $TASK_NAME -ErrorAction SilentlyContinue
        if ($task) {
            Write-StatusMessage "Scheduled task exists: $($task.State)" "INFO"
        }
        else {
            Write-StatusMessage "Scheduled task not found" "WARNING"
        }
    }
    catch {
        Write-StatusMessage "Could not check scheduled task status" "WARNING"
    }
    
    # Check Docker containers
    Test-DockerRunning | Out-Null
    
    # Check database
    $dbPath = Join-Path $NEXUS_ROOT "nexus_metrics.db"
    if (Test-Path $dbPath) {
        $dbSize = [math]::Round((Get-Item $dbPath).Length / 1MB, 2)
        Write-StatusMessage "Metrics database exists (size: $dbSize MB)" "SUCCESS"
    }
    else {
        Write-StatusMessage "Metrics database not found" "WARNING"
    }
    
    # Check log files
    $logDir = Join-Path $NEXUS_ROOT "logs\system_monitor"
    if (Test-Path $logDir) {
        $logFiles = Get-ChildItem $logDir -Filter "*.log" | Sort-Object LastWriteTime -Descending
        if ($logFiles) {
            $latestLog = $logFiles[0]
            $logAge = (Get-Date) - $latestLog.LastWriteTime
            Write-StatusMessage "Latest log: $($latestLog.Name) (updated $([math]::Round($logAge.TotalMinutes, 1)) minutes ago)" "INFO"
        }
    }
}

function Start-SystemMonitor {
    Write-StatusMessage "Starting NEXUS System Monitor..."
    
    # Change to NEXUS directory
    Set-Location $NEXUS_ROOT
    
    # Check if already running
    $existingProcess = Get-Process python -ErrorAction SilentlyContinue | Where-Object {
        $_.CommandLine -like "*system_monitor.py*"
    }
    
    if ($existingProcess -and -not $Force) {
        Write-StatusMessage "System Monitor is already running (PID: $($existingProcess.Id))" "WARNING"
        Write-StatusMessage "Use -Force to restart" "INFO"
        return
    }
    
    if ($existingProcess -and $Force) {
        Write-StatusMessage "Stopping existing process..." "INFO"
        Stop-Process -Id $existingProcess.Id -Force
        Start-Sleep -Seconds 2
    }
    
    # Start the monitor
    try {
        if ($AsService) {
            Write-StatusMessage "Starting as scheduled task..." "INFO"
            Start-ScheduledTask -TaskName $TASK_NAME
        }
        else {
            Write-StatusMessage "Starting in background..." "INFO"
            $job = Start-Job -ScriptBlock {
                param($nexusRoot)
                Set-Location $nexusRoot
                python agents/system_monitor.py
            } -ArgumentList $NEXUS_ROOT
            
            Write-StatusMessage "System Monitor started (Job ID: $($job.Id))" "SUCCESS"
        }
    }
    catch {
        Write-StatusMessage "Failed to start System Monitor: $($_.Exception.Message)" "ERROR"
    }
}

function Stop-SystemMonitor {
    Write-StatusMessage "Stopping NEXUS System Monitor..."
    
    # Stop Python processes
    $pythonProcesses = Get-Process python -ErrorAction SilentlyContinue | Where-Object {
        $_.CommandLine -like "*system_monitor.py*"
    }
    
    if ($pythonProcesses) {
        foreach ($proc in $pythonProcesses) {
            Write-StatusMessage "Stopping process $($proc.Id)..." "INFO"
            Stop-Process -Id $proc.Id -Force
        }
        Write-StatusMessage "System Monitor stopped" "SUCCESS"
    }
    else {
        Write-StatusMessage "System Monitor is not running" "WARNING"
    }
    
    # Stop scheduled task if running
    try {
        $task = Get-ScheduledTask -TaskName $TASK_NAME -ErrorAction SilentlyContinue
        if ($task -and $task.State -eq "Running") {
            Stop-ScheduledTask -TaskName $TASK_NAME
            Write-StatusMessage "Stopped scheduled task" "INFO"
        }
    }
    catch {
        Write-StatusMessage "Could not stop scheduled task" "WARNING"
    }
}

function Install-SystemMonitorService {
    if (-not (Test-Administrator)) {
        Write-StatusMessage "Administrator privileges required to install service" "ERROR"
        Write-StatusMessage "Please run PowerShell as Administrator" "INFO"
        return
    }
    
    Write-StatusMessage "Installing NEXUS System Monitor as Windows service..." "INFO"
    
    # Create scheduled task
    $action = New-ScheduledTaskAction -Execute "python" -Argument "agents/system_monitor.py" -WorkingDirectory $NEXUS_ROOT
    
    $trigger = New-ScheduledTaskTrigger -AtStartup
    
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
    
    $principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -RunLevel Highest
    
    try {
        Register-ScheduledTask -TaskName $TASK_NAME -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description "NEXUS System Monitor - Real-time system monitoring and alerting"
        
        Write-StatusMessage "Scheduled task created successfully" "SUCCESS"
        Write-StatusMessage "Task Name: $TASK_NAME" "INFO"
        Write-StatusMessage "The monitor will start automatically on system boot" "INFO"
        
    }
    catch {
        Write-StatusMessage "Failed to create scheduled task: $($_.Exception.Message)" "ERROR"
    }
}

function Show-SystemMonitorLogs {
    $logDir = Join-Path $NEXUS_ROOT "logs\system_monitor"
    
    if (-not (Test-Path $logDir)) {
        Write-StatusMessage "Log directory not found: $logDir" "ERROR"
        return
    }
    
    $logFiles = Get-ChildItem $logDir -Filter "*.log" | Sort-Object LastWriteTime -Descending
    
    if (-not $logFiles) {
        Write-StatusMessage "No log files found" "WARNING"
        return
    }
    
    $latestLog = $logFiles[0]
    Write-StatusMessage "Showing latest log: $($latestLog.Name)" "INFO"
    Write-StatusMessage "=" * 80 "INFO"
    
    Get-Content $latestLog.FullName -Tail 50 | ForEach-Object {
        if ($_ -match "ERROR|CRITICAL") {
            Write-Host $_ -ForegroundColor Red
        }
        elseif ($_ -match "WARNING") {
            Write-Host $_ -ForegroundColor Yellow
        }
        elseif ($_ -match "ALERT") {
            Write-Host $_ -ForegroundColor Magenta
        }
        else {
            Write-Host $_
        }
    }
}

function Install-Dependencies {
    Write-StatusMessage "Installing Python dependencies..." "INFO"
    
    Set-Location $NEXUS_ROOT
    
    $packages = @(
        "psutil>=5.9.0",
        "docker>=6.0.0",
        "requests>=2.28.0",
        "watchdog>=2.1.0"
    )
    
    foreach ($package in $packages) {
        try {
            Write-StatusMessage "Installing $package..." "INFO"
            python -m pip install $package 2>&1 | Out-Null
            if ($LASTEXITCODE -eq 0) {
                Write-StatusMessage "Installed $package" "SUCCESS"
            }
            else {
                Write-StatusMessage "Failed to install $package" "ERROR"
            }
        }
        catch {
            Write-StatusMessage "Error installing $package: $($_.Exception.Message)" "ERROR"
        }
    }
    
    # Run the Python setup script
    Write-StatusMessage "Running Python setup script..." "INFO"
    try {
        python agents/setup_system_monitor.py
        Write-StatusMessage "Setup completed" "SUCCESS"
    }
    catch {
        Write-StatusMessage "Setup script failed: $($_.Exception.Message)" "ERROR"
    }
}

# Main execution
Write-StatusMessage "NEXUS System Monitor - PowerShell Tools" "INFO"
Write-StatusMessage "Action: $Action" "INFO"

switch ($Action) {
    "install" {
        Install-Dependencies
        if ($AsService) {
            Install-SystemMonitorService
        }
    }
    
    "start" {
        Start-SystemMonitor
    }
    
    "stop" {
        Stop-SystemMonitor
    }
    
    "status" {
        Get-SystemMonitorStatus
    }
    
    "logs" {
        Show-SystemMonitorLogs
    }
    
    "service" {
        Install-SystemMonitorService
    }
    
    default {
        Write-StatusMessage "Unknown action: $Action" "ERROR"
        Write-StatusMessage "Available actions: install, start, stop, status, logs, service" "INFO"
    }
}

Write-StatusMessage "Operation completed" "INFO"