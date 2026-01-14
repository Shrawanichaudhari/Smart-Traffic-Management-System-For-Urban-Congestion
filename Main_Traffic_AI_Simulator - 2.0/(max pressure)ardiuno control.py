import random
import time
import threading
import pygame
import sys
import json
import os
import math
from datetime import datetime
from pyfirmata2 import Arduino
import queue

# Configuration parameters
defaultYellow = 2.0
minGreenTime = 5
maxGreenTime = 5
pressureCheckInterval = 1

# Screen dimensions
screenWidth = 1400
screenHeight = 800
screenSize = (screenWidth, screenHeight)

# Define phases
phases = [[0, 2], [1, 3]]
currentPhase = 0
currentYellow = 0
nextPhase = 0

signals = []
noOfSignals = 4

speeds = {'car': 2.25, 'bus': 1.8, 'truck': 1.8, 'bike': 2.5}

# Coordinates of vehicles' start
x = {'right': [0, 0, 0], 'down': [755, 727, 697], 'left': [1400, 1400, 1400], 'up': [602, 627, 657]}
y = {'right': [348, 370, 398], 'down': [0, 0, 0], 'left': [498, 466, 436], 'up': [800, 800, 800]}

vehicles = {'right': {0: [], 1: [], 2: [], 'crossed': 0}, 
            'down': {0: [], 1: [], 2: [], 'crossed': 0}, 
            'left': {0: [], 1: [], 2: [], 'crossed': 0}, 
            'up': {0: [], 1: [], 2: [], 'crossed': 0}}
vehicleTypes = {0: 'car', 1: 'bus', 2: 'truck', 3: 'bike'}
directionNumbers = {0: 'right', 1: 'down', 2: 'left', 3: 'up'}

# Coordinates of signal image, timer, and vehicle count
signalCoods = [(530, 230), (810, 230), (810, 570), (530, 570)]
signalTimerCoods = [(530, 210), (810, 210), (810, 550), (530, 550)]

# Coordinates of stop lines
stopLines = {'right': 590, 'down': 330, 'left': 800, 'up': 535}
defaultStop = {'right': 580, 'down': 320, 'left': 810, 'up': 545}

# Gap between vehicles
stoppingGap = 15
movingGap = 15

# Metrics variables
simulation_start_time = time.time()
simulation_end_time = 0
total_vehicles_passed = 0
vehicle_wait_times = []
vehicle_speeds = []
cycle_times = []
last_phase_change = time.time()
last_dashboard_update = time.time()

# Simulation control
simulation_active = True
vehicles_remaining = 0

# Arduino connection
arduino_connected = False
board = None
arduino_queue = queue.Queue()

# Define Arduino pins for traffic lights
RED_PIN_EW = 2
YELLOW_PIN_EW = 3
GREEN_PIN_EW = 4
RED_PIN_NS = 5
YELLOW_PIN_NS = 6
GREEN_PIN_NS = 7

pygame.init()
simulation = pygame.sprite.Group()

# Track which vehicles have been generated
generated_vehicles = set()
last_json_mtime = 0

class TrafficSignal:
    def __init__(self, red, yellow, green):
        self.red = red
        self.yellow = yellow
        self.green = green
        self.signalText = ""
        self.totalGreenTime = 0

