import random
import time
import threading
import pygame
import sys
import json
import os
from datetime import datetime

# Default values of signal timers
defaultGreen = {0:10, 1:10, 2:10, 3:10}
defaultRed = 150
defaultYellow = 5

signals = []
noOfSignals = 4
currentGreen = 0
nextGreen = (currentGreen+1)%noOfSignals
currentYellow = 0

speeds = {'car':2.25, 'bus':1.8, 'truck':1.8, 'bike':2.5}

# Coordinates of vehicles' start
x = {'right':[0,0,0], 'down':[755,727,697], 'left':[1400,1400,1400], 'up':[602,627,657]}    
y = {'right':[348,370,398], 'down':[0,0,0], 'left':[498,466,436], 'up':[800,800,800]}

vehicles = {'right': {0:[], 1:[], 2:[], 'crossed':0}, 'down': {0:[], 1:[], 2:[], 'crossed':0}, 'left': {0:[], 1:[], 2:[], 'crossed':0}, 'up': {0:[], 1:[], 2:[], 'crossed':0}}
vehicleTypes = {0:'car', 1:'bus', 2:'truck', 3:'bike'}
directionNumbers = {0:'right', 1:'down', 2:'left', 3:'up'}

# Coordinates of signal image, timer, and vehicle count
signalCoods = [(530,230),(810,230),(810,570),(530,570)]
signalTimerCoods = [(530,210),(810,210),(810,550),(530,550)]

# Coordinates of stop lines
stopLines = {'right': 590, 'down': 330, 'left': 800, 'up': 535}
defaultStop = {'right': 580, 'down': 320, 'left': 810, 'up': 545}

# Gap between vehicles
stoppingGap = 15
movingGap = 15

# Screen dimensions
screenWidth = 1400
screenHeight = 800
screenSize = (screenWidth, screenHeight)

# Metrics variables
simulation_start_time = time.time()
simulation_end_time = 0
total_vehicles_passed = 0
vehicle_wait_times = []
vehicle_speeds = []
simulation_active = True
vehicles_remaining = 0

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
        self.creation_time = time.time()
        self.waiting = True
        vehicles[direction][lane].append(self)
        self.index = len(vehicles[direction][lane]) - 1
        path = "images/" + direction + "/" + vehicleClass + ".png"
        self.image = pygame.image.load(path)

        # Update vehicles remaining count
        global vehicles_remaining
        vehicles_remaining += 1

        if(len(vehicles[direction][lane])>1 and vehicles[direction][lane][self.index-1].crossed==0):
            if(direction=='right'):
                self.stop = vehicles[direction][lane][self.index-1].stop - vehicles[direction][lane][self.index-1].image.get_rect().width - stoppingGap
            elif(direction=='left'):
                self.stop = vehicles[direction][lane][self.index-1].stop + vehicles[direction][lane][self.index-1].image.get_rect().width + stoppingGap
            elif(direction=='down'):
                self.stop = vehicles[direction][lane][self.index-1].stop - vehicles[direction][lane][self.index-1].image.get_rect().height - stoppingGap
            elif(direction=='up'):
                self.stop = vehicles[direction][lane][self.index-1].stop + vehicles[direction][lane][self.index-1].image.get_rect().height + stoppingGap
        else:
            self.stop = defaultStop[direction]
            
        # Set new starting and stopping coordinate
        if(direction=='right'):
            temp = self.image.get_rect().width + stoppingGap    
            x[direction][lane] -= temp
        elif(direction=='left'):
            temp = self.image.get_rect().width + stoppingGap
            x[direction][lane] += temp
        elif(direction=='down'):
            temp = self.image.get_rect().height + stoppingGap
            y[direction][lane] -= temp
        elif(direction=='up'):
            temp = self.image.get_rect().height + stoppingGap
            y[direction][lane] += temp
        simulation.add(self)

    def render(self, screen):
        screen.blit(self.image, (self.x, self.y))

    def move(self):
        global total_vehicles_passed, vehicle_wait_times, vehicle_speeds, vehicles_remaining, simulation_active, simulation_end_time
        
        if(self.direction=='right'):
            if(self.crossed==0 and self.x+self.image.get_rect().width>stopLines[self.direction]):
                self.crossed = 1
                total_vehicles_passed += 1
                vehicles_remaining -= 1
                vehicle_wait_times.append(time.time() - self.creation_time)
                vehicle_speeds.append(self.speed)
                
                # Check if this was the last vehicle
                if vehicles_remaining == 0 and simulation_active:
                    simulation_active = False
                    simulation_end_time = time.time()
                    print("All vehicles have crossed. Metrics paused.")
            if((self.x+self.image.get_rect().width<=self.stop or self.crossed == 1 or (currentGreen==0 and currentYellow==0)) and (self.index==0 or self.x+self.image.get_rect().width<(vehicles[self.direction][self.lane][self.index-1].x - movingGap))):                
                self.x += self.speed
        elif(self.direction=='down'):
            if(self.crossed==0 and self.y+self.image.get_rect().height>stopLines[self.direction]):
                self.crossed = 1
                total_vehicles_passed += 1
                vehicles_remaining -= 1
                vehicle_wait_times.append(time.time() - self.creation_time)
                vehicle_speeds.append(self.speed)
                
                # Check if this was the last vehicle
                if vehicles_remaining == 0 and simulation_active:
                    simulation_active = False
                    simulation_end_time = time.time()
                    print("All vehicles have crossed. Metrics paused.")
            if((self.y+self.image.get_rect().height<=self.stop or self.crossed == 1 or (currentGreen==1 and currentYellow==0)) and (self.index==0 or self.y+self.image.get_rect().height<(vehicles[self.direction][self.lane][self.index-1].y - movingGap))):                
                self.y += self.speed
        elif(self.direction=='left'):
            if(self.crossed==0 and self.x<stopLines[self.direction]):
                self.crossed = 1
                total_vehicles_passed += 1
                vehicles_remaining -= 1
                vehicle_wait_times.append(time.time() - self.creation_time)
                vehicle_speeds.append(self.speed)
                
                # Check if this was the last vehicle
                if vehicles_remaining == 0 and simulation_active:
                    simulation_active = False
                    simulation_end_time = time.time()
                    print("All vehicles have crossed. Metrics paused.")
            if((self.x>=self.stop or self.crossed == 1 or (currentGreen==2 and currentYellow==0)) and (self.index==0 or self.x>(vehicles[self.direction][self.lane][self.index-1].x + vehicles[self.direction][self.lane][self.index-1].image.get_rect().width + movingGap))):                
                self.x -= self.speed   
        elif(self.direction=='up'):
            if(self.crossed==0 and self.y<stopLines[self.direction]):
                self.crossed = 1
                total_vehicles_passed += 1
                vehicles_remaining -= 1
                vehicle_wait_times.append(time.time() - self.creation_time)
                vehicle_speeds.append(self.speed)
                
                # Check if this was the last vehicle
                if vehicles_remaining == 0 and simulation_active:
                    simulation_active = False
                    simulation_end_time = time.time()
                    print("All vehicles have crossed. Metrics paused.")
            if((self.y>=self.stop or self.crossed == 1 or (currentGreen==3 and currentYellow==0)) and (self.index==0 or self.y>(vehicles[self.direction][self.lane][self.index-1].y + vehicles[self.direction][self.lane][self.index-1].image.get_rect().height + movingGap))):                
                self.y -= self.speed

