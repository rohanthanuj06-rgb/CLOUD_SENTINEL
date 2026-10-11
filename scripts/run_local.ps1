# CloudSentinel - One-Click Local Launcher (PowerShell)
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   CLOUDSENTINEL - Virtual Infrastructure Self-Healing   " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$CurrentDir = Get-Location

# 1. Start Backend in separate process
Write-Host "[1/2] Starting CloudSentinel Controller Backend on port 8000..." -ForegroundColor Green
$BackendProcess = Start-Process -FilePath "powershell.exe" -ArgumentList "-NoExit", "-Command", "cd '$CurrentDir\backend'; .\.venv\Scripts\uvicorn.exe app.main:app --host 0.0.0.0 --port 8000 --reload" -PassThru

Start-Sleep -Seconds 3

# 2. Start Frontend in separate process
Write-Host "[2/2] Starting React Operations Dashboard on port 5173..." -ForegroundColor Green
$FrontendProcess = Start-Process -FilePath "powershell.exe" -ArgumentList "-NoExit", "-Command", "cd '$CurrentDir\frontend'; npm run dev -- --host" -PassThru

Write-Host "CloudSentinel Platform is online!" -ForegroundColor Cyan
Write-Host "API Swagger Docs: http://localhost:8000/docs" -ForegroundColor Yellow
Write-Host "Dashboard Web UI: http://localhost:5173" -ForegroundColor Yellow
Write-Host "Press Ctrl+C in respective windows to stop." -ForegroundColor White