# Arduino communication thread
def arduino_communication_thread():
    global arduino_connected, board
    
    print("Starting Arduino communication thread...")
    
    try:
        # Try to auto-detect Arduino
        board = Arduino(Arduino.AUTODETECT)
        time.sleep(2)  # Wait for Arduino to initialize
        arduino_connected = True
        print(f"✅ Successfully connected to Arduino on port {board.name}")
        
        # Process messages from the queue
        while simulation_active:
            try:
                # Check for new messages with a timeout
                message = arduino_queue.get(timeout=0.1)
                if message == "UPDATE_LIGHTS":
                    update_arduino_lights()
                elif message == "SHUTDOWN":
                    break
            except queue.Empty:
                # No message in queue, continue
                continue
            except Exception as e:
                print(f"Error in Arduino communication: {e}")
                
    except Exception as e:
        print(f"❌ Failed to connect to Arduino: {e}")
        arduino_connected = False
    
    # Clean up
    if arduino_connected:
        try:
            # Turn off all lights
            board.digital[RED_PIN_EW].write(0)
            board.digital[YELLOW_PIN_EW].write(0)
            board.digital[GREEN_PIN_EW].write(0)
            board.digital[RED_PIN_NS].write(0)
            board.digital[YELLOW_PIN_NS].write(0)
            board.digital[GREEN_PIN_NS].write(0)
            board.exit()
        except:
            pass
    
    print("Arduino communication thread stopped")

# Function to update Arduino lights
def update_arduino_lights():
    global arduino_connected, board
    
    if not arduino_connected:
        return
    
    try:
        # Turn off all lights first
        board.digital[RED_PIN_EW].write(0)
        board.digital[YELLOW_PIN_EW].write(0)
        board.digital[GREEN_PIN_EW].write(0)
        board.digital[RED_PIN_NS].write(0)
        board.digital[YELLOW_PIN_NS].write(0)
        board.digital[GREEN_PIN_NS].write(0)
        
        # Set lights based on current phase and yellow state
        if currentYellow == 1:
            # Yellow phase - set the active system to yellow, other to red
            if currentPhase == 0:  # East-West yellow
                board.digital[YELLOW_PIN_EW].write(1)
                board.digital[RED_PIN_NS].write(1)
            else:  # North-South yellow
                board.digital[YELLOW_PIN_NS].write(1)
                board.digital[RED_PIN_EW].write(1)
        else:
            # Green phase - set the active system to green, other to red
            if currentPhase == 0:  # East-West green
                board.digital[GREEN_PIN_EW].write(1)
                board.digital[RED_PIN_NS].write(1)
            else:  # North-South green
                board.digital[GREEN_PIN_NS].write(1)
                board.digital[RED_PIN_EW].write(1)
                
        print(f"Updated Arduino lights: Phase {currentPhase}, Yellow {currentYellow}")
        
    except Exception as e:
        print(f"Error updating Arduino lights: {e}")
        arduino_connected = False

# Function to send signal states to Arduino
def send_to_arduino():
    if arduino_connected:
        try:
            arduino_queue.put("UPDATE_LIGHTS")
        except:
            pass

# Function to check if a direction has green light
def is_green(direction_number):
    if currentYellow == 1:
        return False
    return direction_number in phases[currentPhase]

