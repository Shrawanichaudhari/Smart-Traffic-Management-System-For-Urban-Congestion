# 🚦 Smart Traffic Management System

An AI-powered traffic signal control and analytics platform featuring real-time simulation, intelligent vehicle detection, interactive dashboard, and comprehensive performance analytics.

## 🌟 Overview

This project implements a complete smart traffic management ecosystem with the following components:

- **AI Traffic Simulator**: Pygame-based traffic intersection simulation with YOLOv8 vehicle detection
- **Real-time Dashboard**: React/TypeScript frontend for live traffic monitoring
- **Analytics Backend**: FastAPI-powered data ingestion and performance analytics
- **Integration Layer**: WebSocket communication for real-time data flow

The system simulates traffic flow at intersections, uses AI to detect and count vehicles, optimizes signal timing, and provides real-time analytics on traffic efficiency, environmental impact, and emergency vehicle handling.

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Video Input   │───▶│ AI Detection    │───▶│ FastAPI Backend │───▶│ React Dashboard │
│   (Cameras)     │    │ (YOLOv8)        │    │                 │    │                 │
│                 │    │                 │    │ - Data Ingestion│    │ - Real-time UI  │
│ - Traffic       │    │ - Vehicle       │    │ - Analytics     │    │ - Charts        │
│   Videos        │    │   Counting      │    │ - WebSocket     │    │ - Metrics       │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
                                                            │
                                                            ▼
                                               ┌─────────────────┐
                                               │ PostgreSQL DB   │
                                               │                 │
                                               │ - Time-series   │
                                               │ - Analytics     │
                                               │ - Performance   │
                                               └─────────────────┘
```

## ✨ Features

### AI Traffic Simulator
- **Real-time Vehicle Detection**: YOLOv8-powered object detection for cars, buses, trucks, bikes
- **Traffic Signal Simulation**: Dynamic signal timing based on vehicle counts and AI optimization
- **Emergency Vehicle Priority**: Automatic green light for ambulances and priority vehicles
- **Performance Metrics**: Throughput, wait times, queue lengths, fuel consumption
- **Visual Simulation**: Pygame-based graphical interface with realistic traffic flow

### Real-time Dashboard
- **Live Traffic Monitoring**: Real-time vehicle counts and signal states
- **Interactive Charts**: Wait time trends, performance comparisons, environmental impact
- **Signal Control Interface**: Manual override capabilities for traffic operators
- **Responsive Design**: Modern UI built with React, TypeScript, and Tailwind CSS
- **WebSocket Integration**: Instant updates without page refresh

### Analytics Backend
- **High-performance Data Ingestion**: RESTful APIs for simulation data processing
- **Advanced Analytics**: AI vs baseline performance comparisons, environmental impact calculations
- **Time-series Analysis**: Historical data analysis and trend visualization
- **Production Ready**: Docker deployment, database migrations, comprehensive testing
- **Real-time Communication**: WebSocket server for live dashboard updates

## 📋 Prerequisites

- **Python 3.11+** (for simulator and backend)
- **Node.js 16+** and npm/yarn (for frontend)
- **PostgreSQL** (for analytics database)
- **Redis** (optional, for caching)
- **Docker & Docker Compose** (for containerized deployment)

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd smart-traffic-management-system
```

### 2. Start the Analytics Backend

```bash
# Navigate to backend directory
cd "SIH Dashboard/Traffic Backend"

# Install Python dependencies
pip install -r requirements.txt

# Start PostgreSQL database
docker-compose up -d postgres

# Run database migrations
alembic upgrade head

# Start FastAPI server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Backend URLs:**
- API: http://localhost:8000
- Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

### 3. Start the React Dashboard

```bash
# Navigate to frontend directory
cd "SIH Dashboard/quantum-junction-gui-main"

# Install Node.js dependencies
npm install

# Start development server
npm run dev
```

**Dashboard URL:** http://localhost:5173

### 4. Run the AI Traffic Simulator

```bash
# Navigate to simulator directory
cd "Main_Traffic_AI_Simulator - 2.0"

# Install Python dependencies
pip install -r requirements.txt

