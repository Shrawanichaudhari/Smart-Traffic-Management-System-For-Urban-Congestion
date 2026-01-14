# Traffic Dashboard Integration Guide

## 🚀 Complete Integration: FastAPI Backend + React Frontend

This guide explains how to run the integrated traffic management system with real-time data from your simulation.

## 📋 Prerequisites

- Python 3.11+
- Node.js 16+ and npm/yarn
- Redis server (for real-time data)
- PostgreSQL (for analytics data)

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Simulation    │───▶│  FastAPI Server │───▶│ React Dashboard │
│                 │    │                 │    │                 │
│ - Generates     │    │ - REST APIs     │    │ - Real-time UI  │
│   JSON data     │    │ - WebSocket     │    │ - Charts        │
│ - Sends to API  │    │ - Redis cache   │    │ - Analytics     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### Step 1: Start the FastAPI Backend

```bash
# Navigate to backend directory
cd "Traffic Backend"

# Install dependencies
pip install -r requirements.txt

# Start PostgreSQL (if not running)
docker-compose up -d postgres

# Start the FastAPI server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at:
- API: http://localhost:8000
- Documentation: http://localhost:8000/docs
- Health: http://localhost:8000/health

### Step 2: Start the React Frontend

```bash
# Navigate to frontend directory
cd "quantum-junction-gui-main"

# Install dependencies
npm install

# Copy environment file
copy .env.example .env

# Start the React app
npm start
```

The dashboard will be available at: http://localhost:3000

### Step 3: Send Simulation Data

Use the simulation server you created earlier or send test data:

```bash
# From your simulation directory
python fastapi_server.py  # Start the Redis sender
python send_to_server.py  # Start sending simulation data
```

## 📡 API Endpoints

### Real-time Data Endpoints

- **WebSocket**: `ws://localhost:8000/ws/updates`
  - Real-time simulation updates
  - Connection status notifications

- **GET** `/api/simulation/latest`
  - Get the most recent simulation data

- **GET** `/api/dashboard/intersection-status`
  - Optimized data for React components

### Analytics Endpoints

- **GET** `/api/v1/analytics/wait-times`
- **GET** `/api/v1/analytics/comparison/baseline-vs-ai`
- **GET** `/api/v1/analytics/environmental-impact`
- **GET** `/api/v1/charts/wait-time-trend`

### Data Ingestion

- **POST** `/api/v1/ingest/simulation`
  - Send simulation data to backend
  - Automatically broadcasts to WebSocket clients

## 🔄 Data Flow

### 1. Simulation → FastAPI

Your simulation sends JSON data to FastAPI:

```python
import requests

simulation_data = {
    "simulation_id": "SIM_001",
    "timestamp": "2023-12-01T10:00:00Z",
    "intersection_id": "INT_001",
    "current_phase": {
        "phase_id": 0,
        "active_directions": ["east", "west"],
        "status": "GREEN",
        "remaining_time": 5
    },
    "direction_metrics": {
        "east": {
            "vehicle_counts": {"car": 15, "bus": 2, "truck": 1, "bike": 3},
            "queue_length": 8,
            "vehicles_crossed": 12,
            "avg_wait_time": 18.5,
            "emergency_vehicle_present": false
        }
        # ... more directions
    },
    "overall_metrics": {
        "total_vehicles_passed": 45,
        "avg_wait_time_all_sides": 22.9,
        "throughput": 0.75,
        "avg_speed": 28.5,
        "cycle_time": 120
    }
}

response = requests.post("http://localhost:8000/api/v1/ingest/simulation", 
                        json={"data": simulation_data})
```

### 2. FastAPI → React (WebSocket)

FastAPI automatically broadcasts updates to connected React clients:

```typescript
// React automatically connects and receives updates
const { lanes, simulationData, isConnected } = useTrafficData();
```

### 3. React Dashboard Updates

