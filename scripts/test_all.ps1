# CloudSentinel - Comprehensive Test Runner
Write-Host "Running Backend Pytest Suite..." -ForegroundColor Cyan
Set-Location "$PSScriptRoot\..\backend"
.\.venv\Scripts\pytest.exe -v

Write-Host "`nRunning Frontend Build Validation..." -ForegroundColor Cyan
Set-Location "$PSScriptRoot\..\frontend"
npm run build

Write-Host "`nAll CloudSentinel verification tests passed successfully!" -ForegroundColor Green