# Run the simulation
python simulation.py
```

## 📖 Usage

### Running a Complete Simulation

1. **Start Backend**: Ensure FastAPI server is running on port 8000
2. **Start Dashboard**: Open React app in browser
3. **Configure Simulator**: Edit `configs/config.yaml` for simulation parameters
4. **Run Simulation**: Execute `python simulation.py` to start traffic simulation
5. **Monitor Results**: View real-time data in the dashboard and API endpoints

### Processing Video Files

```bash
# Process traffic videos with AI detection
python scripts/process_videos_ultralytics.py --input input_videos/test1.mp4 --output output/
```

### API Integration

Send simulation data to backend:

```python
import requests

data = {
    "simulation_id": "SIM_001",
    "timestamp": "2023-12-01T10:00:00Z",
    "intersection_id": "INT_001",
    "signals": [...],  # Signal states and vehicle counts
    "metrics": {...}   # Performance metrics
}

response = requests.post("http://localhost:8000/api/v1/ingest/simulation", json=data)
```

## 📊 API Endpoints

### Core Endpoints
- `GET /health` - System health check
- `POST /api/v1/ingest/simulation` - Ingest simulation data
- `GET /api/v1/analytics/wait-times` - Wait time analytics
- `GET /api/v1/analytics/comparison/baseline-vs-ai` - Performance comparison
- `GET /api/v1/dashboard/live-metrics` - Dashboard data

### WebSocket
- `ws://localhost:8000/ws/updates` - Real-time data streaming

### Documentation
- Interactive API docs: http://localhost:8000/docs
- OpenAPI schema: http://localhost:8000/openapi.json

## 🧪 Testing

### Backend Tests
```bash
cd "SIH Dashboard/Traffic Backend"
pytest
```

### Integration Tests
```bash
cd "SIH Dashboard/SIH-Dashboard"
python test_data_sender.py
```

### Simulator Tests
```bash
cd "Main_Traffic_AI_Simulator - 2.0"
python extra_codes/quick_test.py
```

## 🐳 Docker Deployment

### Full System Deployment
```bash
# From project root
docker-compose up -d
```

### Individual Services
```bash
# Backend only
cd "SIH Dashboard/Traffic Backend"
docker-compose up -d

# Database only
docker-compose up -d postgres
```

## 🔧 Configuration

### Environment Variables

Create `.env` files in respective directories:

**Backend (.env):**
```bash
DATABASE_URL=postgresql://traffic_user:traffic_pass@localhost:5432/traffic_simulation
API_HOST=0.0.0.0
API_PORT=8000
REDIS_URL=redis://localhost:6379/0
```

**Frontend (.env):**
```bash
REACT_APP_API_BASE_URL=http://localhost:8000
REACT_APP_WS_HOST=localhost:8000
```

### Simulation Configuration

Edit `Main_Traffic_AI_Simulator - 2.0/configs/config.yaml`:
```yaml
simulation:
  duration: 3600  # seconds
  fps: 30
  intersection_size: 400

ai_config:
  model: yolov8n.pt
  confidence_threshold: 0.5
  emergency_detection: true
```

## 📈 Performance Metrics

The system tracks:
- **Traffic Efficiency**: Average wait times, throughput, queue lengths
- **Environmental Impact**: Fuel consumption, CO2 emissions
- **Emergency Response**: Priority vehicle handling times
- **AI Optimization**: Performance improvements over baseline timing

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 for Python code
- Use TypeScript for React components
- Add tests for new features
- Update documentation

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: Check individual component READMEs
- **API Docs**: http://localhost:8000/docs
- **Issues**: Create GitHub issues for bugs/features
- **Discussions**: Use GitHub Discussions for questions

## 🎯 Roadmap

- [ ] Multi-intersection coordination
- [ ] Mobile dashboard app
- [ ] Advanced AI algorithms (reinforcement learning)
- [ ] Historical data analytics dashboard
- [ ] Integration with real traffic cameras
- [ ] Predictive traffic modeling

---

🚦 **Optimizing traffic flow with AI-powered intelligence!** 🚦

Built for Smart India Hackathon (SIH) - Transforming urban mobility through intelligent traffic management.
