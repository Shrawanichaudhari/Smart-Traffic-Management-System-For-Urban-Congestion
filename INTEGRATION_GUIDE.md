# SIH Dashboard - Frontend & Backend Integration

This is a working integration of the Traffic Analytics Frontend and Backend.

## Quick Start

### Prerequisites
- **Python 3.8+** installed
- **Node.js 16+** installed

### Running the Application

1. **Start Backend** (Terminal 1):
   ```bash
   cd "Traffic Backend"
   
   # Option 1: Use the batch script (Windows)
   start_backend.bat
   
   # Option 2: Manual start
   pip install fastapi uvicorn
   python simple_main.py
   ```

2. **Start Frontend** (Terminal 2):
   ```bash
   cd quantum-junction-gui-main
   
   # Option 1: Use the batch script (Windows)
   start_frontend.bat
   
   # Option 2: Manual start
   npm install
   npm run dev
   ```

3. **Access the Application**:
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## What's Working

✅ **Health Checks**: Backend health endpoint  
✅ **Live Metrics**: Real-time traffic data display  
✅ **Performance Comparison**: AI vs Baseline comparison  
✅ **Analytics**: Wait times, speeds, environmental impact  
✅ **Charts**: Wait time trends and performance data  
✅ **CORS**: Properly configured for local development  

## API Endpoints Available

- `GET /health` - Backend health status
- `GET /api/v1/dashboard/live-metrics` - Main dashboard data
- `GET /api/v1/dashboard/performance-comparison` - Performance metrics
- `GET /api/v1/analytics/wait-times` - Wait time analytics
- `GET /api/v1/analytics/speeds` - Speed analytics
- `GET /api/v1/analytics/environmental-impact` - Environmental data
- `GET /api/v1/charts/wait-time-trend` - Chart data for trends
- `POST /api/v1/ingest/simulation` - Data ingestion

## Data Flow

1. Frontend makes API calls to `http://localhost:8000`
2. Backend generates realistic mock data with random values
3. Data updates every 5 seconds automatically
4. All charts and metrics display live data

## Configuration

- **Backend Port**: 8000 (configurable in `simple_main.py`)
- **Frontend Port**: 5173 (Vite default)
- **CORS**: Configured for local development
- **Environment**: Check `.env` file in frontend for API URL

## Troubleshooting

**Backend Issues**:
- Make sure Python is installed: `python --version`
- Install dependencies: `pip install fastapi uvicorn`
- Check port 8000 is not in use

**Frontend Issues**:
- Make sure Node.js is installed: `node --version`
- Install dependencies: `npm install`
- Check port 5173 is available
- Clear browser cache if needed

**Connection Issues**:
- Ensure backend is running first
- Check CORS configuration in `simple_main.py`
- Verify API URL in `.env` file

## Next Steps

This basic integration provides:
- Mock data for all dashboard components
- Working API endpoints
- Real-time updates
- Chart data visualization

To enhance further, you could:
- Add real database integration
- Implement WebSocket connections
- Add user authentication
- Connect to actual traffic simulation data