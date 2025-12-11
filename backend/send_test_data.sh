#!/bin/bash
# Send test telemetry data to the backend

API_URL="http://localhost:8000"

echo "Sending test telemetry data..."

# House 01 - Phase R (L1)
curl -X POST "$API_URL/telemetry" \
  -H "Content-Type: application/json" \
  -d '{
    "house_id": "House_01",
    "voltage": 238.4,
    "current": 10.5,
    "power_kw": 2.4,
    "phase": "L1"
  }'

sleep 0.5

# House 02 - Phase Y (L2)
curl -X POST "$API_URL/telemetry" \
  -H "Content-Type: application/json" \
  -d '{
    "house_id": "House_02",
    "voltage": 239.1,
    "current": 5.7,
    "power_kw": 1.3,
    "phase": "L2"
  }'

sleep 0.5

# House 03 - Phase B (L3)
curl -X POST "$API_URL/telemetry" \
  -H "Content-Type: application/json" \
  -d '{
    "house_id": "House_03",
    "voltage": 237.8,
    "current": 14.3,
    "power_kw": 3.1,
    "phase": "L3"
  }'

sleep 0.5

# House 04 - Phase R (L1) - EXPORT
curl -X POST "$API_URL/telemetry" \
  -H "Content-Type: application/json" \
  -d '{
    "house_id": "House_04",
    "voltage": 242.1,
    "current": -5.2,
    "power_kw": -1.2,
    "phase": "L1"
  }'

sleep 0.5

# House 05 - Phase Y (L2)
curl -X POST "$API_URL/telemetry" \
  -H "Content-Type: application/json" \
  -d '{
    "house_id": "House_05",
    "voltage": 238.9,
    "current": 12.1,
    "power_kw": 2.8,
    "phase": "L2"
  }'

sleep 0.5

# House 06 - Phase B (L3)
curl -X POST "$API_URL/telemetry" \
  -H "Content-Type: application/json" \
  -d '{
    "house_id": "House_06",
    "voltage": 239.5,
    "current": 6.2,
    "power_kw": 1.4,
    "phase": "L3"
  }'

sleep 0.5

# House 07 - Phase Y (L2)
curl -X POST "$API_URL/telemetry" \
  -H "Content-Type: application/json" \
  -d '{
    "house_id": "House_07",
    "voltage": 236.8,
    "current": 10.0,
    "power_kw": 2.2,
    "phase": "L2"
  }'

sleep 0.5

# House 08 - Phase R (L1)
curl -X POST "$API_URL/telemetry" \
  -H "Content-Type: application/json" \
  -d '{
    "house_id": "House_08",
    "voltage": 241.2,
    "current": 15.3,
    "power_kw": 3.5,
    "phase": "L1"
  }'

sleep 0.5

# Add more houses for better visualization
for i in {9..24}; do
  # Random phase
  PHASES=("L1" "L2" "L3")
  PHASE=${PHASES[$((RANDOM % 3))]}
  
  # Random voltage (235-245V)
  VOLTAGE=$(echo "235 + ($RANDOM % 10)" | bc)
  
  # Random current (1-15A)
  CURRENT=$(echo "scale=1; 1 + ($RANDOM % 140) / 10" | bc)
  
  # Random power (0.2-3.5 kW, some negative for export)
  if [ $((RANDOM % 5)) -eq 0 ]; then
    # 20% chance of export
    POWER=$(echo "scale=2; -0.5 - ($RANDOM % 15) / 10" | bc)
  else
    POWER=$(echo "scale=2; 0.2 + ($RANDOM % 33) / 10" | bc)
  fi
  
  curl -X POST "$API_URL/telemetry" \
    -H "Content-Type: application/json" \
    -d "{
      \"house_id\": \"House_$(printf '%02d' $i)\",
      \"voltage\": $VOLTAGE,
      \"current\": $CURRENT,
      \"power_kw\": $POWER,
      \"phase\": \"$PHASE\"
    }" > /dev/null 2>&1
  
  sleep 0.2
done

echo ""
echo "✅ Test data sent successfully!"
echo "Check the dashboard at http://localhost:5174"
