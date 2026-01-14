# Smart Traffic Signal Analytics Backend - Deployment Guide

## 🏗️ Architecture Overview

This backend system provides a complete solution for ingesting, storing, and analyzing AI-powered traffic signal simulation data. The architecture includes:

- **PostgreSQL Database**: Optimized schema for time-series traffic data
- **FastAPI Backend**: High-performance REST API with async capabilities
- **SQLAlchemy ORM**: Database abstraction with connection pooling
- **Analytics Engine**: Comprehensive metrics and comparison capabilities
- **Docker Support**: Complete containerized deployment

## 🚀 Quick Start

### 1. Prerequisites

```bash
# Python 3.8+ required
python --version

# Docker and Docker Compose (optional)
docker --version
docker-compose --version

# PostgreSQL (if not using Docker)
psql --version
```

### 2. Environment Setup

```bash
# Clone or create project directory
mkdir traffic-analytics-api
cd traffic-analytics-api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Database Configuration

Create a `.env` file:

```env
# Database Configuration
DATABASE_URL=postgresql://traffic_user:traffic_pass@localhost:5432/traffic_simulation

# API Configuration
ENVIRONMENT=development
LOG_LEVEL=INFO

# Optional: Redis for caching
REDIS_URL=redis://localhost:6379/0
```

### 4. Database Setup

#### Option A: Using Docker Compose (Recommended)

```bash
# Start all services
docker-compose up -d postgres

# Wait for PostgreSQL to be ready
docker-compose logs -f postgres

# Initialize database schema
python -c "from database import db_manager; db_manager.create_tables()"
```

#### Option B: Manual PostgreSQL Setup

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database and user
CREATE DATABASE traffic_simulation;
CREATE USER traffic_user WITH PASSWORD 'traffic_pass';
GRANT ALL PRIVILEGES ON DATABASE traffic_simulation TO traffic_user;

# Exit and run schema creation
python -c "from database import db_manager; db_manager.create_tables()"
```

### 5. Start the API Server

```bash
# Development mode
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Production mode
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### 6. Test the System

```bash
# Run the test suite
python example_usage.py

# Check health endpoint
curl http://localhost:8000/health

# View API documentation
# Open browser to: http://localhost:8000/docs
```

## 🐳 Docker Deployment

### Development Environment

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f api

# Scale API instances
docker-compose up -d --scale api=3
```

### Production Environment

```bash
# Use production profile
docker-compose --profile production up -d

# With monitoring
docker-compose --profile production --profile monitoring up -d
```

## 📊 API Endpoints Overview

### Data Ingestion
- `POST /api/v1/ingest/simulation` - Ingest single simulation data
- `POST /api/v1/ingest/batch` - Batch ingest multiple data points

### Analytics
- `GET /api/v1/analytics/simulation/{id}/summary` - Simulation summary
- `GET /api/v1/analytics/wait-times` - Average wait time analytics
- `GET /api/v1/analytics/speeds` - Average speed metrics  
- `GET /api/v1/analytics/environmental-impact` - Fuel/CO2 savings
- `GET /api/v1/analytics/comparison/baseline-vs-ai` - Performance comparison
- `GET /api/v1/analytics/emergency-report` - Emergency handling metrics
- `GET /api/v1/analytics/time-series/{id}` - Time-series data for charts

### Dashboard
- `GET /api/v1/dashboard/live-metrics` - Real-time dashboard data
- `GET /api/v1/dashboard/performance-comparison` - Comparison dashboard
- `GET /api/v1/charts/wait-time-trend` - Chart-ready wait time data
- `GET /api/v1/charts/performance-scatter` - Scatter plot data

### System
- `GET /health` - Health check
- `GET /system/info` - System information
- `POST /api/v1/admin/clear-cache` - Clear internal caches

## 📈 Sample Data Format

### Input JSON Structure
```json
{
  "simulation_id": "SIM_20250910_001",
  "timestamp": "2025-09-10T23:20:00Z",
  "intersection_id": "INT_001",
  "signals": [
    {
      "direction": "north",
      "vehicle_counts": {
        "car": 78, "bus": 0, "truck": 0, "bike": 0, "rickshaw": 0
      },
      "emergency_vehicle_present": false,
      "signal_status": "GREEN",
      "signal_timer": 18,
      "vehicles_crossed": 35,
      "avg_wait_time": 12.5,
      "green_time_allocated": 20
    }
  ],
  "metrics": {
    "total_vehicles_passed": 104,
    "avg_wait_time_all_sides": 20.6,
    "throughput": 0.87,
    "avg_speed": 28.3,
    "fuel_saved": 1.2,
    "co2_saved": 3.8,
    "emergency_overrides": 0
  }
}
```

## 🔧 Performance Optimization

### Database Optimizations

1. **Indexing Strategy**
```sql
-- Time-series optimized indexes
CREATE INDEX idx_signal_states_simulation_timestamp 
ON signal_states(simulation_id, timestamp);

CREATE INDEX idx_traffic_data_signal_timestamp 
ON traffic_data(signal_id, timestamp);

-- JSONB index for vehicle counts
CREATE INDEX idx_traffic_data_vehicle_counts 
ON traffic_data USING GIN (vehicle_counts);
```

