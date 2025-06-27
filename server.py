from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import asyncio
import json
import logging
from datetime import datetime
import uvicorn

from crew import WalmartSupplyChainCrew

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# NOTE: I had no involvement with this- please remove this PoS API at your earliest convenience

app = FastAPI(
    title="Walmart Supply Chain AI API",
    description="Multi-Agent Supply Chain Optimization System",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

supply_chain_system = None

class RouteOptimizationRequest(BaseModel):
    origin_warehouse_id: int
    destination_requests: List[Dict[str, Any]]
    truck_preferences: Optional[Dict[str, Any]] = None

class DemandForecastRequest(BaseModel):
    region: str
    days_ahead: int = 7
    products: Optional[List[str]] = None

class EmergencyRestockRequest(BaseModel):
    warehouse_id: int
    product: str
    critical_level: int
    urgency: str = "high"

class TruckDispatchRequest(BaseModel):
    truck_id: str
    route_id: str
    priority: str = "medium"

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Client connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"Client disconnected. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                # Remove broken connections
                self.active_connections.remove(connection)

manager = ConnectionManager()

# Initialize the system
@app.on_event("startup")
async def startup_event():
    global supply_chain_system
    logger.info("Initializing Walmart Supply Chain AI System...")
    try:
        supply_chain_system = WalmartSupplyChainCrew()
        logger.info("✅ Supply Chain AI System initialized successfully!")
    except Exception as e:
        logger.error(f"❌ Failed to initialize system: {str(e)}")
        raise

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "system": "Walmart Supply Chain AI",
        "version": "1.0.0"
    }

