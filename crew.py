import json
import asyncio
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from geopy.distance import geodesic
import numpy as np
import pandas as pd

from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

import os
from dotenv import load_dotenv

load_dotenv()

def get_llm():
    """Get configured LLM instance"""
    gemini_api_key = os.environ.get("GEMINI_API_KEY") 
    
    return LLM(
        model="gemini/gemini-2.0-flash-exp",
        api_key=gemini_api_key
    )

#def get_llm():
#    """Get configured LLM instance"""
#    openai_api_key = os.environ.get("OPENAI_API_KEY") 
#    
#    return LLM(
#        model="gpt-4o-mini-2024-07-18",
#        api_key=openai_api_key
#    )

@dataclass
class Location:
    lat: float
    lng: float
    name: str
    
@dataclass 
class Warehouse:
    id: int
    name: str
    lat: float
    lng: float
    type: str  # 'main', 'pickup', 'delivery'
    inventory: Dict[str, int]
    capacity: int = 1000
    
@dataclass
class Truck:
    id: str
    driver: str
    capacity: int
    current_load: int
    lat: float
    lng: float
    status: str  # 'idle', 'en-route', 'loading', 'completed'
    route: List[Dict]
    efficiency: float
    fuel_saved: float = 0.0
    co2_reduced: float = 0.0
    completed_stops: int = 0
    total_stops: int = 0

@dataclass
class RouteWaypoint:
    lat: float
    lng: float
    type: str  # 'start', 'pickup', 'delivery', 'end'
    name: str
    action: str

@dataclass
class OptimizedRoute:
    id: str
    name: str
    waypoints: List[RouteWaypoint]
    distance: float
    estimated_time: str
    efficiency: float
    priority: str
    truck_id: Optional[str] = None

