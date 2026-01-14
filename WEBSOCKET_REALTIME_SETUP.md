# 🚦 Real-Time Traffic Dashboard with WebSocket

A high-performance WebSocket-based real-time traffic management system that streams live intersection data every second and supports manual traffic signal overrides.

## 🎯 Features

- ⚡ **Real-time Updates**: Live traffic data streaming every 1 second
- 🔄 **WebSocket Communication**: Bidirectional communication for instant updates
- 🎛️ **Manual Override**: Remote traffic signal control via WebSocket
- 📊 **Live Metrics**: Real-time wait times, speeds, and environmental impact
- 🚨 **Emergency Mode**: Priority lane clearing for emergency vehicles
- 🔌 **Auto-Reconnection**: Automatic reconnection with exponential backoff
- 📈 **Performance Analytics**: Live performance comparison and optimization

## 🏗️ Architecture

```
┌─────────────────┐    WebSocket     ┌──────────────────┐
│   React Frontend │ ◄──────────────► │   FastAPI Backend │
│                 │   ws://8001/ws   │                  │  
│ - Dashboard     │                  │ - Traffic Engine │
│ - Controls      │                  │ - AI Controller  │
│ - Analytics     │                  │ - Data Stream    │
└─────────────────┘                  └──────────────────┘
```

## 📁 File Structure

```
SIH Dashboard/
├── Traffic Backend/
│   ├── websocket_backend.py           # WebSocket server
│   └── start_websocket_server.py      # Server startup script
└── Traffic Frontend/
    └── src/
        ├── hooks/
        │   └── useWebSocketTraffic.ts  # WebSocket React hook
        └── components/
            └── TrafficDashboardWebSocket.tsx  # Updated dashboard
```

## 🚀 Quick Start

### Backend Setup

1. **Navigate to backend directory**:
   ```bash
   cd "D:\Projects\SIH Dashboard\Traffic Backend"
   ```

2. **Install dependencies**:
   ```bash
   pip install fastapi uvicorn websockets
   ```

3. **Start the WebSocket server**:
   ```bash
   python start_websocket_server.py
   ```

   Or manually:
   ```bash
   python -m uvicorn websocket_backend:app --host 0.0.0.0 --port 8001 --reload
   ```

4. **Verify server is running**:
   - WebSocket endpoint: `ws://localhost:8001/ws/traffic`
   - Health check: `http://localhost:8001/health`
   - API docs: `http://localhost:8001/docs`

### Frontend Setup

1. **Navigate to frontend directory**:
   ```bash
   cd "D:\Projects\SIH Dashboard\Traffic Frontend"
   ```

2. **Install the WebSocket hook** (already created):
   - File: `src/hooks/useWebSocketTraffic.ts`

3. **Update your main component** to use the WebSocket version:
   ```tsx
   // In your main App.tsx or Index.tsx, replace:
   import { TrafficDashboard } from "./components/TrafficDashboard";
   
   // With:
   import { TrafficDashboard } from "./components/TrafficDashboardWebSocket";
   ```

4. **Start the React development server**:
   ```bash
   npm run dev
   # or
   yarn dev
   ```

## 🔧 Configuration

### WebSocket Backend Configuration

Edit `websocket_backend.py` to customize:

```python
# Update interval (currently 1 second)
await asyncio.sleep(1)  # Line 282

# Port configuration
uvicorn.run(app, host="0.0.0.0", port=8001, reload=True)  # Line 301

# CORS origins (currently allows all)
allow_origins=["*"]  # Line 19 - Change to specific domains for production
```

### Frontend Configuration

Edit `useWebSocketTraffic.ts` to customize:

```typescript
const {
  websocketUrl = 'ws://localhost:8001/ws/traffic',  // WebSocket URL
  reconnectAttempts = 5,                            // Retry attempts
  reconnectInterval = 3000,                         // Retry delay (ms)  
  debug = false,                                    // Debug logging
} = options;
```

## 📡 WebSocket API

### Connection
```javascript
const ws = new WebSocket('ws://localhost:8001/ws/traffic');
```

### Incoming Messages

**Traffic Update**:
```json
{
  "type": "traffic_update",
  "timestamp": "2024-01-15T10:30:00",
  "intersection_id": "INT_001",
  "signals": [
    {
      "lane_id": "n-straight",
      "direction": "north",
      "type": "straight",
      "current_light": "green",
      "time_remaining": 25,
      "max_time": 45,
      "vehicle_count": 8,
      "avg_speed": 32.1,
      "queue_length": 2
    }
  ],
  "live_metrics": {
    "wait_times": {
      "overall_avg_wait_time": 23.5,
      "best_performance": 15,
      "worst_performance": 45
    },
    "speeds": {
      "overall_avg_speed": 28.7
    },
    "environmental_impact": {
      "total_fuel_saved": 12.3,
      "total_co2_saved": 28.29
    }
  }
}
```

