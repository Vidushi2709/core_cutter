# MANUAL TEST DATA - PowerShell Examples
# Make sure your FastAPI server is running: python app.py

# Example 1: Send a single house consuming power
Invoke-RestMethod -Uri "http://localhost:8000/telemetry" -Method POST -ContentType "application/json" -Body '{
    "house_id": "H1",
    "voltage": 230.0,
    "current": 5.0,
    "power_kw": 1.2,
    "phase": "L1"
}'

# Example 2: Send a house exporting power (solar panel)
Invoke-RestMethod -Uri "http://localhost:8000/telemetry" -Method POST -ContentType "application/json" -Body '{
    "house_id": "H2",
    "voltage": 235.0,
    "current": -3.0,
    "power_kw": -0.7,
    "phase": "L2"
}'

# Example 3: Send multiple houses quickly (Critical Imbalance scenario)
$houses = @(
    @{house_id="H1"; voltage=230; current=8; power_kw=1.8; phase="L1"}
    @{house_id="H2"; voltage=230; current=5; power_kw=1.0; phase="L1"}
    @{house_id="H3"; voltage=230; current=6; power_kw=1.2; phase="L1"}
    @{house_id="B1"; voltage=230; current=2; power_kw=0.4; phase="L1"}
    @{house_id="B2"; voltage=230; current=12; power_kw=2.4; phase="L1"}
    @{house_id="V1"; voltage=230; current=3; power_kw=0.7; phase="L1"}
)

foreach ($house in $houses) {
    $json = $house | ConvertTo-Json
    Write-Host "Sending: $($house.house_id)"
    Invoke-RestMethod -Uri "http://localhost:8000/telemetry" -Method POST -ContentType "application/json" -Body $json
    Start-Sleep -Milliseconds 200
}

Write-Host "`nDone! Check dashboard at http://localhost:5500/dashboard.html"

# Example 4: Check current status
Invoke-RestMethod -Uri "http://localhost:8000/analytics/status" -Method GET

# Example 5: View switch history
Invoke-RestMethod -Uri "http://localhost:8000/analytics/switches?limit=5" -Method GET