# Enhanced Tools for CrewAI
class RouteOptimizationTool(BaseTool):
    name: str = "route_optimization"
    description: str = "Optimize delivery routes based on distance, traffic, and priority"
    
    def _run(self, warehouses: List[Dict], deliveries: List[Dict], truck_capacity: int) -> Dict:
        """Optimize routes using advanced algorithms"""
        try:
            # Convert to proper format
            route_waypoints = []
            
            # Add warehouse pickup points
            for warehouse in warehouses:
                route_waypoints.append(RouteWaypoint(
                    lat=warehouse['lat'],
                    lng=warehouse['lng'],
                    type='pickup',
                    name=warehouse['name'],
                    action=f"Pickup inventory from {warehouse['name']}"
                ))
            
            # Add delivery points
            for delivery in deliveries:
                route_waypoints.append(RouteWaypoint(
                    lat=delivery['lat'],
                    lng=delivery['lng'],
                    type='delivery',
                    name=delivery['name'],
                    action=f"Deliver {delivery.get('quantity', 'items')} to {delivery['name']}"
                ))
            
            # Calculate total distance
            total_distance = 0
            for i in range(len(route_waypoints) - 1):
                curr = route_waypoints[i]
                next_wp = route_waypoints[i + 1]
                distance = geodesic((curr.lat, curr.lng), (next_wp.lat, next_wp.lng)).miles
                total_distance += distance
            
            # Estimate time (assuming average speed of 45 mph)
            estimated_hours = total_distance / 45
            estimated_time = f"{int(estimated_hours)}h {int((estimated_hours % 1) * 60)}m"
            
            # Calculate efficiency based on distance optimization
            efficiency = max(85, min(99, 100 - (total_distance / 10)))
            
            optimized_route = OptimizedRoute(
                id=f"route_{int(time.time())}",
                name=f"Optimized Route - {len(route_waypoints)} stops",
                waypoints=route_waypoints,
                distance=total_distance,
                estimated_time=estimated_time,
                efficiency=efficiency,
                priority="high" if len(deliveries) > 3 else "medium"
            )
            
            return {
                "success": True,
                "route": asdict(optimized_route),
                "recommendations": [
                    f"Route optimized for {len(route_waypoints)} stops",
                    f"Estimated fuel savings: {efficiency - 85}%",
                    f"Total distance: {total_distance:.1f} miles"
                ]
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

class InventoryAnalysisTool(BaseTool):
    name: str = "inventory_analysis"
    description: str = "Analyze warehouse inventory levels and predict restocking needs"
    
    def _run(self, warehouses: List[Dict], demand_history: Dict) -> Dict:
        """Analyze inventory and predict needs"""
        try:
            analysis_results = []
            restock_recommendations = []
            
            for warehouse in warehouses:
                inventory = warehouse.get('inventory', {})
                warehouse_analysis = {
                    "warehouse_id": warehouse['id'],
                    "name": warehouse['name'],
                    "current_stock": inventory,
                    "status": "normal"
                }
                
                # Check for low stock items
                low_stock_items = []
                for product, quantity in inventory.items():
                    if quantity < 50:  # Threshold for low stock
                        low_stock_items.append(product)
                        restock_recommendations.append({
                            "warehouse": warehouse['name'],
                            "product": product,
                            "current_stock": quantity,
                            "recommended_restock": 200,
                            "priority": "high" if quantity < 20 else "medium"
                        })
                
                if low_stock_items:
                    warehouse_analysis["status"] = "needs_restock"
                    warehouse_analysis["low_stock_items"] = low_stock_items
                
                analysis_results.append(warehouse_analysis)
            
            return {
                "success": True,
                "warehouse_analysis": analysis_results,
                "restock_recommendations": restock_recommendations,
                "total_warehouses_analyzed": len(warehouses),
                "warehouses_needing_restock": len([w for w in analysis_results if w["status"] == "needs_restock"])
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

class DemandForecastingTool(BaseTool):
    name: str = "demand_forecasting"
    description: str = "Forecast demand based on historical data and trends"
    
    def _run(self, historical_data: Dict, region: str, time_horizon: int = 7) -> Dict:
        """Forecast demand for specified region and time horizon"""
        try:
            forecasts = {}
            
            for product, history in historical_data.items():
                if len(history) >= 3:
                    # Simple moving average forecast
                    recent_avg = sum(history[-3:]) / 3
                    trend = (history[-1] - history[-3]) / 2 if len(history) >= 3 else 0
                    forecast = max(0, recent_avg + trend)
                    
                    forecasts[product] = {
                        "predicted_demand": round(forecast),
                        "confidence": 0.85,
                        "trend": "increasing" if trend > 0 else "decreasing" if trend < 0 else "stable"
                    }
                else:
                    forecasts[product] = {
                        "predicted_demand": history[-1] if history else 0,
                        "confidence": 0.5,
                        "trend": "insufficient_data"
                    }
            
            return {
                "success": True,
                "region": region,
                "time_horizon_days": time_horizon,
                "forecasts": forecasts,
                "total_predicted_demand": sum(f["predicted_demand"] for f in forecasts.values())
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

class TruckDispatchTool(BaseTool):
    name: str = "truck_dispatch"
    description: str = "Dispatch trucks to optimal routes based on capacity and location"
    
    def _run(self, trucks: List[Dict], route: Dict, priority: str = "medium") -> Dict:
        """Dispatch the best available truck for a route"""
        try:
            available_trucks = [t for t in trucks if t.get('status') == 'idle']
            
            if not available_trucks:
                return {
                    "success": False,
                    "error": "No available trucks for dispatch",
                    "recommendation": "Wait for trucks to complete current routes"
                }
            
            best_truck = max(available_trucks, key=lambda t: t.get('efficiency', 0))    # select best truck via efficiency
            
            # Update truck status
            best_truck['status'] = 'en-route'
            best_truck['route'] = route.get('waypoints', [])
            best_truck['total_stops'] = len(route.get('waypoints', []))
            
            return {
                "success": True,
                "dispatched_truck": best_truck['id'],
                "driver": best_truck.get('driver', 'Unknown'),
                "route_name": route.get('name', 'Unnamed Route'),
                "estimated_completion": route.get('estimated_time', 'Unknown'),
                "efficiency_rating": best_truck.get('efficiency', 0)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

# Agents
def create_supply_chain_manager_agent() -> Agent:
    """Create the main supply chain coordinator agent"""
    return Agent(
        role='Supply Chain Manager',
        goal='Optimize overall supply chain operations, coordinate between warehouses, and ensure efficient inventory distribution',
        backstory="""You are an experienced supply chain manager at Walmart with 15 years of experience. 
        You excel at coordinating complex logistics operations, managing inventory across multiple warehouses, 
        and ensuring customer demands are met efficiently. You use data-driven insights to make strategic decisions.""",
        verbose=True,
        allow_delegation=True,
        max_rpm=15,  # fuck around here if gemini ratelimits strike you
        max_retry_limit=2,
        tools=[InventoryAnalysisTool(), DemandForecastingTool()],
        llm=get_llm()
    )

def create_logistics_coordinator_agent() -> Agent:
    """Create the logistics and route optimization agent"""
    return Agent(
        role='Logistics Coordinator',
        goal='Optimize delivery routes, manage truck dispatching, and minimize transportation costs while maximizing efficiency',
        backstory="""You are a logistics expert specializing in route optimization and fleet management. 
        You have deep knowledge of transportation networks, traffic patterns, and fuel efficiency optimization. 
        Your goal is to ensure the most efficient movement of goods across the supply chain network.""",
        verbose=True,
        max_rpm=15,
        max_retry_limit=2,
        allow_delegation=False,
        tools=[RouteOptimizationTool(), TruckDispatchTool()],
        llm=get_llm()
    )

def create_demand_analyst_agent() -> Agent:
    """Create the demand analysis and forecasting agent"""
    return Agent(
        role='Demand Analyst',
        goal='Analyze consumer demand patterns, forecast future needs, and recommend inventory adjustments',
        backstory="""You are a data scientist specializing in demand forecasting and consumer behavior analysis. 
        You use advanced analytics to predict demand patterns, seasonal trends, and help optimize inventory levels 
        across different regions. Your insights drive proactive inventory management decisions.""",
        verbose=True,
        max_rpm=15,
        max_retry_limit=2,
        allow_delegation=False,
        tools=[DemandForecastingTool(), InventoryAnalysisTool()],
        llm=get_llm()
    )

# Main Multi-Agent System
class WalmartSupplyChainCrew:
    def __init__(self):
        self.warehouses = self._initialize_warehouses()
        self.trucks = self._initialize_trucks()
        self.demand_history = self._initialize_demand_history()
        self.performance_metrics = {
            "total_distance_saved": 0,
            "fuel_saved": 0,
            "co2_reduced": 0,
            "efficiency_score": 0,
            "active_routes": 0
        }
        
        # initialize agents
        self.supply_chain_manager = create_supply_chain_manager_agent()
        self.logistics_coordinator = create_logistics_coordinator_agent()
        self.demand_analyst = create_demand_analyst_agent()
        
        self.crew = Crew(
            agents=[self.supply_chain_manager, self.logistics_coordinator, self.demand_analyst],
            process=Process.sequential,
            verbose=True
        )
    
    def _initialize_warehouses(self) -> List[Warehouse]:
        """Initialize warehouse data"""
        return [
            Warehouse(1, 'Dallas DC', 32.7767, -96.7970, 'main', 
                    {'cereal': 1250, 'milk': 890, 'juice': 650, 'bread': 420}, 2000),
            Warehouse(2, 'Houston DC', 29.7604, -95.3698, 'main', 
                    {'cereal': 890, 'milk': 1100, 'juice': 300, 'bread': 380}, 2000),
            Warehouse(3, 'Austin DC', 30.2672, -97.7431, 'main', 
                    {'cereal': 650, 'milk': 480, 'juice': 720, 'bread': 290}, 1500),
            Warehouse(4, 'Fort Worth Hub', 32.7555, -97.3308, 'pickup', 
                    {'cereal': 320, 'milk': 240, 'juice': 180, 'bread': 150}, 800),
            Warehouse(5, 'San Antonio Hub', 29.4241, -98.4936, 'delivery', 
                    {'cereal': 180, 'milk': 160, 'juice': 140, 'bread': 120}, 600)
        ]
    
    def _initialize_trucks(self) -> List[Truck]:
        """Initialize truck fleet"""
        return [
            Truck('T001', 'John Smith', 100, 0, 32.7767, -96.7970, 'idle', [], 98.5),
            Truck('T002', 'Sarah Johnson', 120, 0, 29.7604, -95.3698, 'idle', [], 97.2),
            Truck('T003', 'Mike Wilson', 110, 0, 30.2672, -97.7431, 'idle', [], 96.8),
            Truck('T004', 'Lisa Brown', 95, 0, 32.7555, -97.3308, 'idle', [], 98.0)
        ]
    
    def _initialize_demand_history(self) -> Dict:
        """Initialize demand history for forecasting"""
        return {
            "Dallas": {
                "cereal": [120, 140, 160, 180, 200],
                "milk": [200, 220, 240, 260, 280],
                "juice": [80, 90, 100, 110, 120],
                "bread": [150, 160, 170, 180, 190]
            },
            "Houston": {
                "cereal": [100, 110, 120, 130, 140],
                "milk": [180, 190, 200, 210, 220],
                "juice": [70, 75, 80, 85, 90],
                "bread": [140, 145, 150, 155, 160]
            },
            "Austin": {
                "cereal": [80, 85, 90, 95, 100],
                "milk": [120, 125, 130, 135, 140],
                "juice": [90, 95, 100, 105, 110],
                "bread": [100, 105, 110, 115, 120]
            }
        }
    
    def analyze_supply_chain_status(self) -> Dict:
        """Analyze current supply chain status using AI agents"""
        
        # Create comprehensive analysis task
        analysis_task = Task(
            description=f"""
            Analyze the current supply chain status including:
            1. Warehouse inventory levels: {[asdict(w) for w in self.warehouses]}
            2. Truck fleet status: {[asdict(t) for t in self.trucks]}
            3. Historical demand data: {self.demand_history}
            
            Provide recommendations for:
            - Inventory rebalancing needs
            - Optimal routing strategies
            - Demand forecasting insights
            - Performance optimization opportunities
            
            Return a comprehensive status report with actionable insights.
            """,
            expected_output="A detailed supply chain analysis report with specific recommendations",
            agent=self.supply_chain_manager
        )
        
        # Create a temporary crew for this specific task
        temp_crew = Crew(
            agents=[self.supply_chain_manager],
            tasks=[analysis_task],
            process=Process.sequential,
            verbose=True
        )
        
        result = temp_crew.kickoff()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "analysis": result,
            "warehouses": [asdict(w) for w in self.warehouses],
            "trucks": [asdict(t) for t in self.trucks],
            "performance_metrics": self.performance_metrics
        }
    
    def optimize_route(self, origin_warehouse_id: int, destination_requests: List[Dict]) -> Dict:
        """Optimize a route using AI agents"""
        
        origin_warehouse = next((w for w in self.warehouses if w.id == origin_warehouse_id), None)
        if not origin_warehouse:
            return {"success": False, "error": "Origin warehouse not found"}
        
        # Create route optimization task
        route_task = Task(
            description=f"""
            Optimize a delivery route starting from {origin_warehouse.name}:
            
            Origin: {asdict(origin_warehouse)}
            Delivery Requests: {destination_requests}
            Available Trucks: {[asdict(t) for t in self.trucks if t.status == 'idle']}
            
            Requirements:
            1. Minimize total distance and fuel consumption
            2. Respect truck capacity constraints
            3. Prioritize high-priority deliveries
            4. Consider real-time traffic and road conditions
            5. Optimize for environmental impact
            
            Provide a complete optimized route with waypoints, truck assignment, and efficiency metrics.
            """,
            expected_output="An optimized route plan with truck assignment and efficiency metrics",
            agent=self.logistics_coordinator
        )
        
        # Create a temporary crew for this specific task
        temp_crew = Crew(
            agents=[self.logistics_coordinator],
            tasks=[route_task],
            process=Process.sequential,
            verbose=True
        )
        
        result = temp_crew.kickoff()
        
        # Update performance metrics
        self.performance_metrics["active_routes"] += 1
        self.performance_metrics["efficiency_score"] = min(99, self.performance_metrics["efficiency_score"] + 0.5)
        
        return {
            "success": True,
            "optimization_result": result,
            "timestamp": datetime.now().isoformat()
        }
    
    def forecast_demand(self, region: str, days_ahead: int = 7) -> Dict:
        """Forecast demand for a specific region"""
        
        if region not in self.demand_history:
            return {"success": False, "error": f"No historical data for region: {region}"}
        
        forecast_task = Task(
            description=f"""
            Forecast demand for region: {region}
            
            Historical Data: {self.demand_history[region]}
            Forecast Horizon: {days_ahead} days
            Current Season: {datetime.now().strftime("%B")}
            
            Consider:
            1. Historical trends and seasonality
            2. Recent demand patterns
            3. External factors (holidays, events, weather)
            4. Regional preferences and demographics
            
            Provide detailed demand forecasts with confidence intervals and recommendations for inventory adjustments.
            """,
            expected_output="Detailed demand forecast with confidence metrics and inventory recommendations",
            agent=self.demand_analyst
        )
        
        # Create a temporary crew for this specific task
        temp_crew = Crew(
            agents=[self.demand_analyst],
            tasks=[forecast_task],
            process=Process.sequential,
            verbose=True
        )
        
        result = temp_crew.kickoff()
        
        return {
            "success": True,
            "region": region,
            "forecast_horizon": days_ahead,
            "forecast_result": result,
            "timestamp": datetime.now().isoformat()
        }
    
    def handle_emergency_restock(self, warehouse_id: int, product: str, critical_level: int) -> Dict:
        """Handle emergency restocking situation using AI coordination"""
        
        target_warehouse = next((w for w in self.warehouses if w.id == warehouse_id), None)
        if not target_warehouse:
            return {"success": False, "error": "Target warehouse not found"}
        
        emergency_task = Task(
            description=f"""
            EMERGENCY RESTOCK SITUATION:
            
            Warehouse: {target_warehouse.name} (ID: {warehouse_id})
            Product: {product}
            Critical Level: {critical_level} units remaining
            Current Inventory: {target_warehouse.inventory.get(product, 0)} units
            
            Available Source Warehouses: {[asdict(w) for w in self.warehouses if w.id != warehouse_id and w.inventory.get(product, 0) > 100]}
            Available Trucks: {[asdict(t) for t in self.trucks if t.status == 'idle']}
            
            IMMEDIATE ACTIONS REQUIRED:
            1. Identify nearest warehouse with sufficient {product} inventory
            2. Calculate fastest route for emergency delivery
            3. Dispatch most efficient available truck
            4. Provide ETA and alternative solutions if needed
            5. Consider customer impact and mitigation strategies
            
            This is a high-priority emergency requiring immediate resolution.
            """,
            expected_output="Emergency restock action plan with truck dispatch and ETA",
            agent=self.supply_chain_manager
        )
        
        # Create a temporary crew for this specific task
        temp_crew = Crew(
            agents=[self.supply_chain_manager],
            tasks=[emergency_task],
            process=Process.sequential,
            verbose=True
        )
        
        result = temp_crew.kickoff()
        
        return {
            "success": True,
            "emergency_type": "critical_restock",
            "warehouse": target_warehouse.name,
            "product": product,
            "action_plan": result,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_real_time_status(self) -> Dict:
        """Get real-time status of the entire supply chain system"""
        
        # Calculate dynamic metrics
        total_inventory = sum(sum(w.inventory.values()) for w in self.warehouses)
        active_trucks = len([t for t in self.trucks if t.status != 'idle'])
        avg_efficiency = sum(t.efficiency for t in self.trucks) / len(self.trucks)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "system_status": "operational",
            "warehouses": {
                "total": len(self.warehouses),
                "total_inventory": total_inventory,
                "details": [asdict(w) for w in self.warehouses]
            },
            "fleet": {
                "total_trucks": len(self.trucks),
                "active_trucks": active_trucks,
                "idle_trucks": len(self.trucks) - active_trucks,
                "average_efficiency": round(avg_efficiency, 1),
                "details": [asdict(t) for t in self.trucks]
            },
            "performance_metrics": self.performance_metrics,
            "ai_agents_status": {
                "supply_chain_manager": "active",
                "logistics_coordinator": "active", 
                "demand_analyst": "active"
            }
        }

async def run_walmart_supply_chain_demo():
    """Run the Walmart supply chain demo with CrewAI agents"""
    print("🚛 Initializing Walmart Supply Chain AI System...")
    print("=" * 60)
    
    supply_chain_system = WalmartSupplyChainCrew()
    
    print("✅ Multi-agent system initialized successfully!")
    print(f"📦 Warehouses: {len(supply_chain_system.warehouses)}")
    print(f"🚛 Trucks: {len(supply_chain_system.trucks)}")
    print(f"🤖 AI Agents: 3 (Supply Chain Manager, Logistics Coordinator, Demand Analyst)")
    print("\n" + "=" * 60)
    
    # Scenario 1: Analyze current supply chain status
    print("\n🔍 SCENARIO 1: Supply Chain Analysis")
    print("-" * 50)
    
    try:
        status_analysis = supply_chain_system.analyze_supply_chain_status()
        print("✅ Supply chain analysis completed!")
        print(f"📊 Analysis timestamp: {status_analysis['timestamp']}")
        print(f"🏭 Active warehouses: {len(status_analysis['warehouses'])}")
        print(f"🚛 Fleet status: {len([t for t in status_analysis['trucks'] if t['status'] == 'idle'])} idle, {len([t for t in status_analysis['trucks'] if t['status'] != 'idle'])} active")
        
    except Exception as e:
        print(f"❌ Error in supply chain analysis: {str(e)}")
    
    # Scenario 2: Optimize a complex delivery route
    print("\n🗺️ SCENARIO 2: Route Optimization")
    print("-" * 50)
    
    try:
        delivery_requests = [
            {"name": "Plano Store", "lat": 33.0198, "lng": -96.6989, "quantity": 45, "priority": "high"},
            {"name": "Frisco Store", "lat": 33.1507, "lng": -96.8236, "quantity": 30, "priority": "medium"},
            {"name": "McKinney Store", "lat": 33.1972, "lng": -96.6397, "quantity": 25, "priority": "high"}
        ]
        
        route_optimization = supply_chain_system.optimize_route(1, delivery_requests)  # Dallas DC
        
        if route_optimization["success"]:
            print("✅ Route optimization completed!")
            print(f"🎯 Optimized route from Dallas DC to {len(delivery_requests)} locations")
            print(f"⏰ Optimization timestamp: {route_optimization['timestamp']}")
        else:
            print(f"❌ Route optimization failed: {route_optimization.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Error in route optimization: {str(e)}")
    
    # Scenario 3: Demand forecasting
    print("\n📈 SCENARIO 3: Demand Forecasting")
    print("-" * 50)
    
    try:
        demand_forecast = supply_chain_system.forecast_demand("Dallas", 7)
        
        if demand_forecast["success"]:
            print("✅ Demand forecasting completed!")
            print(f"📍 Region: {demand_forecast['region']}")
            print(f"📅 Forecast horizon: {demand_forecast['forecast_horizon']} days")
            print(f"🕐 Forecast timestamp: {demand_forecast['timestamp']}")
        else:
            print(f"❌ Demand forecasting failed: {demand_forecast.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Error in demand forecasting: {str(e)}")
    
    # Scenario 4: Emergency restocking
    print("\n🚨 SCENARIO 4: Emergency Restocking")
    print("-" * 50)
    
    try:
        emergency_response = supply_chain_system.handle_emergency_restock(5, "milk", 15)  # San Antonio Hub
        
        if emergency_response["success"]:
            print("✅ Emergency restocking handled!")
            print(f"🏭 Warehouse: {emergency_response['warehouse']}")
            print(f"📦 Product: {emergency_response['product']}")
            print(f"⚡ Response timestamp: {emergency_response['timestamp']}")
        else:
            print(f"❌ Emergency restocking failed: {emergency_response.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Error in emergency restocking: {str(e)}")
    
    print("\n📊 FINAL SYSTEM STATUS")
    print("-" * 50)
    
    try:
        final_status = supply_chain_system.get_real_time_status()
        print(f"🕐 Status timestamp: {final_status['timestamp']}")
        print(f"🟢 System status: {final_status['system_status']}")
        print(f"🏭 Total warehouses: {final_status['warehouses']['total']}")
        print(f"📦 Total inventory: {final_status['warehouses']['total_inventory']} units")
        print(f"🚛 Fleet: {final_status['fleet']['total_trucks']} trucks ({final_status['fleet']['active_trucks']} active)")
        print(f"⚡ Average efficiency: {final_status['fleet']['average_efficiency']}%")
        print(f"🤖 AI agents: All {len(final_status['ai_agents_status'])} agents active")
        
    except Exception as e:
        print(f"❌ Error getting system status: {str(e)}")
    
    print("\n" + "=" * 60)
    print("🎉 Walmart Supply Chain AI Demo Complete!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(run_walmart_supply_chain_demo())
