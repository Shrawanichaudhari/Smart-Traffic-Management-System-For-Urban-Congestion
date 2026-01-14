# API Endpoints Documentation

## Overview

The Smart Traffic Signal Analytics API provides comprehensive endpoints for traffic data ingestion, analytics, and visualization. All endpoints return JSON responses and follow RESTful conventions.

## Base URL

```
http://localhost:8000
```

## Authentication

Currently, the API does not require authentication. In production deployments, consider implementing API keys or OAuth2.

## Response Format

All successful responses return JSON with appropriate HTTP status codes:
- `200 OK` - Successful request
- `400 Bad Request` - Invalid request data
- `500 Internal Server Error` - Server error

Error responses include an `error` field with details.

## Endpoints

### Health & System

#### GET /health
Health check endpoint for monitoring.

**Response:**
```json
{
  "status": "healthy",
  "database": "connected", 
  "timestamp": "2023-12-01T10:00:00.000Z",
  "service": "traffic-analytics-api"
}
```

#### GET /system/info
System information and database connection stats.

**Response:**
```json
{
  "database": {
    "url": "localhost:5432/traffic_simulation",
    "pool_size": 20,
    "checked_out": 2,
    "overflow": 0,
    "checked_in": 18
  },
  "service_info": {
    "name": "Smart Traffic Analytics API",
    "version": "1.0.0",
    "uptime": "N/A"
  }
}
```

### Data Ingestion

#### POST /api/v1/ingest/simulation
Ingest single simulation data point.

**Request Body:**
```json
{
  "data": {
    "simulation_id": "SIM_001",
    "timestamp": "2023-12-01T10:00:00Z",
    "intersection_id": "INT_001",
    "signals": [...],
    "metrics": {...}
  }
}
```

**Response:**
```json
{
  "status": "success",
  "simulation_id": "SIM_001",
  "timestamp": "2023-12-01T10:00:00+00:00",
  "records_inserted": {
    "signal_states": 4,
    "traffic_data": 4, 
    "performance_metrics": 1,
    "emergency_events": 0
  }
}
```

#### POST /api/v1/ingest/batch
Batch ingest multiple simulation data points.

**Request Body:**
```json
{
  "data_list": [
    { /* simulation data 1 */ },
    { /* simulation data 2 */ }
  ]
}
```

### Analytics

#### GET /api/v1/analytics/wait-times
Get average wait time analysis.

**Query Parameters:**
- `simulation_id` (optional): Filter by simulation
- `intersection_id` (optional): Filter by intersection  
- `time_window_hours` (optional): Time window in hours

**Response:**
```json
{
  "overall_avg_wait_time": 25.6,
  "best_performance": {
    "simulation_id": "SIM_001",
    "avg_wait_time": 18.2
  },
  "worst_performance": {
    "simulation_id": "SIM_002", 
    "avg_wait_time": 32.4
  },
  "detailed_data": [...],
  "total_intersections": 3,
  "total_simulations": 2
}
```

#### GET /api/v1/analytics/comparison/baseline-vs-ai
Compare baseline vs AI performance.

**Query Parameters:**
- `intersection_id` (optional): Filter by intersection
- `time_window_hours` (optional, default: 24): Time window
- `metric` (optional, default: "wait_time"): Primary metric

**Response:**
```json
{
  "comparison_data": {
    "baseline": {
      "avg_wait_time": 32.1,
      "avg_speed": 25.6,
      "total_fuel_saved": 12.5
    },
    "ai": {
      "avg_wait_time": 22.3,
      "avg_speed": 31.2, 
      "total_fuel_saved": 18.7
    }
  },
  "improvements": {
    "wait_time_reduction_pct": 30.5,
    "speed_improvement_pct": 21.9,
    "additional_fuel_saved": 6.2
  }
}
```

#### GET /api/v1/analytics/environmental-impact
Get environmental impact analysis.

**Query Parameters:**
- `simulation_id` (optional): Filter by simulation
- `comparison_mode` (optional, default: false): Enable mode comparison

#### GET /api/v1/analytics/emergency-handling
Get emergency vehicle handling performance.

**Query Parameters:**
- `simulation_id` (optional): Filter by simulation
- `time_window_hours` (optional): Time window in hours

#### GET /api/v1/analytics/time-series/{simulation_id}
Get time-series data for visualization.

**Path Parameters:**
- `simulation_id`: The simulation ID

**Query Parameters:**
- `metric` (optional, default: "wait_time"): Metric type
- `interval_minutes` (optional, default: 5): Time interval

### Dashboard

#### GET /api/v1/dashboard/live-metrics
Get real-time metrics for dashboard.

**Response:**
```json
{
  "timestamp": "2023-12-01T10:00:00.000Z",
  "wait_times": {...},
  "speeds": {...},
  "environmental_impact": {...}
}
```

#### GET /api/v1/dashboard/performance-comparison
Get performance comparison for dashboard.

**Response:**
```json
{
  "comparison": {...},
  "emergency_handling": {...},
  "generated_at": "2023-12-01T10:00:00.000Z"
}
```

### Charts & Visualization

#### GET /api/v1/charts/wait-time-trend
Get wait time trend data for line charts.

**Query Parameters:**
- `simulation_ids`: List of simulation IDs (required)
- `hours` (optional, default: 24): Time window in hours

**Response:**
```json
{
  "chart_type": "line",
  "datasets": [
    {
      "simulation_id": "SIM_001",
      "data": [...]
    }
  ],
  "x_axis": "timestamp",
  "y_axis": "avg_wait_time"
}
```

#### GET /api/v1/charts/performance-scatter
Get performance scatter plot data.

**Query Parameters:**
- `metric_x` (optional, default: "avg_wait_time"): X-axis metric
- `metric_y` (optional, default: "throughput"): Y-axis metric  
- `time_window_hours` (optional, default: 24): Time window

### Simulation Management

#### GET /api/v1/simulations/{simulation_id}
Get comprehensive simulation summary.

**Path Parameters:**
- `simulation_id`: The simulation ID

**Response:**
```json
{
  "simulation_id": "SIM_001",
  "mode": "ai",
  "status": "completed",
  "start_time": "2023-12-01T09:00:00+00:00",
  "end_time": "2023-12-01T10:00:00+00:00",
  "total_data_points": 720,
  "emergency_events": 5,
  "latest_metrics": {
    "avg_wait_time": 22.3,
    "throughput": 0.85,
    "fuel_saved": 15.2
  }
}
```

## Rate Limits

No rate limits are currently enforced, but consider implementing them for production use.

## Error Handling

All endpoints return appropriate HTTP status codes:

- `400 Bad Request`: Invalid input data or parameters
- `404 Not Found`: Resource not found  
- `422 Unprocessable Entity`: Validation errors
- `500 Internal Server Error`: Server-side errors

Example error response:
```json
{
  "error": "Validation failed",
  "detail": "Invalid timestamp format"
}
```