### Outgoing Messages

**Manual Override**:
```json
{
  "type": "manual_override",
  "lane_id": "n-straight",
  "signal_state": "green"
}
```

**Override Confirmation**:
```json
{
  "type": "override_confirmation",
  "lane_id": "n-straight", 
  "signal_state": "green",
  "success": true
}
```

## 🎛️ Manual Controls

### Using the Dashboard
1. Click any traffic light in the intersection view
2. Select the desired signal state (red/yellow/green)  
3. The system automatically switches to manual mode
4. Changes are sent via WebSocket and applied instantly

### Programmatic Control
```typescript
// Send manual override
sendManualOverride('n-straight', 'green');

// Emergency override (clears a specific lane)
sendManualOverride('emergency-lane', 'green');
```

## 📊 Live Metrics

The system provides real-time analytics:

- **Wait Times**: Average, best, and worst performance across intersections
- **Speed Analysis**: Traffic flow speeds and throughput metrics  
- **Environmental Impact**: Real-time fuel and CO₂ savings calculations
- **Lane Efficiency**: Per-lane performance indicators
- **System Health**: Connection status, response times, sensor accuracy

## 🚨 Emergency Mode

Emergency mode can be activated to:
1. Clear a specific traffic lane for emergency vehicles
2. Override all other signals to red
3. Maintain priority until manually reset
4. Log all emergency activations for compliance

## 🔍 Debugging & Monitoring

### Backend Logs
```bash
# View server logs
python start_websocket_server.py
# Look for:
# ✅ Client connected. Total connections: 1
# 🔄 Manual override: n-straight -> green
```

### Frontend Debug Mode  
```typescript
// Enable in useWebSocketTraffic hook
const { trafficData, connectionStatus } = useWebSocketTraffic({
  debug: true  // Enables console logging
});
```

### Health Check
```bash
# Check server health
curl http://localhost:8001/health

# Response:
{
  "status": "healthy",
  "active_connections": 1,
  "timestamp": "2024-01-15T10:30:00"
}
```

## 🔒 Production Considerations

### Security
- Update CORS origins to specific domains
- Implement authentication for WebSocket connections
- Add rate limiting for manual overrides
- Enable HTTPS/WSS for production

### Performance  
- Consider Redis for scaling to multiple intersections
- Implement message queuing for high-traffic scenarios
- Add database persistence for historical data
- Set up load balancing for multiple backend instances

### Monitoring
- Add Prometheus metrics collection
- Set up alerts for connection failures
- Implement logging aggregation (ELK stack)
- Monitor WebSocket connection counts and performance

## 🐛 Troubleshooting

### Common Issues

**"Connection refused" error**:
- Ensure backend server is running on port 8001
- Check firewall settings
- Verify WebSocket URL in frontend configuration

**"WebSocket closed unexpectedly"**:  
- Check server logs for errors
- Verify network connectivity
- Enable debug mode to see detailed connection info

**Frontend not updating**:
- Check browser console for WebSocket errors
- Verify data structure matches expected format
- Ensure React components are re-rendering on state changes

**Manual override not working**:
- Check WebSocket connection status  
- Verify message format matches expected JSON structure
- Look for backend confirmation messages

### Debug Commands

```bash
# Test WebSocket connection manually
wscat -c ws://localhost:8001/ws/traffic

# Send test manual override
echo '{"type":"manual_override","lane_id":"n-straight","signal_state":"green"}' | wscat -c ws://localhost:8001/ws/traffic

# Check server processes
netstat -tlnp | grep :8001
```

## 🚀 Next Steps

1. **Database Integration**: Connect to your existing traffic database
2. **Multi-Intersection**: Scale to handle multiple intersections
3. **Historical Data**: Add data persistence and historical analytics  
4. **Mobile App**: Extend WebSocket support to mobile applications
5. **AI Enhancement**: Integrate with machine learning traffic prediction models

## 📞 Support

For issues or questions:
- Check the troubleshooting section above
- Review server and browser console logs  
- Verify all dependencies are properly installed
- Test with the provided debug tools

---

🎉 **You're now ready to run real-time traffic management with WebSocket connectivity!**