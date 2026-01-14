# 🧪 Testing Guide: FastAPI + React Integration

## Quick Test Setup

### Prerequisites
1. **FastAPI Backend** running on `http://localhost:8000`
2. **React Frontend** running on `http://localhost:3000`
3. Python `requests` library installed

## 🚀 Testing Methods

### Method 1: Automated Test Script (Recommended)

Use the comprehensive test script that simulates realistic traffic data:

```bash
# Run interactive mode
python test_data_sender.py

# Or run directly
python test_data_sender.py single       # Send one test data
python test_data_sender.py continuous   # Stream data continuously
```

**Or use the batch file:**
```bash
run_test.bat
```

### Method 2: Manual curl Testing

Send test data using curl command:

```bash
curl -X POST "http://localhost:8000/api/v1/ingest/simulation" \
  -H "Content-Type: application/json" \
  -d @sample_test_data.json
```

### Method 3: API Documentation Testing

1. Open `http://localhost:8000/docs`
2. Navigate to `POST /api/v1/ingest/simulation`
3. Click "Try it out"
4. Paste the sample JSON data
5. Click "Execute"

## 📊 What to Expect

### In the React Dashboard
- **Real-time traffic light updates** (Green/Yellow/Red)
- **Live vehicle counts** per direction
- **Queue length indicators**
- **Wait time metrics**
- **Connection status notifications**

### In the Browser Console
- WebSocket connection messages
- Data update logs
- Error messages (if any)

### In the Backend Terminal
- Incoming data validation
- WebSocket client connections
- Broadcasting confirmations

## 🔍 Validation Checklist

### ✅ Backend Health Check
```bash
curl http://localhost:8000/health
```
Expected response:
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2023-12-13T19:30:00Z",
  "service": "traffic-analytics-api"
}
```

### ✅ WebSocket Connection
1. Open React dashboard
2. Open browser dev tools → Network → WS
3. Should see WebSocket connection to `ws://localhost:8000/ws/updates`
4. Send test data - should see real-time messages

### ✅ Data Flow Verification
1. Send test data using any method above
2. Check React dashboard immediately updates
3. Verify traffic light colors change
4. Confirm vehicle counts update
5. Check queue lengths adjust

## 🚨 Troubleshooting

### Problem: Backend Connection Failed
```
❌ Cannot connect to backend at http://localhost:8000
```
**Solution:**
- Start FastAPI backend: `uvicorn app.main:app --reload`
- Check port 8000 is available
- Verify no firewall blocking

### Problem: WebSocket Connection Failed
```
WebSocket connection to 'ws://localhost:8000/ws/updates' failed
```
**Solution:**
- Ensure backend is running
- Check CORS settings in FastAPI
- Verify WebSocket endpoint is accessible

### Problem: No Data Updates in Dashboard
**Check:**
- Browser console for errors
- Network tab for failed requests  
- Backend terminal for incoming data
- WebSocket connection status

### Problem: Invalid JSON Data
```
❌ Failed to send data: HTTP 422
```
**Solution:**
- Verify JSON structure matches expected format
- Check all required fields are present
- Validate timestamp format

## 📱 Test Data Examples

### Basic Test Data
```json
{
  "data": {
    "simulation_id": "TEST_001",
    "timestamp": "2023-12-13T19:30:00Z",
    "intersection_id": "INT_001",
    "current_phase": {
      "phase_id": 0,
      "active_directions": ["east", "west"],
      "status": "GREEN",
      "remaining_time": 25.0
    },
    "direction_metrics": {
      "east": {
        "vehicle_counts": {"car": 5, "bus": 1, "truck": 0, "bike": 2},
        "queue_length": 3,
        "vehicles_crossed": 10,
        "avg_wait_time": 15.5,
        "emergency_vehicle_present": false
      }
    },
    "overall_metrics": {
      "total_vehicles_passed": 25,
      "avg_wait_time_all_sides": 18.0,
      "throughput": 0.6,
      "avg_speed": 25.0,
      "cycle_time": 90.0
    }
  }
}
```

### Emergency Vehicle Test
```json
{
  "data": {
    "simulation_id": "EMERGENCY_TEST",
    "current_phase": {
      "phase_id": 1,
      "active_directions": ["north"],
      "status": "GREEN",
      "remaining_time": 60.0
    },
    "direction_metrics": {
      "north": {
        "vehicle_counts": {"car": 10, "bus": 1, "truck": 0, "bike": 0},
        "queue_length": 0,
        "vehicles_crossed": 15,
        "avg_wait_time": 5.0,
        "emergency_vehicle_present": true
      }
    }
  }
}
```

## 🎯 Success Criteria

### ✅ Integration Working When:
1. **Backend receives data** without errors
2. **WebSocket broadcasts** data to clients
3. **React dashboard updates** in real-time
4. **Traffic lights change** based on active directions
5. **Vehicle counts display** correctly
6. **Queue lengths update** dynamically
7. **No console errors** in browser
8. **Connection status** shows as connected

## 📈 Performance Testing

### Load Testing
```bash
# Run multiple parallel streams (advanced)
python test_data_sender.py continuous &
python test_data_sender.py continuous &
python test_data_sender.py continuous &
```

### Stress Testing
- Modify `UPDATE_INTERVAL` to 0.5 seconds in test script
- Send high-frequency updates
- Monitor memory usage in both frontend and backend

## 🔧 Debugging Commands

### Check API Endpoints
```bash
# Health check
curl http://localhost:8000/health

# Get latest data
curl http://localhost:8000/api/simulation/latest

# Get optimized dashboard data
curl http://localhost:8000/api/dashboard/intersection-status

# Check system info
curl http://localhost:8000/system/info
```

### Monitor Logs
```bash
# Backend logs (if configured)
tail -f app.log

# Or check terminal output for uvicorn logs
```

## 🎉 Success!

When everything works, you should see:
- ✅ Smooth real-time data updates
- ✅ Responsive traffic light animations  
- ✅ Live vehicle count changes
- ✅ Dynamic queue length indicators
- ✅ Emergency vehicle alerts
- ✅ Connection status indicators
- ✅ Toast notifications for events

**Your AI-powered traffic management system is fully operational!** 🚦