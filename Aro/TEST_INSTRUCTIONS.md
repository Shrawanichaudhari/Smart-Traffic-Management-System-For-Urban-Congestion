# 🧪 Real-time Data Testing Guide

## 🎯 **What This Test Does**

The test simulator mimics a real ML model by:
- **Generating AI decisions** for traffic signal optimization
- **Calculating metrics** (wait times, speeds, environmental impact)
- **Posting data to backend** every 2 seconds
- **Simulating realistic traffic flow** with vehicle counts and speeds

## 🚀 **How to Test**

### **Step 1: Start Backend** (Terminal 1)
```bash
cd "D:\Projects\SIH Dashboard\Traffic Backend"
python fastapi_main.py
```

### **Step 2: Start Frontend** (Terminal 2)
```bash
cd "D:\Projects\SIH Dashboard\quantum-junction-gui-main"
npm run dev
```

### **Step 3: Run Test Simulator** (Terminal 3)
```bash
cd "D:\Projects\SIH Dashboard\Traffic Backend"

# Option 1: Use batch file (Windows)
run_test_simulator.bat

# Option 2: Run directly
python test_realtime_data.py
```

### **Step 4: Watch Live Updates**
Open your browser to: **http://localhost:5173**

---

## 📊 **What You'll See**

### **In the Dashboard:**
✅ **Signal lights** changing every few seconds  
✅ **Timer countdowns** updating in real-time  
✅ **Vehicle counts** fluctuating dynamically  
✅ **Metrics updates** every 2 seconds  
✅ **Environmental data** calculating live savings  

### **In the Test Simulator Console:**
```
🔄 Cycle 15 - 14:30:25
🤖 AI Decision: Priority given to east direction
📊 Total Vehicles: 44
🚦 Signal States:
   n-straight: 🔴 (23s, 8 cars)
   s-straight: 🔴 (18s, 12 cars) 
   e-straight: 🟢 (45s, 15 cars)
   w-straight: 🔴 (31s, 9 cars)
📡 Posted to 3/3 endpoints successfully
```

### **Live Data Flow:**
1. **AI makes decision** based on vehicle counts
2. **Signals change** to optimize traffic flow
3. **Data posts to backend** via 3 endpoints
4. **Frontend fetches** updated data every 2s
5. **Dashboard updates** all components live

---

## 🔧 **Simulated ML Model Features**

### **AI Logic:**
- **Priority Algorithm**: Gives green light to direction with most vehicles
- **Dynamic Timing**: Adjusts signal duration based on traffic density
- **Confidence Scoring**: Simulates ML confidence levels (85-98%)
- **Processing Time**: Realistic AI response times (8-15ms)

### **Traffic Simulation:**
- **Vehicle Flow**: Realistic accumulation and clearing patterns
- **Speed Calculation**: Speed varies based on congestion
- **Queue Management**: Queue lengths grow and shrink naturally
- **Environmental Impact**: CO₂ and fuel savings calculations

### **Data Generation:**
- **Live Metrics**: Real-time dashboard data
- **Signal Timings**: Exact timing for each lane
- **Simulation Data**: Complete cycle information for analysis

---

## 🎮 **Testing Scenarios**

### **1. Normal Operation**
- Watch signals change automatically
- See vehicle counts fluctuate
- Monitor environmental savings

### **2. Manual Override**
- Click signal buttons in dashboard
- See if manual changes take effect
- Test return to AI mode

### **3. Emergency Mode**
- Test emergency override functionality
- Watch all signals turn red except priority lane

### **4. Connection Issues**
- Stop the simulator
- See how dashboard handles lost connection
- Restart to see recovery

---

## ✅ **Success Indicators**

**🟢 Working Correctly:**
- Signal lights change dynamically
- Timers count down accurately  
- Vehicle counts update live
- Metrics refresh every 2 seconds
- Console shows successful posts
- No error messages in browser

**🔴 Issues to Check:**
- Static signals (not changing)
- Connection error indicators
- Failed API posts in console
- Frontend showing stale data

---

## 🛑 **Stopping the Test**

Press **Ctrl+C** in the simulator terminal to stop the test.

The simulator will clean up and stop posting data to your backend.

---

## 💡 **Next Steps**

Once testing is successful:
1. **Replace simulator** with your real ML model
2. **Use same data format** that the simulator generates
3. **Post to same endpoints** for seamless integration
4. **Keep 2-second update interval** for real-time experience

**Your dashboard is ready for real ML integration! 🚀**