2. **Connection Pooling**
```python
# Already configured in database.py
engine = create_engine(
    DATABASE_URL,
    pool_size=20,        # Increased for high-frequency inserts
    max_overflow=30,     # Handle traffic spikes
    pool_pre_ping=True,  # Connection health checks
)
```

3. **Batch Processing**
```python
# Use batch ingestion for better performance
await ingestion_service.batch_ingest(json_data_list)
```

### API Performance Tips

1. **Async Processing**: All endpoints use async/await
2. **Background Tasks**: Heavy processing moved to background
3. **Caching**: Internal caching for frequent lookups
4. **Connection Pooling**: Database connections optimized

## 🔒 Security Considerations

### Production Checklist

1. **Environment Variables**
```bash
# Never commit these to version control
DATABASE_URL=postgresql://user:pass@host:5432/db
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=yourdomain.com,api.yourdomain.com
```

2. **API Security**
```python
# Add authentication middleware
from fastapi.security import HTTPBearer
security = HTTPBearer()

@app.get("/protected")
async def protected_route(token: str = Depends(security)):
    # Verify JWT token
    pass
```

3. **Database Security**
- Use strong passwords
- Enable SSL connections
- Restrict network access
- Regular security updates

## 📊 Monitoring and Logging

### Application Logging
```python
# Structured logging already configured
logger.info("Processing simulation data", 
           extra={"simulation_id": sim_id, "records": count})
```

### Health Monitoring
```bash
# Check application health
curl http://localhost:8000/health

# Check database connections
curl http://localhost:8000/system/info
```

### Metrics Collection (Optional)
- Prometheus metrics endpoint
- Grafana dashboards for visualization
- Alert manager for notifications

## 🧪 Testing Strategy

### Unit Tests
```bash
# Run comprehensive tests
pytest tests/ -v

# Test with coverage
pytest --cov=. tests/
```

### Integration Tests
```bash
# Test complete data flow
python example_usage.py

# Load testing
ab -n 1000 -c 10 http://localhost:8000/health
```

### Performance Testing
```python
# Simulate high-frequency data ingestion
async def load_test():
    tasks = []
    for i in range(100):
        task = ingest_simulation_data(sample_data)
        tasks.append(task)
    await asyncio.gather(*tasks)
```

## 🚀 Production Deployment

### Using Docker Compose
```bash
# Production deployment
docker-compose --profile production up -d

# Behind load balancer
docker-compose up -d --scale api=3
```

### Manual Deployment
```bash
# Install production dependencies
pip install gunicorn

# Run with Gunicorn
gunicorn main:app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -
```

### Environment-Specific Configuration
```python
# Production settings
if os.getenv("ENVIRONMENT") == "production":
    # Disable debug mode
    # Enable HTTPS only
    # Stricter CORS policies
    # Connection pooling optimization
```

## 📋 Maintenance Tasks

### Database Maintenance
```sql
-- Regular maintenance
VACUUM ANALYZE;
REINDEX DATABASE traffic_simulation;

-- Monitor table sizes
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(tablename::regclass))
FROM pg_tables WHERE schemaname = 'public';
```

### Log Rotation
```bash
# Configure log rotation
# /etc/logrotate.d/traffic-api
/var/log/traffic-api/*.log {
    daily
    rotate 30
    compress
    missingok
    notifempty
}
```

### Backup Strategy
```bash
# Database backups
pg_dump traffic_simulation | gzip > backup_$(date +%Y%m%d).sql.gz

# Automated backups
crontab -e
0 2 * * * /path/to/backup-script.sh
```

## 🔍 Troubleshooting

### Common Issues

1. **Database Connection Errors**
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check connection
psql -h localhost -U traffic_user -d traffic_simulation
```

2. **High Memory Usage**
```python
# Monitor connection pool
print(db_manager.get_connection_info())

# Adjust pool settings if needed
engine.update(pool_size=10, max_overflow=20)
```

3. **Slow Analytics Queries**
```sql
-- Check query performance
EXPLAIN ANALYZE SELECT * FROM performance_metrics 
WHERE simulation_id = 'SIM_001';

-- Add missing indexes
CREATE INDEX idx_custom ON table_name(column_name);
```

### Performance Monitoring
```python
# Add timing middleware
@app.middleware("http")
async def add_process_time_header(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response
```

## 📞 Support and Contribution

### Getting Help
- Check the API documentation: http://localhost:8000/docs
- Review logs for error details
- Use the test suite to verify functionality

### Contributing
1. Fork the repository
2. Create feature branch
3. Add tests for new functionality
4. Submit pull request with clear description

### Version History
- v1.0.0: Initial release with core analytics
- v1.1.0: Added batch processing and emergency handling
- v1.2.0: Enhanced monitoring and performance optimizations

This backend system provides a robust foundation for AI-powered traffic signal analytics with excellent performance, scalability, and maintainability.