# Function to calculate metrics
def calculate_metrics():
    # Use appropriate time based on simulation state
    if simulation_active:
        current_time = time.time()
    else:
        current_time = simulation_end_time
    
    elapsed_time = current_time - simulation_start_time
    
    # Calculate average wait time
    avg_wait_time = sum(vehicle_wait_times) / len(vehicle_wait_times) if vehicle_wait_times else 0
    
    # Calculate throughput (vehicles per minute)
    throughput = (total_vehicles_passed / elapsed_time) * 60 if elapsed_time > 0 else 0
    
    # Calculate average speed
    avg_speed = sum(vehicle_speeds) / len(vehicle_speeds) if vehicle_speeds else 0
    
    return {
        "total_vehicles_passed": total_vehicles_passed,
        "avg_wait_time": avg_wait_time,
        "throughput": throughput,
        "avg_speed": avg_speed,
        "elapsed_time": elapsed_time,
        "vehicles_remaining": vehicles_remaining
    }

# Function to display metrics on the screen
def display_metrics(screen, metrics):
    # Create a more beautiful metrics display
    panel_width = 420
    panel_height = 280
    panel_x = 20  # Moved to top left
    panel_y = 20

    # Create gradient background
    metrics_bg = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
    for i in range(panel_height):
        alpha = 240 - (i * 60 // panel_height)  # Gradient from dark to lighter (less transparent)
        pygame.draw.line(metrics_bg, (20, 20, 30, max(200, alpha)), (0, i), (panel_width, i))

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
    title_text = title_font.render("TRAFFIC METRICS", True, (0, 255, 200))
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

    # Metrics with colors and icons
    y_pos = panel_y + 85
    metrics_config = [
        ("elapsed_time", "Timer", f"{metrics['elapsed_time']:.1f}s", (255, 255, 100)),
        ("total_vehicles_passed", "Total Vehicles", str(metrics["total_vehicles_passed"]), (100, 200, 255)),
        ("avg_wait_time", "Avg Wait Time", f"{metrics['avg_wait_time']:.1f}s", (255, 150, 100)),
        ("throughput", "Throughput", f"{metrics['throughput']:.1f} veh/min", (150, 255, 150)),
        ("avg_speed", "Avg Speed", f"{metrics['avg_speed']:.1f} px/s", (200, 150, 255)),
        ("vehicles_remaining", "Remaining Vehicles", str(metrics["vehicles_remaining"]), (255, 100, 150))
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

# Initialization of signals with default values
def initialize():
    ts1 = TrafficSignal(0, defaultYellow, defaultGreen[0])
    signals.append(ts1)
    ts2 = TrafficSignal(ts1.red+ts1.yellow+ts1.green, defaultYellow, defaultGreen[1])
    signals.append(ts2)
    ts3 = TrafficSignal(defaultRed, defaultYellow, defaultGreen[2])
    signals.append(ts3)
    ts4 = TrafficSignal(defaultRed, defaultYellow, defaultGreen[3])
    signals.append(ts4)
    repeat()

def repeat():
    global currentGreen, currentYellow, nextGreen
    while(signals[currentGreen].green>0 and simulation_active):
        updateValues()
        time.sleep(1)
    if not simulation_active:
        return
        
    currentYellow = 1
    for i in range(0,3):
        for vehicle in vehicles[directionNumbers[currentGreen]][i]:
            vehicle.stop = defaultStop[directionNumbers[currentGreen]]
    while(signals[currentGreen].yellow>0 and simulation_active):
        updateValues()
        time.sleep(1)
    if not simulation_active:
        return
        
    currentYellow = 0
    
    signals[currentGreen].green = defaultGreen[currentGreen]
    signals[currentGreen].yellow = defaultYellow
    signals[currentGreen].red = defaultRed
       
    currentGreen = nextGreen
    nextGreen = (currentGreen+1)%noOfSignals
    signals[nextGreen].red = signals[currentGreen].yellow+signals[currentGreen].green
    repeat()  

# Update values of the signal timers after every second
def updateValues():
    for i in range(0, noOfSignals):
        if(i==currentGreen):
            if(currentYellow==0):
                signals[i].green-=1
            else:
                signals[i].yellow-=1
        else:
            signals[i].red-=1

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
    
    filename = "output\directional_counts.json"
    
    # Check if file exists and has been modified
    if not os.path.exists(filename):
        return
    
    current_mtime = os.path.getmtime(filename)
    if current_mtime <= last_json_mtime:
        return  # No changes to the file
    
    last_json_mtime = current_mtime
    
    vehicle_counts = read_vehicle_counts(filename)
    if not vehicle_counts:
        return
    
    # Create a mapping from direction names to numbers
    direction_mapping = {'right': 0, 'down': 1, 'left': 2, 'up': 3}
    
    # Generate a unique ID for this batch of vehicles
    batch_id = int(time.time())
    
    for direction, vehicles_data in vehicle_counts.items():
        for vehicle_type, count in vehicles_data.items():
            for i in range(count):
                # Create a unique vehicle ID
                vehicle_id = f"{batch_id}_{direction}_{vehicle_type}_{i}"
                
                # Check if we've already generated this vehicle
                if vehicle_id in generated_vehicles:
                    continue
                
                # Randomly assign a lane (0, 1, or 2)
                lane = random.randint(0, 2)
                direction_number = direction_mapping[direction]
                
                # Generate the vehicle
                Vehicle(lane, vehicle_type, direction_number, direction, vehicle_id)
                
                # Mark this vehicle as generated
                generated_vehicles.add(vehicle_id)
                
                # Add a small delay to prevent too many vehicles at once
                time.sleep(0.1)

# Thread function to periodically check for new vehicles
def vehicle_generation_thread():
    while simulation_active:  # Only run while simulation is active
        generate_vehicles_from_json()
        time.sleep(2)  # Check for updates every 2 seconds

class Main:
    thread1 = threading.Thread(name="initialization",target=initialize, args=())    # initialization
    thread1.daemon = True
    thread1.start()

    # Start vehicle generation thread
    thread2 = threading.Thread(name="vehicle_generation", target=vehicle_generation_thread, args=())
    thread2.daemon = True
    thread2.start()

    # Colours 
    black = (0, 0, 0)
    white = (255, 255, 255)

    # Setting background image i.e. image of intersection
    background = pygame.image.load('images/intersection.png')

    screen = pygame.display.set_mode(screenSize)
    pygame.display.set_caption("Normal Traffic Simulation with Metrics")

    # Loading signal images and font
    redSignal = pygame.image.load('images/signals/red.png')
    yellowSignal = pygame.image.load('images/signals/yellow.png')
    greenSignal = pygame.image.load('images/signals/green.png')
    font = pygame.font.Font(None, 30)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()

        screen.blit(background,(0,0))
        for i in range(0,noOfSignals):
            if(i==currentGreen):
                if(currentYellow==1):
                    signals[i].signalText = signals[i].yellow
                    screen.blit(yellowSignal, signalCoods[i])
                else:
                    signals[i].signalText = signals[i].green
                    screen.blit(greenSignal, signalCoods[i])
            else:
                if(signals[i].red<=10):
                    signals[i].signalText = signals[i].red
                else:
                    signals[i].signalText = "---"
                screen.blit(redSignal, signalCoods[i])
        signalTexts = ["","","",""]

        # display signal timer
        for i in range(0,noOfSignals):  
            signalTexts[i] = font.render(str(signals[i].signalText), True, white, black)
            screen.blit(signalTexts[i],signalTimerCoods[i])

        # display the vehicles
        for vehicle in simulation:  
            screen.blit(vehicle.image, [vehicle.x, vehicle.y])
            if simulation_active:
                vehicle.move()

        # Calculate and display metrics
        metrics = calculate_metrics()
        display_metrics(screen, metrics)
        
        pygame.display.update()


Main()