The dashboard shows:
- **Real-time traffic light states**
- **Live vehicle counts and queue lengths**
- **Wait time analytics**
- **Performance comparisons**
- **Environmental impact metrics**

## 🎛️ React Components Integration

### TrafficDashboard Component

Now uses the `useTrafficData` hook for real backend data:

```typescript
const {
  lanes,              // Real-time lane data
  simulationData,     // Full simulation object
  isConnected,        // WebSocket status
  isLoading,          // Initial load state
  error,              // Connection errors
  lastUpdateTime,     // Last data update
  refreshData         // Manual refresh function
} = useTrafficData();
```

### Key Features

1. **Real-time Updates**: WebSocket connection for live data
2. **Fallback Handling**: Graceful degradation when backend is unavailable
3. **Error Notifications**: Toast notifications for connection issues
4. **Data Transformation**: Converts backend data to existing component format
5. **Connection Status**: Visual indicators for connection state

## 🔧 Configuration

### Backend Configuration

Edit `Traffic Backend/.env`:

```bash
# Database
DATABASE_URL=postgresql://traffic_user:traffic_pass@localhost:5432/traffic_simulation

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Redis (optional)
REDIS_URL=redis://localhost:6379/0
```

### Frontend Configuration

Edit `quantum-junction-gui-main/.env`:

```bash
REACT_APP_API_BASE_URL=http://localhost:8000
REACT_APP_WS_HOST=localhost:8000
REACT_APP_DEBUG=true
```

## 🧪 Testing the Integration

### 1. Health Check

```bash
curl http://localhost:8000/health
```

### 2. Send Test Data

```bash
curl -X POST "http://localhost:8000/api/v1/ingest/simulation" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "simulation_id": "TEST_001",
      "timestamp": "2023-12-01T10:00:00Z",
      "intersection_id": "INT_001",
      "current_phase": {
        "phase_id": 0,
        "active_directions": ["north"],
        "status": "GREEN",
        "remaining_time": 30
      },
      "direction_metrics": {
        "north": {
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
        "cycle_time": 90
      }
    }
  }'
```

### 3. Check WebSocket

Open browser dev tools → Network → WS to see WebSocket messages.

## 📊 Analytics Integration

The system provides rich analytics through the backend:

- **Wait Time Analysis**: Per-direction and overall averages
- **AI vs Baseline Comparison**: Performance improvements
- **Environmental Impact**: CO₂ and fuel savings
- **Emergency Handling**: Response time analytics
- **Throughput Metrics**: Vehicles per minute analysis

## 🚨 Troubleshooting

### Common Issues

1. **CORS Errors**
   - Ensure FastAPI CORS middleware is configured
   - Check frontend URL is allowed

2. **WebSocket Connection Failed**
   - Verify backend is running on port 8000
   - Check firewall settings
   - Confirm WebSocket endpoint path

3. **No Data Showing**
   - Check if simulation is sending data
   - Verify API endpoints are working
   - Check browser console for errors

4. **Database Connection Issues**
   - Ensure PostgreSQL is running
   - Check database credentials in `.env`
   - Run database migrations

### Debug Commands

```bash
# Check API health
curl http://localhost:8000/health

# Check latest data
curl http://localhost:8000/api/simulation/latest

# Check intersection status
curl http://localhost:8000/api/dashboard/intersection-status

# View backend logs
tail -f logs/traffic_api.log
```

## 🎯 Next Steps

1. **Deploy to Production**: Use Docker containers
2. **Add Authentication**: Secure the API endpoints
3. **Enhanced Analytics**: Add more complex metrics
4. **Mobile Support**: Responsive dashboard design
5. **Historical Data**: Long-term trend analysis

## 📞 Support

- Backend API docs: http://localhost:8000/docs
- React app: http://localhost:3000
- Check console logs for detailed error messages
- Verify all services are running with `curl` commands

---

🚦 **Your AI-powered traffic management system is now fully integrated!** 🚦