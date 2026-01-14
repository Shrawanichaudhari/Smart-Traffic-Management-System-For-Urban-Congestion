# Smart Traffic Signal Analytics API

🚦 A high-performance backend system for AI-powered traffic signal simulation analytics.

## 🌟 Features

- **Real-time Data Ingestion**: High-frequency simulation data processing
- **Advanced Analytics**: Comprehensive performance metrics and comparisons  
- **Baseline vs AI Comparison**: Statistical analysis of traffic improvements
- **Environmental Impact**: Fuel savings and CO2 reduction calculations
- **Emergency Vehicle Handling**: Priority override tracking and analysis
- **Time-series Analytics**: Chart-ready data for visualization
- **Production Ready**: Docker deployment with monitoring capabilities

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- Git

### 1. Clone and Setup

```bash
git clone <repository-url>
cd traffic-analytics-api
```

### 2. Environment Setup

```bash
# Create and activate virtual environment (if not already done)
python -m venv venv

# On Windows:
venv\Scripts\activate

# On Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Database Setup

```bash
# Start PostgreSQL with Docker
docker-compose up -d postgres

# Wait for database to be ready (check logs if needed)
docker-compose logs postgres

# The database is automatically initialized with schema and sample data
```

### 4. Start the API

```bash
# Start the FastAPI application
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# The API will be available at:
# - API: http://localhost:8000
# - Documentation: http://localhost:8000/docs  
# - Health Check: http://localhost:8000/health
```

### 5. Test the Setup

```bash
# Run the comprehensive test suite
python scripts/example_usage.py
```

## 📚 API Documentation

### Core Endpoints

#### Health & System
- `GET /health` - Health check endpoint
- `GET /system/info` - System information and database stats
- `GET /` - Root endpoint with API information

#### Data Ingestion
- `POST /api/v1/ingest/simulation` - Ingest single simulation data
- `POST /api/v1/ingest/batch` - Batch ingest multiple records

#### Analytics
- `GET /api/v1/analytics/wait-times` - Average wait time analysis
- `GET /api/v1/analytics/comparison/baseline-vs-ai` - Performance comparison
- `GET /api/v1/analytics/environmental-impact` - Fuel/CO2 savings
- `GET /api/v1/analytics/emergency-handling` - Emergency vehicle performance
- `GET /api/v1/analytics/time-series/{simulation_id}` - Time-series data

#### Dashboard
- `GET /api/v1/dashboard/live-metrics` - Real-time metrics
- `GET /api/v1/dashboard/performance-comparison` - Performance dashboard data

#### Charts & Visualization
- `GET /api/v1/charts/wait-time-trend` - Wait time trend data
- `GET /api/v1/charts/performance-scatter` - Performance scatter plot data

#### Simulation Management
- `GET /api/v1/simulations/{simulation_id}` - Get simulation summary

### Sample Data Format

```json
{
  "simulation_id": "SIM_001", 
  "timestamp": "2023-12-01T10:00:00Z",
  "intersection_id": "INT_001",
  "signals": [
    {
      "direction": "north",
      "vehicle_counts": {
        "car": 15,
        "bus": 2, 
        "truck": 1,
        "bike": 3,
        "rickshaw": 0
      },
      "emergency_vehicle_present": false,
      "signal_status": "GREEN",
      "signal_timer": 25,
      "vehicles_crossed": 12,
      "avg_wait_time": 18.5,
      "green_time_allocated": 45,
      "queue_length": 4
    }
  ],
  "metrics": {
    "total_vehicles_passed": 45,
    "avg_wait_time_all_sides": 22.9,
    "throughput": 0.75,
    "avg_speed": 28.5,
    "fuel_saved": 3.2,
    "co2_saved": 7.36,
    "emergency_overrides": 1,
    "cycle_time": 120
  }
}
```

## 🏗️ Architecture

### Technology Stack

- **FastAPI**: Modern, fast web framework for building APIs
- **PostgreSQL**: Robust relational database for time-series data
- **SQLAlchemy**: Powerful ORM with async support  
- **Docker**: Containerized deployment and development
- **Alembic**: Database migration management
- **Pydantic**: Data validation and serialization
- **Uvicorn**: ASGI server for production deployment

### Project Structure

```
traffic-analytics-api/
├── app/                     # Main application code
│   ├── __init__.py
│   ├── main.py             # FastAPI application entry point
│   ├── models.py           # SQLAlchemy ORM models
│   ├── database.py         # Database configuration
│   ├── ingestion.py        # Data ingestion service
│   └── analytics.py        # Analytics service
├── tests/                  # Test files
│   ├── test_api.py
│   ├── test_ingestion.py
│   └── test_analytics.py
├── scripts/                # Utility scripts
│   ├── init_db.py          # Database initialization
│   └── example_usage.py    # API testing examples
├── sql/                    # SQL scripts
│   ├── init-db.sql         # Database schema initialization
│   └── indexes.sql         # Performance optimization indexes
├── docker/                 # Docker files
│   └── Dockerfile          # Application container
├── config/                 # Configuration files  
├── alembic/               # Database migrations
├── docs/                  # Documentation
├── .env                   # Environment variables
├── .gitignore            # Git ignore rules
├── requirements.txt       # Python dependencies
├── docker-compose.yml     # Docker services
├── pytest.ini           # Test configuration
└── README.md             # This file
```

### Database Schema

The system uses PostgreSQL with the following key tables:

- **simulations**: Simulation run metadata
- **intersections**: Static intersection data
- **signals**: Signal configuration per intersection  
- **signal_states**: Time-series signal status data
- **traffic_data**: Vehicle counts and conditions (time-series)
- **performance_metrics**: Aggregated performance data
- **emergency_events**: Emergency vehicle handling logs

## 🔧 Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test types
pytest -m unit      # Unit tests only
pytest -m integration  # Integration tests only
```

### Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Downgrade migrations  
alembic downgrade -1
```

### Code Quality

```bash
# Format code with black
black app/ tests/ scripts/

# Lint code with flake8
flake8 app/ tests/ scripts/

# Type checking with mypy
mypy app/
```

## 🐳 Docker Deployment

### Development Environment

```bash
# Start all services
docker-compose up -d

# Start with monitoring (Prometheus + Grafana)
docker-compose --profile monitoring up -d

# Start with caching (Redis)
docker-compose --profile cache up -d
```

### Production Deployment

```bash
# Use production configuration
docker-compose -f docker-compose.prod.yml up -d

# Scale the API service
docker-compose up -d --scale api=3
```

## 📊 Monitoring

The system includes optional monitoring with:

- **Prometheus**: Metrics collection
- **Grafana**: Visualization dashboards
- **Health checks**: Built-in endpoint monitoring

Access monitoring at:
- Grafana: http://localhost:3000 (admin/admin123)
- Prometheus: http://localhost:9090

## 🔐 Security

- Environment variable based configuration
- Database connection pooling and security
- Input validation with Pydantic models
- CORS middleware for frontend integration

## 🌍 Environment Variables

Key environment variables (see `.env.example`):

```bash
# Database
DATABASE_URL=postgresql://traffic_user:traffic_pass@localhost:5432/traffic_simulation
POSTGRES_DB=traffic_simulation
POSTGRES_USER=traffic_user
POSTGRES_PASSWORD=traffic_pass

# API Configuration  
ENVIRONMENT=development
API_HOST=0.0.0.0
API_PORT=8000

# Optional Services
REDIS_URL=redis://localhost:6379/0
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
```

## 📈 Performance

The system is optimized for:

- **High-frequency data ingestion**: Batch processing and connection pooling
- **Time-series analytics**: Proper indexing and query optimization
- **Real-time responses**: Async processing and background tasks
- **Scalability**: Docker deployment with load balancing support

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:

1. Check the API documentation at `/docs`
2. Review the test examples in `scripts/example_usage.py`
3. Check container logs: `docker-compose logs [service]`
4. Verify database health: `python scripts/init_db.py`

## 🎯 API Usage Examples

### Health Check
```bash
curl http://localhost:8000/health
```

### Ingest Simulation Data
```bash
curl -X POST "http://localhost:8000/api/v1/ingest/simulation" \
  -H "Content-Type: application/json" \
  -d @sample_data.json
```

### Get Analytics
```bash
curl "http://localhost:8000/api/v1/analytics/wait-times?simulation_id=SIM_001"
```

### Performance Comparison
```bash
curl "http://localhost:8000/api/v1/analytics/comparison/baseline-vs-ai"
```

---

🚦 **Ready to optimize traffic flow with AI-powered analytics!** 🚦
