# ... existing code ...

# Signal timing endpoints
@app.get("/api/v1/signals/timings")
async def get_signal_timings(intersection_id: Optional[str] = None):
    """Get current signal timings for an intersection."""
    try:
        if USE_REAL_DB:
            with get_db_context() as db:
                query = """
                    SELECT s.signal_id, s.direction, s.lane_type,
                           ss.status as current_state, ss.timer_remaining,
                           ss.green_time_allocated as max_time,
                           i.intersection_id
                    FROM signals s
                    JOIN intersections i ON s.intersection_id = i.intersection_id
                    LEFT JOIN signal_states ss ON s.signal_id = ss.signal_id
                    WHERE ss.timestamp = (
                        SELECT MAX(timestamp)
                        FROM signal_states
                        WHERE signal_id = s.signal_id
                    )
                """
                
                params = {}
                if intersection_id:
                    query += " AND i.intersection_id = :intersection_id"
                    params["intersection_id"] = intersection_id
                
                result = db.execute(text(query), params)
                
                signals = [{
                    "lane_id": str(row.signal_id),
                    "direction": row.direction,
                    "type": row.lane_type,
                    "current_light": row.current_state or "RED",
                    "time_remaining": row.timer_remaining or 30,
                    "max_time": row.max_time or 60,
                    "intersection_id": row.intersection_id
                } for row in result]
                
                return {"signal_timings": signals}
        else:
            # Return mock data for testing
            mock_signals = [
                {
                    "lane_id": f"LANE_{i}",
                    "direction": direction,
                    "type": "straight",
                    "current_light": random.choice(["RED", "GREEN", "YELLOW"]),
                    "time_remaining": random.randint(0, 30),
                    "max_time": 60,
                    "intersection_id": intersection_id or "INT_001"
                }
                for i, direction in enumerate(["north", "south", "east", "west"], 1)
            ]
            return {"signal_timings": mock_signals}
    
    except Exception as e:
        logger.error(f"Error getting signal timings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ... existing code ...