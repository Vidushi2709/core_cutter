# Run all consumption test cases
# PowerShell script to execute all consume-only test scenarios

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "CONSUMPTION TEST SUITE" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "Make sure the FastAPI server is running (python app.py)`n" -ForegroundColor Yellow
Read-Host "Press Enter to start tests"

# Test 1: Balanced
Write-Host "`n[1/5] Running: Balanced Consumption Test" -ForegroundColor Green
python test_consume_balanced.py
Start-Sleep -Seconds 3

# Test 2: Light Imbalance
Write-Host "`n[2/5] Running: Light Imbalance Test" -ForegroundColor Green
python test_consume_light.py
Start-Sleep -Seconds 3

# Test 3: Original imbalanced (from test_consume_only.py)
Write-Host "`n[3/5] Running: Heavy Imbalance Test" -ForegroundColor Green
python test_consume_only.py
Start-Sleep -Seconds 3

# Test 4: Small Houses
Write-Host "`n[4/5] Running: Small Houses Test" -ForegroundColor Green
python test_consume_small_houses.py
Start-Sleep -Seconds 3

# Test 5: Critical Imbalance
Write-Host "`n[5/5] Running: Critical Imbalance Test" -ForegroundColor Green
python test_consume_critical.py

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "ALL TESTS COMPLETED" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "Summary of test cases:" -ForegroundColor Yellow
Write-Host "  1. Balanced        - No switching expected"
Write-Host "  2. Light Imbalance - Minor switching expected"
Write-Host "  3. Heavy Imbalance - Multiple switches expected"
Write-Host "  4. Small Houses    - Tests 100W+ threshold"
Write-Host "  5. Critical        - Aggressive balancing expected"
Write-Host "`nCheck dashboard at: http://localhost:5500/dashboard.html`n" -ForegroundColor Green
