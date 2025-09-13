# ⚡ Real-time Data Fetching Configuration

## 🚀 **Current Setup**

Your dashboard now fetches data from the backend **every 2 seconds** for real-time updates.

### **📊 What Gets Fetched Every 2 Seconds:**

1. **Live Metrics** (`/api/v1/dashboard/live-metrics`)
   - Wait times
   - Vehicle speeds  
   - Environmental impact data
   - Throughput metrics

2. **Signal Timings** (`/api/v1/signals/timings`)
   - Current signal states (Red/Yellow/Green)
   - Time remaining for each signal
   - Vehicle counts per lane
   - Signal cycle information

### **🔄 Data Flow:**

```
Every 2 seconds:
├── TrafficDashboard.fetchRealTimeData()
├── → trafficApi.getLiveMetrics()
├── → trafficApi.getSignalTimings("INT_001")
├── → Update lane states, colors, timings
├── → Update metrics and analytics
└── → Refresh UI components
```

### **📱 Components Updated:**

✅ **TrafficDashboard**: Main intersection view with 2s updates  
✅ **AnalyticsDashboard**: Performance metrics with 2s updates  
✅ **IntersectionView**: Signal lights update in real-time  
✅ **LaneControl**: Timer countdowns update every 2s  

### **⚙️ Technical Details:**

- **Fetch Interval**: 2000ms (2 seconds)
- **Error Handling**: Graceful fallback on connection issues
- **Connection Status**: Live indicator (Green/Red/Yellow)
- **Last Updated**: Timestamp shows exact update time
- **Simulation Fallback**: Mock data when backend unavailable

### **🎯 Backend Endpoints Used:**

```http
GET /health                           # Health check
GET /api/v1/dashboard/live-metrics    # Main metrics
GET /api/v1/signals/timings           # Signal states
POST /api/v1/signals/manual-override  # Manual control
POST /api/v1/signals/emergency-override # Emergency
POST /api/v1/signals/reset-ai         # Return to AI
```

### **🔧 Performance Optimization:**

- **Parallel Requests**: Metrics and signals fetched simultaneously
- **Error Isolation**: Signal timing errors don't break metrics
- **Connection Status**: Clear feedback for users
- **Efficient Updates**: Only changed data triggers re-renders

### **💡 User Experience:**

- **Real-time Signal Changes**: See lights change every 2 seconds
- **Live Timer Countdowns**: Accurate countdown displays  
- **Instant Manual Override**: Immediate feedback on controls
- **Connection Indicators**: Always know data freshness
- **Smooth Animations**: No jarring updates

## ✅ **Ready for Production!**

Your dashboard now provides true real-time traffic signal monitoring and control with 2-second data refresh rates.

**Test it:** Start backend → Start frontend → Watch live updates! 🚀