# Function to generate dashboard JSON
def generate_dashboard_json():
    """Generate the dashboard JSON with current simulation data"""
    
    # Map direction numbers to names
    direction_map = {0: "east", 1: "south", 2: "west", 3: "north"}
    
    # Calculate phase information
    if currentYellow == 1:
        phase_status = "YELLOW"
    else:
        phase_status = "GREEN"
    
    # Get active directions based on current phase
    active_directions = []
    for dir_num in phases[currentPhase]:
        active_directions.append(direction_map[dir_num])
    
    # Calculate direction metrics
    direction_metrics = {}
    for dir_num, dir_name in direction_map.items():
        direction = directionNumbers[dir_num]
        
        # Count vehicles by type
        vehicle_counts = {"car": 0, 'bus': 0, 'truck': 0, 'bike': 0}
        queue_length = 0
        vehicles_crossed = vehicles[direction]['crossed']
        
        for lane in [0, 1, 2]:
            for vehicle in vehicles[direction][lane]:
                if not vehicle.crossed:
                    vehicle_counts[vehicle.vehicleClass] += 1
                    if vehicle.waiting:
                        queue_length += 1
        
        # Calculate average wait time for this direction
        wait_times = []
        for lane in [0, 1, 2]:
            for vehicle in vehicles[direction][lane]:
                if vehicle.crossed:
                    wait_times.append(vehicle.total_wait_time)
        
        avg_wait_time = sum(wait_times) / len(wait_times) if wait_times else 0
        
        direction_metrics[dir_name] = {
            "vehicle_counts": vehicle_counts,
            "queue_length": queue_length,
            "vehicles_crossed": vehicles_crossed,
            "avg_wait_time": round(avg_wait_time, 1),
            "emergency_vehicle_present": False
        }
    
    # Calculate overall metrics
    elapsed_time = time.time() - simulation_start_time
    throughput = (total_vehicles_passed / elapsed_time) * 60 if elapsed_time > 0 else 0
    
    avg_wait_time_all = sum(vehicle_wait_times) / len(vehicle_wait_times) if vehicle_wait_times else 0
    avg_speed = sum(vehicle_speeds) / len(vehicle_speeds) if vehicle_speeds else 0
    
    # For cycle time, we can use the time since last phase change
    cycle_time = time.time() - last_phase_change
    
    # Get remaining time for current phase
    if currentYellow == 1:
        remaining_time = signals[phases[currentPhase][0]].yellow
    else:
        remaining_time = signals[phases[currentPhase][0]].green
    
    dashboard_data = {
        "simulation_id": "SIM_001",
        "timestamp": datetime.now().isoformat() + "Z",
        "intersection_id": "INT_001",
        "current_phase": {
            "phase_id": currentPhase,
            "active_directions": active_directions,
            "status": phase_status,
            "remaining_time": remaining_time
        },
        "direction_metrics": direction_metrics,
        "overall_metrics": {
            "total_vehicles_passed": total_vehicles_passed,
            "avg_wait_time_all_sides": round(avg_wait_time_all, 1),
            "throughput": round(throughput, 2),
            "avg_speed": round(avg_speed, 1),
            "cycle_time": round(cycle_time, 1)
        }
    }
    
    return dashboard_data

def send_to_dashboard():
    """Generate and send the dashboard JSON"""
    global last_dashboard_update
    
    dashboard_data = generate_dashboard_json()
    
    # Write to a file that can be read by the dashboard
    with open('dashboard_data.json', 'w') as f:
        json.dump(dashboard_data, f, indent=2)
    
    # Also send to Arduino if connected
    send_to_arduino()
    
    last_dashboard_update = time.time()
    print(f"Dashboard data updated at {datetime.now().isoformat()}")
        
