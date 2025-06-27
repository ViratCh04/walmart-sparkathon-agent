#!/usr/bin/env python3
"""
Walmart Supply Chain Multi-Agent System
Powered by CrewAI for intelligent logistics optimization
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Dict, List, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    from crew import WalmartSupplyChainCrew
    print("✅ CrewAI system import successful")
except ImportError as e:
    print(f"⚠️  CrewAI system not available: {e}")
    print("📦 Installing required packages...")
    
    # Fallback to basic implementation
    class BasicSupplyChainSystem:
        def __init__(self):
            self.warehouses = [
                {'id': 1, 'name': 'Dallas DC', 'lat': 32.7767, 'lng': -96.7970, 'type': 'main', 'inventory': {'cereal': 1250, 'milk': 890}},
                {'id': 2, 'name': 'Houston DC', 'lat': 29.7604, 'lng': -95.3698, 'type': 'main', 'inventory': {'cereal': 890, 'milk': 1100}},
                {'id': 3, 'name': 'Austin DC', 'lat': 30.2672, 'lng': -97.7431, 'type': 'main', 'inventory': {'cereal': 650, 'milk': 480}}
            ]
            self.trucks = [
                {'id': 'T001', 'driver': 'John Smith', 'capacity': 100, 'lat': 32.7767, 'lng': -96.7970, 'status': 'idle', 'efficiency': 98.5},
                {'id': 'T002', 'driver': 'Sarah Johnson', 'capacity': 120, 'lat': 29.7604, 'lng': -95.3698, 'status': 'idle', 'efficiency': 97.2}
            ]
            self.performance_metrics = {
                'fuel_saved': 125,
                'co2_reduced': 340,
                'total_distance': 1250,
                'efficiency': 96.8
            }
        
        def get_system_status(self):
            return {
                'timestamp': datetime.now().isoformat(),
                'warehouses': self.warehouses,
                'trucks': self.trucks,
                'performance_metrics': self.performance_metrics,
                'system_type': 'basic_fallback'
            }
        
        def simulate_route_optimization(self, origin_id: int):
            origin = next((w for w in self.warehouses if w['id'] == origin_id), self.warehouses[0])
            return {
                'success': True,
                'route': {
                    'id': f'route_{origin_id}',
                    'name': f'Optimized Route from {origin["name"]}',
                    'waypoints': [
                        {'lat': origin['lat'], 'lng': origin['lng'], 'name': origin['name'], 'action': 'Load inventory'},
                        {'lat': 33.0198, 'lng': -96.6989, 'name': 'Plano Store', 'action': 'Deliver 45 units'},
                        {'lat': 33.1507, 'lng': -96.8236, 'name': 'Frisco Store', 'action': 'Deliver 30 units'}
                    ],
                    'distance': 156.7,
                    'estimated_time': '4h 30m',
                    'efficiency': 98.2
                },
                'message': 'Route optimized using basic algorithm'
            }
        
        def simulate_demand_forecast(self, region: str):
            return {
                'success': True,
                'region': region,
                'forecasts': {
                    'cereal': {'predicted_demand': 180, 'confidence': 0.85, 'trend': 'increasing'},
                    'milk': {'predicted_demand': 220, 'confidence': 0.90, 'trend': 'stable'}
                },
                'message': f'Demand forecast for {region} region'
            }

def print_banner():
    """Print system banner"""
    print("=" * 70)
    print("🚛 WALMART SUPPLY CHAIN MULTI-AGENT SYSTEM")
    print("🤖 Powered by CrewAI & Advanced AI Agents")
    print("=" * 70)

def print_system_info(system):
    """Print system information"""
    print("\n📊 SYSTEM INFORMATION")
    print("-" * 50)
    print(f"🏭 Warehouses: {len(system.warehouses) if hasattr(system, 'warehouses') else 'N/A'}")
    print(f"🚛 Truck Fleet: {len(system.trucks) if hasattr(system, 'trucks') else 'N/A'}")
    print(f"🤖 AI Agents: {'3 (CrewAI)' if hasattr(system, 'crew') else 'Basic System'}")
    print(f"🔧 System Type: {'Advanced CrewAI' if hasattr(system, 'crew') else 'Basic Fallback'}")

def demonstrate_capabilities(system):
    """Demonstrate system capabilities"""
    print("\n🎯 DEMONSTRATING SYSTEM CAPABILITIES")
    print("-" * 50)
    
    # 1. System Status
    print("\n1️⃣ Getting System Status...")
    try:
        if hasattr(system, 'get_real_time_status'):
            status = system.get_real_time_status()
        else:
            status = system.get_system_status()
        print(f"   ✅ Status retrieved at {status.get('timestamp', 'N/A')}")
        print(f"   📦 Total inventory: {status.get('warehouses', {}).get('total_inventory', 'N/A')} units")
        if 'performance_metrics' in status:
            metrics = status['performance_metrics']
            print(f"   ⚡ Efficiency: {metrics.get('efficiency', 'N/A')}%")
            print(f"   🌱 Fuel saved: {metrics.get('fuel_saved', 'N/A')}L")
            print(f"   🌍 CO2 reduced: {metrics.get('co2_reduced', 'N/A')}kg")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    # 2. Route Optimization
    print("\n2️⃣ Route Optimization...")
    try:
        if hasattr(system, 'optimize_route'):
            deliveries = [
                {"name": "Plano Store", "lat": 33.0198, "lng": -96.6989, "quantity": 45, "priority": "high"},
                {"name": "Frisco Store", "lat": 33.1507, "lng": -96.8236, "quantity": 30, "priority": "medium"}
            ]
            result = system.optimize_route(1, deliveries)
        else:
            result = system.simulate_route_optimization(1)
        
        if result.get('success'):
            print("   ✅ Route optimization completed")
            route = result.get('route', result.get('optimization_result', {}))
            if isinstance(route, dict):
                print(f"   🗺️  Route: {route.get('name', 'Unnamed Route')}")
                print(f"   📏 Distance: {route.get('distance', 'N/A')} miles")
                print(f"   ⏱️  Time: {route.get('estimated_time', 'N/A')}")
            print(f"   💬 {result.get('message', 'Route optimized successfully')}")
        else:
            print(f"   ❌ Error: {result.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    # 3. Demand Forecasting
    print("\n3️⃣ Demand Forecasting...")
    try:
        if hasattr(system, 'forecast_demand'):
            result = system.forecast_demand("Dallas", 7)
        else:
            result = system.simulate_demand_forecast("Dallas")
        
        if result.get('success'):
            print("   ✅ Demand forecast completed")
            print(f"   📍 Region: {result.get('region', 'N/A')}")
            forecasts = result.get('forecasts', {})
            if isinstance(forecasts, dict):
                for product, forecast in forecasts.items():
                    if isinstance(forecast, dict):
                        demand = forecast.get('predicted_demand', 'N/A')
                        confidence = forecast.get('confidence', 'N/A')
                        print(f"   📦 {product}: {demand} units (confidence: {confidence})")
            print(f"   💬 {result.get('message', 'Forecast completed successfully')}")
        else:
            print(f"   ❌ Error: {result.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")

def main():
    """Main execution function"""
    print_banner()
    
    # Initialize system
    print("\n🔄 INITIALIZING SYSTEM...")
    try:
        # Try to use CrewAI system
        supply_chain_system = WalmartSupplyChainCrew()
        print("✅ CrewAI Multi-Agent System initialized successfully!")
    except Exception as e:
        print(f"⚠️  CrewAI not available ({str(e)}), using basic system...")
        supply_chain_system = BasicSupplyChainSystem()
        print("✅ Basic Supply Chain System initialized!")
    
    print_system_info(supply_chain_system)
    
    # Demonstrate capabilities
    demonstrate_capabilities(supply_chain_system)
    return supply_chain_system

async def run_async_demo():
    """Run async demo if available"""
    try:
        from crew import run_walmart_supply_chain_demo
        await run_walmart_supply_chain_demo()
    except ImportError:
        print("⚠️  Async demo not available, running basic demo...")
        main()

if __name__ == "__main__":
    # Check if we can run async demo
    try:
        import asyncio
        asyncio.run(run_async_demo())
    except Exception as e:
        print(f"Running basic demo: {str(e)}")
        main()
