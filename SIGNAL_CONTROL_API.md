# 🚦 Signal Control API Integration Guide

## **4-Way Intersection Structure**

Your dashboard manages a **4-way intersection** with:
- **Directions**: North, South, East, West
- **Lane Types**: Straight, Left, Right  
- **Signals**: Red, Yellow, Green
- **Lane IDs**: `n-straight`, `s-straight`, `e-straight`, `w-straight`, etc.

---

## **📤 Frontend → Backend (Signal Control)**

### **1. Manual Signal Override**
**When user clicks Red/Yellow/Green in dashboard:**
```http
POST http://localhost:8000/api/v1/signals/manual-override
Content-Type: application/json

{
  "lane_id": "n-straight",
  "signal_state": "green",
  "duration": 30
}
```

### **2. Emergency Override**
**When emergency vehicle detected:**
```http
POST http://localhost:8000/api/v1/signals/emergency-override
Content-Type: application/json

{
  "lane_id": "n-straight", 
  "duration": 60
}
```

### **3. Reset to AI Control**
**When returning to AI mode:**
```http
POST http://localhost:8000/api/v1/signals/reset-ai
Content-Type: application/json

{
  "intersection_id": "INT_001"
}
```

### **4. Get Signal Timings**
**Fetch current signal state:**
```http
GET http://localhost:8000/api/v1/signals/timings?intersection_id=INT_001
```

---

## **📥 Backend → Frontend (Real-time Updates)**

### **Signal Status Polling (Every 1-2 seconds)**
**Your backend should POST to:**
```http
POST http://localhost:3000/api/signals/update
Content-Type: application/json

{
  "intersection_id": "INT_001",
  "signals": [
    {
      "lane_id": "n-straight",
      "direction": "north",
      "type": "straight", 
      "current_light": "green",
      "time_remaining": 25,
      "max_time": 30,
      "vehicle_count": 8
    },
    {
      "lane_id": "s-straight",
      "direction": "south", 
      "type": "straight",
      "current_light": "red",
      "time_remaining": 35,
      "max_time": 45,
      "vehicle_count": 12
    },
    {
      "lane_id": "e-straight",
      "direction": "east",
      "type": "straight", 
      "current_light": "red",
      "time_remaining": 15,
      "max_time": 45,
      "vehicle_count": 15
    },
    {
      "lane_id": "w-straight",
      "direction": "west",
      "type": "straight",
      "current_light": "red", 
      "time_remaining": 20,
      "max_time": 45,
      "vehicle_count": 9
    }
  ],
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## **🔄 Current Data Flow**

### **Dashboard → Backend**
1. **User clicks signal button** → `handleManualOverride()` 
2. **Calls** → `trafficApi.updateSignalTiming()`
3. **Posts to** → `/api/v1/signals/manual-override`
4. **Updates local state** → Lane colors change

### **Backend → Dashboard** 
1. **Backend calculates new timings** (every 1-2 seconds)
2. **Posts update to** → `http://localhost:3000/api/signals/update`
3. **Dashboard receives** → Signal states update automatically
4. **UI reflects** → New colors, timings, vehicle counts

---

## **🛠️ Backend Implementation Needed**

Add these endpoints to your FastAPI backend:

```python
@app.post("/api/v1/signals/manual-override")
async def manual_signal_override(request: dict):
    lane_id = request["lane_id"]
    signal_state = request["signal_state"] 
    duration = request["duration"]
    
    # Update your signal control system
    # Return success response
    
@app.post("/api/v1/signals/emergency-override") 
async def emergency_override(request: dict):
    lane_id = request["lane_id"]
    duration = request["duration"]
    
    # Clear emergency route
    # Set specified lane to green, others to red
    
@app.post("/api/v1/signals/reset-ai")
async def reset_to_ai(request: dict):
    intersection_id = request["intersection_id"]
    
    # Return control to AI system
    
@app.get("/api/v1/signals/timings")
async def get_signal_timings(intersection_id: str = None):
    # Return current signal states and timings
```

---

## **🎯 Key Integration Points**

✅ **Frontend Ready**: All signal controls call backend endpoints
✅ **API Endpoints**: Complete set of control APIs defined  
✅ **Data Structure**: Matches your intersection layout
✅ **Error Handling**: Graceful fallback on API failures
✅ **Real-time Updates**: 1-2 second polling supported

**Next Steps:**
1. Implement the 4 backend endpoints above
2. Set up polling from backend to frontend
3. Test signal control workflow end-to-end

**Your dashboard is now fully integrated for real-time signal control! 🚀**