class Vehicle(pygame.sprite.Sprite):
    def __init__(self, lane, vehicleClass, direction_number, direction, vehicle_id):
        pygame.sprite.Sprite.__init__(self)
        self.lane = lane
        self.vehicleClass = vehicleClass
        self.speed = speeds[vehicleClass]
        self.direction_number = direction_number
        self.direction = direction
        self.x = x[direction][lane]
        self.y = y[direction][lane]
        self.crossed = 0
        self.vehicle_id = vehicle_id
        self.waiting = True
        self.creation_time = time.time()
        self.wait_start_time = time.time()
        self.total_wait_time = 0
        vehicles[direction][lane].append(self)
        self.index = len(vehicles[direction][lane]) - 1
        path = "images/" + direction + "/" + vehicleClass + ".png"
        self.image = pygame.image.load(path)

        if len(vehicles[direction][lane]) > 1 and vehicles[direction][lane][self.index-1].crossed == 0:
            if direction == 'right':
                self.stop = vehicles[direction][lane][self.index-1].stop - vehicles[direction][lane][self.index-1].image.get_rect().width - stoppingGap
            elif direction == 'left':
                self.stop = vehicles[direction][lane][self.index-1].stop + vehicles[direction][lane][self.index-1].image.get_rect().width + stoppingGap
            elif direction == 'down':
                self.stop = vehicles[direction][lane][self.index-1].stop - vehicles[direction][lane][self.index-1].image.get_rect().height - stoppingGap
            elif direction == 'up':
                self.stop = vehicles[direction][lane][self.index-1].stop + vehicles[direction][lane][self.index-1].image.get_rect().height + stoppingGap
        else:
            self.stop = defaultStop[direction]
            
        # Set new starting and stopping coordinate
        if direction == 'right':
            temp = self.image.get_rect().width + stoppingGap    
            x[direction][lane] -= temp
        elif direction == 'left':
            temp = self.image.get_rect().width + stoppingGap
            x[direction][lane] += temp
        elif direction == 'down':
            temp = self.image.get_rect().height + stoppingGap
            y[direction][lane] -= temp
        elif direction == 'up':
            temp = self.image.get_rect().height + stoppingGap
            y[direction][lane] += temp
            
        # Update vehicles remaining count
        global vehicles_remaining
        vehicles_remaining += 1
        
        simulation.add(self)

    def render(self, screen):
        screen.blit(self.image, (self.x, self.y))

    def move(self):
        global total_vehicles_passed, vehicle_wait_times, vehicle_speeds, vehicles_remaining, simulation_active, simulation_end_time
        
        if self.direction == 'right':
            if self.crossed == 0 and self.x + self.image.get_rect().width > stopLines[self.direction]:
                self.crossed = 1
                self.waiting = False
                total_vehicles_passed += 1
                vehicles_remaining -= 1
                vehicle_wait_times.append(time.time() - self.creation_time)
                vehicle_speeds.append(self.speed)
                
                if vehicles_remaining == 0 and simulation_active:
                    simulation_active = False
                    simulation_end_time = time.time()
                    print("All vehicles have crossed. Metrics paused.")
            if ((self.x + self.image.get_rect().width <= self.stop or self.crossed == 1 or 
                 is_green(self.direction_number)) and 
                (self.index == 0 or self.x + self.image.get_rect().width < 
                 (vehicles[self.direction][self.lane][self.index-1].x - movingGap))):
                self.x += self.speed
                if self.x + self.image.get_rect().width < stopLines[self.direction]:
                    self.waiting = True
        elif self.direction == 'down':
            if self.crossed == 0 and self.y + self.image.get_rect().height > stopLines[self.direction]:
                self.crossed = 1
                self.waiting = False
                total_vehicles_passed += 1
                vehicles_remaining -= 1
                vehicle_wait_times.append(time.time() - self.creation_time)
                vehicle_speeds.append(self.speed)
                
                if vehicles_remaining == 0 and simulation_active:
                    simulation_active = False
                    simulation_end_time = time.time()
                    print("All vehicles have crossed. Metrics paused.")
            if ((self.y + self.image.get_rect().height <= self.stop or self.crossed == 1 or 
                 is_green(self.direction_number)) and 
                (self.index == 0 or self.y + self.image.get_rect().height < 
                 (vehicles[self.direction][self.lane][self.index-1].y - movingGap))):
                self.y += self.speed
                if self.y + self.image.get_rect().height < stopLines[self.direction]:
                    self.waiting = True
        elif self.direction == 'left':
            if self.crossed == 0 and self.x < stopLines[self.direction]:
                self.crossed = 1
                self.waiting = False
                total_vehicles_passed += 1
                vehicles_remaining -= 1
                vehicle_wait_times.append(time.time() - self.creation_time)
                vehicle_speeds.append(self.speed)
                
                if vehicles_remaining == 0 and simulation_active:
                    simulation_active = False
                    simulation_end_time = time.time()
                    print("All vehicles have crossed. Metrics paused.")
            if ((self.x >= self.stop or self.crossed == 1 or 
                 is_green(self.direction_number)) and 
                (self.index == 0 or self.x > 
                 (vehicles[self.direction][self.lane][self.index-1].x + 
                  vehicles[self.direction][self.lane][self.index-1].image.get_rect().width + movingGap))):
                self.x -= self.speed
                if self.x > stopLines[self.direction]:
                    self.waiting = True
        elif self.direction == 'up':
            if self.crossed == 0 and self.y < stopLines[self.direction]:
                self.crossed = 1
                self.waiting = False
                total_vehicles_passed += 1
                vehicles_remaining -= 1
                vehicle_wait_times.append(time.time() - self.creation_time)
                vehicle_speeds.append(self.speed)
                
                if vehicles_remaining == 0 and simulation_active:
                    simulation_active = False
                    simulation_end_time = time.time()
                    print("All vehicles have crossed. Metrics paused.")
            if ((self.y >= self.stop or self.crossed == 1 or 
                 is_green(self.direction_number)) and 
                (self.index == 0 or self.y > 
                 (vehicles[self.direction][self.lane][self.index-1].y + 
                  vehicles[self.direction][self.lane][self.index-1].image.get_rect().height + movingGap))):
                self.y -= self.speed
                if self.y > stopLines[self.direction]:
                    self.waiting = True
        
        # Update wait time calculation
        if self.waiting:
            self.total_wait_time = time.time() - self.wait_start_time
        else:
            self.wait_start_time = time.time()

