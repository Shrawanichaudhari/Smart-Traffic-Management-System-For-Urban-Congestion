export interface Vehicle {
  type: 'car' | 'bus' | 'truck' | 'bike' | 'emergency';
  count: number;
}

export interface TrafficImpact {
  waitTime: number;
  speed: number;
  fuelConsumption: number;
  co2Emission: number;
}

export const vehicleImpacts: Record<Vehicle['type'], TrafficImpact> = {
  car: { waitTime: 1, speed: 40, fuelConsumption: 0.1, co2Emission: 0.2 },
  bus: { waitTime: 1.5, speed: 30, fuelConsumption: 0.3, co2Emission: 0.5 },
  truck: { waitTime: 2, speed: 25, fuelConsumption: 0.4, co2Emission: 0.6 },
  bike: { waitTime: 0.5, speed: 45, fuelConsumption: 0.05, co2Emission: 0.1 },
  emergency: { waitTime: 0, speed: 60, fuelConsumption: 0.15, co2Emission: 0.3 }
};