# Get system status
@app.get("/api/status")
async def get_system_status():
    """Get real-time system status"""
    try:
        if not supply_chain_system:
            raise HTTPException(status_code=503, detail="System not initialized")
        
        status = supply_chain_system.get_real_time_status()
        return JSONResponse(content=status)
    except Exception as e:
        logger.error(f"Error getting system status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Get warehouse data
@app.get("/api/warehouses")
async def get_warehouses():
    """Get all warehouse information"""
    try:
        if not supply_chain_system:
            raise HTTPException(status_code=503, detail="System not initialized")
        
        warehouses = [
            {
                "id": w.id,
                "name": w.name,
                "lat": w.lat,
                "lng": w.lng,
                "type": w.type,
                "inventory": w.inventory,
                "capacity": w.capacity,
                "utilization": sum(w.inventory.values()) / w.capacity * 100
            }
            for w in supply_chain_system.warehouses
        ]
        
        return JSONResponse(content={"warehouses": warehouses})
    except Exception as e:
        logger.error(f"Error getting warehouses: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Get truck fleet data
@app.get("/api/trucks")
async def get_trucks():
    """Get all truck fleet information"""
    try:
        if not supply_chain_system:
            raise HTTPException(status_code=503, detail="System not initialized")
        
        trucks = [
            {
                "id": t.id,
                "driver": t.driver,
                "capacity": t.capacity,
                "current_load": t.current_load,
                "lat": t.lat,
                "lng": t.lng,
                "status": t.status,
                "efficiency": t.efficiency,
                "fuel_saved": t.fuel_saved,
                "co2_reduced": t.co2_reduced,
                "completed_stops": t.completed_stops,
                "total_stops": t.total_stops,
                "route": t.route
            }
            for t in supply_chain_system.trucks
        ]
        
        return JSONResponse(content={"trucks": trucks})
    except Exception as e:
        logger.error(f"Error getting trucks: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Analyze supply chain
@app.post("/api/analyze")
async def analyze_supply_chain():
    """Perform comprehensive supply chain analysis using AI agents"""
    try:
        if not supply_chain_system:
            raise HTTPException(status_code=503, detail="System not initialized")
        
        # Broadcast analysis start
        await manager.broadcast(json.dumps({
            "type": "analysis_started",
            "message": "AI agents are analyzing supply chain...",
            "timestamp": datetime.now().isoformat()
        }))
        
        analysis = supply_chain_system.analyze_supply_chain_status()
        
        # Broadcast analysis complete
        await manager.broadcast(json.dumps({
            "type": "analysis_complete",
            "data": analysis,
            "timestamp": datetime.now().isoformat()
        }))
        
        return JSONResponse(content=analysis)
    except Exception as e:
        logger.error(f"Error in supply chain analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Optimize route
@app.post("/api/optimize-route")
async def optimize_route(request: RouteOptimizationRequest):
    """Optimize delivery route using AI agents"""
    try:
        if not supply_chain_system:
            raise HTTPException(status_code=503, detail="System not initialized")
        
        # Broadcast optimization start
        await manager.broadcast(json.dumps({
            "type": "route_optimization_started",
            "message": f"Optimizing route from warehouse {request.origin_warehouse_id}...",
            "timestamp": datetime.now().isoformat()
        }))
        
        result = supply_chain_system.optimize_route(
            request.origin_warehouse_id,
            request.destination_requests
        )
        
        # Broadcast optimization complete
        await manager.broadcast(json.dumps({
            "type": "route_optimization_complete",
            "data": result,
            "timestamp": datetime.now().isoformat()
        }))
        
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Error in route optimization: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Forecast demand
@app.post("/api/forecast-demand")
async def forecast_demand(request: DemandForecastRequest):
    """Forecast demand using AI agents"""
    try:
        if not supply_chain_system:
            raise HTTPException(status_code=503, detail="System not initialized")
        
        # Broadcast forecasting start
        await manager.broadcast(json.dumps({
            "type": "demand_forecast_started",
            "message": f"Forecasting demand for {request.region}...",
            "timestamp": datetime.now().isoformat()
        }))
        
        result = supply_chain_system.forecast_demand(
            request.region,
            request.days_ahead
        )
        
        # Broadcast forecasting complete
        await manager.broadcast(json.dumps({
            "type": "demand_forecast_complete",
            "data": result,
            "timestamp": datetime.now().isoformat()
        }))
        
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Error in demand forecasting: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Handle emergency restock
@app.post("/api/emergency-restock")
async def emergency_restock(request: EmergencyRestockRequest):
    """Handle emergency restocking situation"""
    try:
        if not supply_chain_system:
            raise HTTPException(status_code=503, detail="System not initialized")
        
        # Broadcast emergency alert
        await manager.broadcast(json.dumps({
            "type": "emergency_alert",
            "message": f"Emergency restock initiated for warehouse {request.warehouse_id}",
            "urgency": request.urgency,
            "timestamp": datetime.now().isoformat()
        }))
        
        result = supply_chain_system.handle_emergency_restock(
            request.warehouse_id,
            request.product,
            request.critical_level
        )
        
        # Broadcast emergency response
        await manager.broadcast(json.dumps({
            "type": "emergency_response",
            "data": result,
            "timestamp": datetime.now().isoformat()
        }))
        
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Error in emergency restock: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Dispatch truck
@app.post("/api/dispatch-truck")
async def dispatch_truck(request: TruckDispatchRequest):
    """Dispatch a truck to a route"""
    try:
        if not supply_chain_system:
            raise HTTPException(status_code=503, detail="System not initialized")
        
        # Find the truck
        truck = next((t for t in supply_chain_system.trucks if t.id == request.truck_id), None)
        if not truck:
            raise HTTPException(status_code=404, detail="Truck not found")
        
        if truck.status != 'idle':
            raise HTTPException(status_code=400, detail="Truck is not available")
        
        # Update truck status
        truck.status = 'en-route'
        
        # Broadcast truck dispatch
        await manager.broadcast(json.dumps({
            "type": "truck_dispatched",
            "data": {
                "truck_id": request.truck_id,
                "route_id": request.route_id,
                "priority": request.priority,
                "driver": truck.driver
            },
            "timestamp": datetime.now().isoformat()
        }))
        
        return JSONResponse(content={
            "success": True,
            "message": f"Truck {request.truck_id} dispatched successfully",
            "truck_id": request.truck_id,
            "status": truck.status
        })
    except Exception as e:
        logger.error(f"Error dispatching truck: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Send initial system status
        if supply_chain_system:
            status = supply_chain_system.get_real_time_status()
            await websocket.send_text(json.dumps({
                "type": "system_status",
                "data": status,
                "timestamp": datetime.now().isoformat()
            }))
        
        while True:
            # Keep connection alive and listen for client messages
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "ping":
                await websocket.send_text(json.dumps({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                }))
            elif message.get("type") == "request_status":
                if supply_chain_system:
                    status = supply_chain_system.get_real_time_status()
                    await websocket.send_text(json.dumps({
                        "type": "system_status",
                        "data": status,
                        "timestamp": datetime.now().isoformat()
                    }))
                    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        manager.disconnect(websocket)

# Performance metrics endpoint
@app.get("/api/metrics")
async def get_performance_metrics():
    """Get performance metrics for the dashboard"""
    try:
        if not supply_chain_system:
            raise HTTPException(status_code=503, detail="System not initialized")
        
        # Calculate real-time metrics
        total_inventory = sum(sum(w.inventory.values()) for w in supply_chain_system.warehouses)
        active_trucks = len([t for t in supply_chain_system.trucks if t.status != 'idle'])
        total_fuel_saved = sum(t.fuel_saved for t in supply_chain_system.trucks)
        total_co2_reduced = sum(t.co2_reduced for t in supply_chain_system.trucks)
        avg_efficiency = sum(t.efficiency for t in supply_chain_system.trucks) / len(supply_chain_system.trucks)
        
        metrics = {
            "total_distance": supply_chain_system.performance_metrics.get("total_distance_saved", 0),
            "fuel_saved": total_fuel_saved,
            "co2_reduced": total_co2_reduced,
            "efficiency": round(avg_efficiency, 1),
            "active_routes": active_trucks,
            "total_inventory": total_inventory,
            "warehouse_utilization": round((total_inventory / sum(w.capacity for w in supply_chain_system.warehouses)) * 100, 1),
            "fleet_utilization": round((active_trucks / len(supply_chain_system.trucks)) * 100, 1),
            "timestamp": datetime.now().isoformat()
        }
        
        return JSONResponse(content=metrics)
    except Exception as e:
        logger.error(f"Error getting metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Background task to simulate real-time updates
async def simulate_real_time_updates():
    """Simulate real-time system updates"""
    while True:
        try:
            if supply_chain_system and len(manager.active_connections) > 0:
                # Simulate some changes
                import random
                
                # Update some truck positions slightly
                for truck in supply_chain_system.trucks:
                    if truck.status == 'en-route':
                        truck.lat += random.uniform(-0.001, 0.001)
                        truck.lng += random.uniform(-0.001, 0.001)
                        truck.fuel_saved += random.uniform(0, 0.1)
                        truck.co2_reduced += random.uniform(0, 0.3)
                
                # Update performance metrics
                supply_chain_system.performance_metrics["efficiency_score"] = min(99, 
                    supply_chain_system.performance_metrics["efficiency_score"] + random.uniform(-0.5, 0.5))
                
                # Broadcast updates
                await manager.broadcast(json.dumps({
                    "type": "real_time_update",
                    "data": {
                        "trucks": [
                            {
                                "id": t.id,
                                "lat": t.lat,
                                "lng": t.lng,
                                "status": t.status,
                                "fuel_saved": t.fuel_saved,
                                "co2_reduced": t.co2_reduced
                            }
                            for t in supply_chain_system.trucks
                        ],
                        "performance_metrics": supply_chain_system.performance_metrics
                    },
                    "timestamp": datetime.now().isoformat()
                }))
            
            await asyncio.sleep(5)  # Update every 5 seconds
        except Exception as e:
            logger.error(f"Error in real-time updates: {str(e)}")
            await asyncio.sleep(10)

# Start background task
@app.on_event("startup")
async def start_background_tasks():
    asyncio.create_task(simulate_real_time_updates())

if __name__ == "__main__":
    print("🚀 Starting Walmart Supply Chain AI Server...")
    print("🔗 Frontend can connect to: http://localhost:8000")
    print("📊 API documentation: http://localhost:8000/docs")
    print("🔌 WebSocket endpoint: ws://localhost:8000/ws")
    
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