# Function to calculate pressure for each approach
def calculate_pressures():
    pressures = [0] * noOfSignals
    
    for i, direction in enumerate(['right', 'down', 'left', 'up']):
        for lane in [0, 1, 2]:
            for vehicle in vehicles[direction][lane]:
                if vehicle.waiting:
                    pressures[i] += 1
                    
    return pressures

# Function to calculate metrics
def calculate_metrics():
    global cycle_times, last_phase_change
    
    if simulation_active:
        current_time = time.time()
    else:
        current_time = simulation_end_time
    
    elapsed_time = current_time - simulation_start_time
    avg_wait_time = sum(vehicle_wait_times) / len(vehicle_wait_times) if vehicle_wait_times else 0
    throughput = (total_vehicles_passed / elapsed_time) * 60 if elapsed_time > 0 else 0
    avg_speed = sum(vehicle_speeds) / len(vehicle_speeds) if vehicle_speeds else 0
    
    if simulation_active:
        cycle_time = time.time() - last_phase_change
    else:
        cycle_time = simulation_end_time - last_phase_change
    
    return {
        "total_vehicles_passed": total_vehicles_passed,
        "avg_wait_time": avg_wait_time,
        "throughput": throughput,
        "avg_speed": avg_speed,
        "cycle_time": cycle_time,
        "elapsed_time": elapsed_time,
        "vehicles_remaining": vehicles_remaining
    }

