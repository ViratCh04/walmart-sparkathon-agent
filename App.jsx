import React, { useState, useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from 'react-leaflet';
import { Truck, Package, MapPin, Play, Pause, RotateCcw, Share2, Navigation, AlertCircle, CheckCircle, Clock, Zap } from 'lucide-react';
import 'leaflet/dist/leaflet.css';

// Fix for default markers in React Leaflet
import L from 'leaflet';
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// Custom truck icon
const createTruckIcon = (color = '#0071ce') => new L.DivIcon({
  html: `<div style="background: ${color}; width: 30px; height: 30px; border-radius: 50%; display: flex; align-items: center; justify-content: center; border: 3px solid white; box-shadow: 0 2px 8px rgba(0,0,0,0.3);"><i class="fas fa-truck" style="color: white; font-size: 14px;"></i></div>`,
  className: 'custom-truck-icon',
  iconSize: [30, 30],
  iconAnchor: [15, 15]
});

const createWarehouseIcon = (type = 'warehouse') => new L.DivIcon({
  html: `<div style="background: ${type === 'pickup' ? '#10b981' : '#ef4444'}; width: 25px; height: 25px; border-radius: 50%; display: flex; align-items: center; justify-content: center; border: 2px solid white; box-shadow: 0 2px 6px rgba(0,0,0,0.2);"><i class="fas fa-${type === 'pickup' ? 'plus' : 'minus'}" style="color: white; font-size: 10px;"></i></div>`,
  className: 'custom-warehouse-icon',
  iconSize: [25, 25],
  iconAnchor: [12, 12]
});

// Sample data for demo
const WAREHOUSES = [
  { id: 1, name: 'Dallas DC', lat: 32.7767, lng: -96.7970, type: 'main', inventory: 1250 },
  { id: 2, name: 'Houston DC', lat: 29.7604, lng: -95.3698, type: 'main', inventory: 890 },
  { id: 3, name: 'Austin DC', lat: 30.2672, lng: -97.7431, type: 'main', inventory: 650 },
  { id: 4, name: 'Fort Worth Hub', lat: 32.7555, lng: -97.3308, type: 'pickup', inventory: 320 },
  { id: 5, name: 'San Antonio Hub', lat: 29.4241, lng: -98.4936, type: 'delivery', inventory: 180 }
];

const INITIAL_TRUCKS = [
  {
    id: 'T001',
    driver: 'John Smith',
    capacity: 100,
    currentLoad: 0,
    lat: 32.7767,
    lng: -96.7970,
    status: 'idle',
    route: [],
    completedStops: 0,
    totalStops: 0,
    efficiency: 98.5,
    fuelSaved: 0,
    co2Reduced: 0
  },
  {
    id: 'T002',
    driver: 'Sarah Johnson',
    capacity: 120,
    currentLoad: 0,
    lat: 29.7604,
    lng: -95.3698,
    status: 'idle',
    route: [],
    completedStops: 0,
    totalStops: 0,
    efficiency: 97.2,
    fuelSaved: 0,
    co2Reduced: 0
  }
];

const SAMPLE_ROUTES = [
  {
    id: 'route1',
    name: 'North Texas Circuit',
    waypoints: [
      { lat: 32.7767, lng: -96.7970, type: 'start', name: 'Dallas DC', action: 'Load 45 units' },
      { lat: 32.7555, lng: -97.3308, type: 'pickup', name: 'Fort Worth Hub', action: 'Pickup 25 units' },
      { lat: 33.2148, lng: -97.1331, type: 'delivery', name: 'Denton Store', action: 'Deliver 30 units' },
      { lat: 32.9607, lng: -96.1039, type: 'delivery', name: 'Plano Store', action: 'Deliver 40 units' },
      { lat: 32.7767, lng: -96.7970, type: 'end', name: 'Dallas DC', action: 'Return to base' }
    ],
    distance: '156 miles',
    estimatedTime: '4h 30m',
    efficiency: 98.5,
    priority: 'high'
  },
  {
    id: 'route2',
    name: 'South Texas Loop',
    waypoints: [
      { lat: 29.7604, lng: -95.3698, type: 'start', name: 'Houston DC', action: 'Load 60 units' },
      { lat: 29.4241, lng: -98.4936, type: 'pickup', name: 'San Antonio Hub', action: 'Pickup 20 units' },
      { lat: 30.2672, lng: -97.7431, type: 'delivery', name: 'Austin DC', action: 'Deliver 35 units' },
      { lat: 29.5516, lng: -98.3271, type: 'delivery', name: 'San Antonio Store', action: 'Deliver 45 units' },
      { lat: 29.7604, lng: -95.3698, type: 'end', name: 'Houston DC', action: 'Return to base' }
    ],
    distance: '234 miles',
    estimatedTime: '6h 15m',
    efficiency: 97.2,
    priority: 'medium'
  }
];

// Animation component for moving trucks
const MovingTruck = ({ truck, route, isActive, onComplete }) => {
  const map = useMap();
  const [currentPosition, setCurrentPosition] = useState(0);
  const intervalRef = useRef();

  useEffect(() => {
    if (isActive && route.waypoints.length > 1) {
      intervalRef.current = setInterval(() => {
        setCurrentPosition(prev => {
          const next = prev + 0.02; // Speed of movement
          if (next >= route.waypoints.length - 1) {
            onComplete();
            return route.waypoints.length - 1;
          }
          return next;
        });
      }, 200);
    } else {
      clearInterval(intervalRef.current);
    }

    return () => clearInterval(intervalRef.current);
  }, [isActive, route, onComplete]);

  // Interpolate position between waypoints
  const getInterpolatedPosition = () => {
    if (route.waypoints.length < 2) return route.waypoints[0] || { lat: truck.lat, lng: truck.lng };
    
    const index = Math.floor(currentPosition);
    const fraction = currentPosition - index;
    
    if (index >= route.waypoints.length - 1) {
      return route.waypoints[route.waypoints.length - 1];
    }
    
    const current = route.waypoints[index];
    const next = route.waypoints[index + 1];
    
    return {
      lat: current.lat + (next.lat - current.lat) * fraction,
      lng: current.lng + (next.lng - current.lng) * fraction
    };
  };

  const position = getInterpolatedPosition();
  
  return (
    <Marker
      position={[position.lat, position.lng]}
      icon={createTruckIcon(isActive ? '#ef4444' : '#0071ce')}
    >
      <Popup>
        <div className="p-2">
          <h3 className="font-bold text-gray-800">{truck.id}</h3>
          <p className="text-sm text-gray-600">Driver: {truck.driver}</p>
          <p className="text-sm text-gray-600">Load: {truck.currentLoad}/{truck.capacity}</p>
          <p className="text-sm text-gray-600">Status: {truck.status}</p>
          <p className="text-sm text-gray-600">Efficiency: {truck.efficiency}%</p>
        </div>
      </Popup>
    </Marker>
  );
};

export default function WalmartTruckSimulation() {
  const [trucks, setTrucks] = useState(INITIAL_TRUCKS);
  const [selectedTruck, setSelectedTruck] = useState(null);
  const [selectedRoute, setSelectedRoute] = useState(null);
  const [isSimulating, setIsSimulating] = useState(false);
  const [simulationStats, setSimulationStats] = useState({
    totalDistance: 0,
    fuelSaved: 0,
    co2Reduced: 0,
    efficiency: 0
  });

  const startSimulation = (truckId, route) => {
    setSelectedTruck(truckId);
    setSelectedRoute(route);
    setIsSimulating(true);
    
    // Update truck status
    setTrucks(prev => prev.map(truck => 
      truck.id === truckId 
        ? { ...truck, status: 'en-route', totalStops: route.waypoints.length }
        : truck
    ));
  };

  const stopSimulation = () => {
    setIsSimulating(false);
    setTrucks(prev => prev.map(truck => ({ ...truck, status: 'idle' })));
  };

  const onRouteComplete = () => {
  setIsSimulating(false);
  setTrucks(prev => prev.map(truck => 
    truck.id === selectedTruck 
      ? { 
          ...truck, 
          status: 'completed',
          completedStops: selectedRoute.waypoints.length,
          fuelSaved: Math.round(Math.random() * 15 + 5),
          co2Reduced: Math.round(Math.random() * 50 + 20)
        }
      : truck
  ));

  setSimulationStats(prev => ({
    totalDistance: prev.totalDistance + parseInt(selectedRoute.distance.split(' ')[0]),
    fuelSaved: prev.fuelSaved + Math.round(Math.random() * 15 + 5),
    co2Reduced: prev.co2Reduced + Math.round(Math.random() * 50 + 20),
    efficiency: Math.round(Math.random() * 5 + 95)
  }));

  console.log('Simulation completed:', selectedRoute.name);
};


  const shareRoute = () => {
    if (selectedRoute) {
      const routeData = {
        name: selectedRoute.name,
        waypoints: selectedRoute.waypoints,
        distance: selectedRoute.distance,
        estimatedTime: selectedRoute.estimatedTime
      };
      
      // Simulate sharing to Google Maps
      const googleMapsUrl = `https://www.google.com/maps/dir/${selectedRoute.waypoints.map(w => `${w.lat},${w.lng}`).join('/')}`;
      navigator.clipboard.writeText(googleMapsUrl);
      alert('Route shared! Google Maps URL copied to clipboard.');
    }
  };

  const resetSimulation = () => {
    setTrucks(INITIAL_TRUCKS);
    setSelectedTruck(null);
    setSelectedRoute(null);
    setIsSimulating(false);
    setSimulationStats({
      totalDistance: 0,
      fuelSaved: 0,
      co2Reduced: 0,
      efficiency: 0
    });
  };

  return (
    <div className="flex h-screen bg-gray-900 text-white">
      {/* Sidebar */}
      <div className="w-96 bg-gray-800 border-r border-gray-700 overflow-y-auto">
        {/* Header */}
        <div className="p-6 border-b border-gray-700">
          <div className="flex items-center space-x-3 mb-4">
            <div className="w-12 h-12 bg-blue-600 rounded-lg flex items-center justify-center">
              <Truck className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-yellow-400">Walmart</h1>
              <p className="text-sm text-gray-400">Smart Logistics</p>
            </div>
          </div>
          <div className="text-xs text-gray-500">Multi-Agent Inventory Rebalancing</div>
        </div>

        {/* Simulation Stats */}
        <div className="p-4 border-b border-gray-700">
          <h3 className="text-sm font-semibold mb-3 text-gray-300">Live Performance</h3>
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-gray-700 p-3 rounded-lg">
              <div className="text-xs text-gray-400">Fuel Saved</div>
              <div className="text-lg font-bold text-green-400">{simulationStats.fuelSaved}L</div>
            </div>
            <div className="bg-gray-700 p-3 rounded-lg">
              <div className="text-xs text-gray-400">CO2 Reduced</div>
              <div className="text-lg font-bold text-green-400">{simulationStats.co2Reduced}kg</div>
            </div>
            <div className="bg-gray-700 p-3 rounded-lg">
              <div className="text-xs text-gray-400">Distance</div>
              <div className="text-lg font-bold text-blue-400">{simulationStats.totalDistance}mi</div>
            </div>
            <div className="bg-gray-700 p-3 rounded-lg">
              <div className="text-xs text-gray-400">Efficiency</div>
              <div className="text-lg font-bold text-yellow-400">{simulationStats.efficiency}%</div>
            </div>
          </div>
        </div>

        {/* Controls */}
        <div className="p-4 border-b border-gray-700">
          <div className="flex space-x-2 mb-4">
            <button
              onClick={stopSimulation}
              disabled={!isSimulating}
              className="flex-1 bg-red-600 hover:bg-red-700 disabled:bg-gray-600 px-3 py-2 rounded-lg text-sm font-medium flex items-center justify-center space-x-2"
            >
              <Pause className="w-4 h-4" />
              <span>Stop</span>
            </button>
            <button
              onClick={resetSimulation}
              className="flex-1 bg-gray-600 hover:bg-gray-700 px-3 py-2 rounded-lg text-sm font-medium flex items-center justify-center space-x-2"
            >
              <RotateCcw className="w-4 h-4" />
              <span>Reset</span>
            </button>
            <button
              onClick={shareRoute}
              disabled={!selectedRoute}
              className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 px-3 py-2 rounded-lg text-sm font-medium flex items-center justify-center space-x-2"
            >
              <Share2 className="w-4 h-4" />
              <span>Share</span>
            </button>
          </div>
        </div>

        {/* Active Trucks */}
        <div className="p-4 border-b border-gray-700">
          <h3 className="text-sm font-semibold mb-3 text-gray-300">Fleet Status</h3>
          <div className="space-y-3">
            {trucks.map(truck => (
              <div key={truck.id} className="bg-gray-700 p-3 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <Truck className="w-4 h-4 text-blue-400" />
                    <span className="font-medium">{truck.id}</span>
                  </div>
                  <div className={`px-2 py-1 rounded text-xs ${
                    truck.status === 'idle' ? 'bg-gray-600 text-gray-300' :
                    truck.status === 'en-route' ? 'bg-yellow-600 text-white' :
                    'bg-green-600 text-white'
                  }`}>
                    {truck.status}
                  </div>
                </div>
                <div className="text-xs text-gray-400 mb-2">
                  Driver: {truck.driver} | Load: {truck.currentLoad}/{truck.capacity}
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-green-400">Efficiency: {truck.efficiency}%</span>
                  <span className="text-blue-400">Fuel: {truck.fuelSaved}L saved</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Available Routes */}
        <div className="p-4">
          <h3 className="text-sm font-semibold mb-3 text-gray-300">Available Routes</h3>
          <div className="space-y-3">
            {SAMPLE_ROUTES.map(route => (
              <div key={route.id} className="bg-gray-700 p-3 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-medium text-sm">{route.name}</h4>
                  <div className={`px-2 py-1 rounded text-xs ${
                    route.priority === 'high' ? 'bg-red-600' :
                    route.priority === 'medium' ? 'bg-yellow-600' :
                    'bg-green-600'
                  }`}>
                    {route.priority}
                  </div>
                </div>
                <div className="text-xs text-gray-400 mb-3">
                  {route.distance} • {route.estimatedTime} • {route.waypoints.length} stops
                </div>
                <div className="flex space-x-2">
                  <button
                    onClick={() => startSimulation('T001', route)}
                    disabled={isSimulating}
                    className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 px-3 py-2 rounded text-xs font-medium flex items-center justify-center space-x-1"
                  >
                    <Play className="w-3 h-3" />
                    <span>T001</span>
                  </button>
                  <button
                    onClick={() => startSimulation('T002', route)}
                    disabled={isSimulating}
                    className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 px-3 py-2 rounded text-xs font-medium flex items-center justify-center space-x-1"
                  >
                    <Play className="w-3 h-3" />
                    <span>T002</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Map */}
      <div className="flex-1 relative">
        <MapContainer
          center={[31.5, -97.5]}
          zoom={7}
          style={{ height: '100%', width: '100%' }}
          className="z-0"
        >
          <TileLayer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          />
          
          {/* Warehouse markers */}
          {WAREHOUSES.map(warehouse => (
            <Marker
              key={warehouse.id}
              position={[warehouse.lat, warehouse.lng]}
              icon={createWarehouseIcon(warehouse.type)}
            >
              <Popup>
                <div className="p-2">
                  <h3 className="font-bold text-gray-800">{warehouse.name}</h3>
                  <p className="text-sm text-gray-600">Type: {warehouse.type}</p>
                  <p className="text-sm text-gray-600">Inventory: {warehouse.inventory} units</p>
                </div>
              </Popup>
            </Marker>
          ))}

          {/* Route polyline */}
          {selectedRoute && (
            <Polyline
              positions={selectedRoute.waypoints.map(w => [w.lat, w.lng])}
              color="#0071ce"
              weight={4}
              opacity={0.8}
              dashArray="10, 10"
            />
          )}

          {/* Moving trucks */}
          {trucks.map(truck => (
            <MovingTruck
              key={truck.id}
              truck={truck}
              route={selectedRoute || { waypoints: [{ lat: truck.lat, lng: truck.lng }] }}
              isActive={isSimulating && selectedTruck === truck.id}
              onComplete={onRouteComplete}
            />
          ))}
        </MapContainer>

        {/* Status overlay */}
        {isSimulating && selectedRoute && (
          <div className="absolute top-4 right-4 bg-black bg-opacity-80 p-4 rounded-lg z-10">
            <div className="flex items-center space-x-2 mb-2">
              <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
              <span className="text-sm font-medium">Simulation Active</span>
            </div>
            <div className="text-xs text-gray-300">
              Route: {selectedRoute.name}<br/>
              Truck: {selectedTruck}<br/>
              Status: Real-time tracking
            </div>
          </div>
        )}
      </div>
    </div>
  );
}