# Function to display metrics on the screen
def display_metrics(screen, metrics):
    # Create a more beautiful metrics display
    panel_width = 420
    panel_height = 315  # Reduced height since Arduino status removed
    panel_x = 20  # Position on the top left
    panel_y = 20

    # Create gradient background with decreased transparency (more opaque)
    metrics_bg = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
    for i in range(panel_height):
        alpha = 240 - (i * 60 // panel_height)  # Gradient from dark to lighter (less transparent)
        pygame.draw.line(metrics_bg, (20, 20, 30, max(220, alpha)), (0, i), (panel_width, i))  # Increased min alpha from 200 to 220

    # Add border with glow effect
    border_color = (0, 255, 150) if simulation_active else (255, 100, 100)
    pygame.draw.rect(metrics_bg, border_color, (0, 0, panel_width, panel_height), 2)
    pygame.draw.rect(metrics_bg, (255, 255, 255, 50), (2, 2, panel_width-4, panel_height-4), 1)

    screen.blit(metrics_bg, (panel_x, panel_y))

    # Fonts with increased sizes
    title_font = pygame.font.Font(None, 28)
    header_font = pygame.font.Font(None, 26)
    normal_font = pygame.font.Font(None, 26)
    small_font = pygame.font.Font(None, 22)

    # Title
    title_text = title_font.render("MAX PRESSURE METRICS", True, (0, 255, 200))
    screen.blit(title_text, (panel_x + 20, panel_y + 15))

    # Status indicator with animation
    status = "RUNNING" if simulation_active else "COMPLETED"
    status_color = (50, 255, 100) if simulation_active else (255, 150, 50)

    # Animated status dot
    import math
    pulse = (math.sin(time.time() * 4) + 1) / 2  # 0 to 1
    dot_brightness = int(100 + pulse * 155)
    pygame.draw.circle(screen, (dot_brightness, dot_brightness, dot_brightness),
                      (panel_x + 25, panel_y + 55), 6)

    status_text = header_font.render(f"Status: {status}", True, status_color)
    screen.blit(status_text, (panel_x + 45, panel_y + 45))

    # Metrics with colors and icons (starting higher since Arduino status removed)
    y_pos = panel_y + 75
    metrics_config = [
        ("elapsed_time", "Timer", f"{metrics['elapsed_time']:.1f}s", (255, 255, 100)),
        ("total_vehicles_passed", "Total Vehicles", str(metrics["total_vehicles_passed"]), (100, 200, 255)),
        ("avg_wait_time", "Avg Wait Time", f"{metrics['avg_wait_time']:.1f}s", (255, 150, 100)),
        ("throughput", "Throughput", f"{metrics['throughput']:.1f} veh/min", (150, 255, 150)),
        ("avg_speed", "Avg Speed", f"{metrics['avg_speed']:.1f} px/s", (200, 150, 255)),
        ("cycle_time", "Cycle Time", f"{metrics['cycle_time']:.1f}s", (255, 200, 150)),
        ("vehicles_remaining", "Remaining", str(metrics["vehicles_remaining"]), (255, 100, 150))
    ]

    for key, icon_label, value_text, color in metrics_config:
        # Background for each metric
        row_bg = pygame.Surface((panel_width - 40, 30), pygame.SRCALPHA)
        row_bg.fill((50, 50, 60, 80))
        screen.blit(row_bg, (panel_x + 20, y_pos - 2))

        # Icon and label
        label_text = small_font.render(f"{icon_label}:", True, (200, 200, 220))
        screen.blit(label_text, (panel_x + 25, y_pos + 2))

        # Value with color
        value_render = normal_font.render(value_text, True, color)
        value_width = value_render.get_width()
        screen.blit(value_render, (panel_x + panel_width - value_width - 25, y_pos + 2))

        y_pos += 35

    # Add a subtle animation effect for active simulation
    if simulation_active:
        # Subtle glow effect around the panel
        glow_surface = pygame.Surface((panel_width + 20, panel_height + 20), pygame.SRCALPHA)
        glow_alpha = int(30 + pulse * 20)
        pygame.draw.rect(glow_surface, (0, 255, 150, glow_alpha),
                        (0, 0, panel_width + 20, panel_height + 20), 3)
        screen.blit(glow_surface, (panel_x - 10, panel_y - 10))

    # Display Arduino status separately at bottom right corner
    arduino_status = "Connected" if arduino_connected else "Disconnected"
    arduino_color = (50, 255, 100) if arduino_connected else (255, 100, 100)
    arduino_font = pygame.font.Font(None, 24)

    # Create background for Arduino status
    arduino_bg = pygame.Surface((200, 40), pygame.SRCALPHA)
    arduino_bg.fill((20, 20, 30, 220))  # Semi-transparent background
    pygame.draw.rect(arduino_bg, arduino_color, (0, 0, 200, 40), 2)

    arduino_x = screenWidth - 220  # Bottom right corner
    arduino_y = screenHeight - 60

    screen.blit(arduino_bg, (arduino_x, arduino_y))
    arduino_text = arduino_font.render(f"Arduino: {arduino_status}", True, arduino_color)
    screen.blit(arduino_text, (arduino_x + 10, arduino_y + 8))

# MaxPressure algorithm implementation with phases
def max_pressure_algorithm():
    global currentPhase, currentYellow, nextPhase, last_phase_change, cycle_times
    
    # Initialize signals
    for i in range(noOfSignals):
        signals.append(TrafficSignal(0, defaultYellow, 0))
    
    # Start with phase 0 (East-West: right and left)
    currentPhase = 0
    for dir_index in phases[currentPhase]:
        signals[dir_index].green = minGreenTime
    green_start_time = time.time()
    last_phase_change = green_start_time
    
    # Send initial dashboard data
    send_to_dashboard()
    
    while simulation_active:
        # Handle yellow phase
        if currentYellow == 1:
            time.sleep(1)
            for dir_index in phases[currentPhase]:
                signals[dir_index].yellow -= 1
            
            if time.time() - last_dashboard_update > 1:
                send_to_dashboard()
            
            if all(signals[dir_index].yellow <= 0 for dir_index in phases[currentPhase]):
                currentYellow = 0
                currentPhase = nextPhase
                for dir_index in phases[currentPhase]:
                    signals[dir_index].green = minGreenTime
                green_start_time = time.time()
                last_phase_change = green_start_time
                cycle_times.append(time.time() - last_phase_change)
                send_to_dashboard()
            continue
        
        # Handle green phase
        elapsed_green = time.time() - green_start_time
        for dir_index in phases[currentPhase]:
            signals[dir_index].green = max(0, minGreenTime - int(elapsed_green))
        
        if time.time() - last_dashboard_update > 1:
            send_to_dashboard()
        
        if elapsed_green >= pressureCheckInterval:
            pressures = calculate_pressures()
            
            phase_pressures = [
                pressures[0] + pressures[2],  # Phase 0: right + left
                pressures[1] + pressures[3]   # Phase 1: down + up
            ]
            
            max_pressure = -1
            candidate_phase = currentPhase
            
            for i, pressure in enumerate(phase_pressures):
                if pressure > max_pressure:
                    max_pressure = pressure
                    candidate_phase = i
            
            if (elapsed_green >= minGreenTime and candidate_phase != currentPhase and 
                phase_pressures[candidate_phase] > phase_pressures[currentPhase]):
                currentYellow = 1
                for dir_index in phases[currentPhase]:
                    signals[dir_index].yellow = defaultYellow
                nextPhase = candidate_phase
                cycle_times.append(time.time() - last_phase_change)
                last_phase_change = time.time()
                send_to_dashboard()
            
            elif elapsed_green >= maxGreenTime:
                currentYellow = 1
                for dir_index in phases[currentPhase]:
                    signals[dir_index].yellow = defaultYellow
                nextPhase = candidate_phase
                cycle_times.append(time.time() - last_phase_change)
                last_phase_change = time.time()
                send_to_dashboard()
        
        time.sleep(0.1)

# Function to read vehicle counts from JSON file
def read_vehicle_counts(filename='vehicle_counts.json'):
    try:
        with open(filename, 'r') as f:
            vehicle_counts = json.load(f)
        return vehicle_counts
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
        return None

# Function to generate vehicles based on JSON data
def generate_vehicles_from_json():
    global generated_vehicles, last_json_mtime
    
    filename = 'vehicle_counts.json'
    
    if not os.path.exists(filename):
        return
    
    current_mtime = os.path.getmtime(filename)
    if current_mtime <= last_json_mtime:
        return
    
    last_json_mtime = current_mtime
    
    vehicle_counts = read_vehicle_counts(filename)
    if not vehicle_counts:
        return
    
    direction_mapping = {'right': 0, 'down': 1, 'left': 2, 'up': 3}
    batch_id = int(time.time())
    
    for direction, vehicles_data in vehicle_counts.items():
        for vehicle_type, count in vehicles_data.items():
            for i in range(count):
                vehicle_id = f"{batch_id}{direction}{vehicle_type}_{i}"
                
                if vehicle_id in generated_vehicles:
                    continue
                
                lane = random.randint(0, 2)
                direction_number = direction_mapping[direction]
                Vehicle(lane, vehicle_type, direction_number, direction, vehicle_id)
                generated_vehicles.add(vehicle_id)
                time.sleep(0.1)

# Thread function to periodically check for new vehicles
def vehicle_generation_thread():
    while simulation_active:
        generate_vehicles_from_json()
        time.sleep(2)

class Main:
    def __init__(self):
        # Start Arduino communication thread
        self.arduino_thread = threading.Thread(target=arduino_communication_thread)
        self.arduino_thread.daemon = True
        self.arduino_thread.start()
        
        # Wait a moment for Arduino to connect
        time.sleep(3)
        
        # Start MaxPressure algorithm thread
        self.algorithm_thread = threading.Thread(target=max_pressure_algorithm)
        self.algorithm_thread.daemon = True
        self.algorithm_thread.start()

        # Start vehicle generation thread
        self.vehicle_thread = threading.Thread(target=vehicle_generation_thread)
        self.vehicle_thread.daemon = True
        self.vehicle_thread.start()

        self.run_simulation()

    def run_simulation(self):
        # Colors 
        black = (0, 0, 0)
        white = (255, 255, 255)

        # Setting background image i.e. image of intersection
        background = pygame.image.load('images/intersection.png')

        screen = pygame.display.set_mode(screenSize)
        pygame.display.set_caption("SIMULATION with MaxPressure Algorithm and Arduino Integration")

        # Loading signal images and font
        redSignal = pygame.image.load('images/signals/red.png')
        yellowSignal = pygame.image.load('images/signals/yellow.png')
        greenSignal = pygame.image.load('images/signals/green.png')
        font = pygame.font.Font(None, 30)

        clock = pygame.time.Clock()
        
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    global simulation_active
                    simulation_active = False
                    
                    # Signal Arduino thread to shutdown
                    try:
                        arduino_queue.put("SHUTDOWN")
                    except:
                        pass
                    
                    # Wait for threads to finish
                    self.algorithm_thread.join(1.0)
                    self.vehicle_thread.join(1.0)
                    self.arduino_thread.join(2.0)
                    
                    pygame.quit()
                    sys.exit()

            screen.blit(background, (0, 0))
            
            # Display signals based on current phase
            for i in range(noOfSignals):
                if i in phases[currentPhase]:
                    if currentYellow == 1:
                        signals[i].signalText = signals[i].yellow
                        screen.blit(yellowSignal, signalCoods[i])
                    else:
                        signals[i].signalText = signals[i].green
                        screen.blit(greenSignal, signalCoods[i])
                else:
                    signals[i].signalText = "---"
                    screen.blit(redSignal, signalCoods[i])
            
            # Display signal timer or pressure information
            signalTexts = ["", "", "", ""]
            pressures = calculate_pressures()
            
            for i in range(noOfSignals):
                if i in phases[currentPhase]:
                    if currentYellow == 1:
                        text = f"Y:{signals[i].yellow}"
                    else:
                        text = f"G:{signals[i].green}"
                else:
                    text = f"P:{pressures[i]}"
                
                signalTexts[i] = font.render(text, True, white, black)
                screen.blit(signalTexts[i], signalTimerCoods[i])

            # Display the vehicles
            for vehicle in simulation:  
                screen.blit(vehicle.image, [vehicle.x, vehicle.y])
                vehicle.move()
            
            # Calculate and display metrics
            metrics = calculate_metrics()
            display_metrics(screen, metrics)
            
            pygame.display.update()
            clock.tick(30)  # Limit to 30 frames per second

if __name__ == "__main__":
    Main()