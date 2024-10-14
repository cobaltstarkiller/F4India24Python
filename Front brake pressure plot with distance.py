## Brake pressure changes

import tkinter as tk
from tkinter import filedialog, simpledialog
import pandas as pd
import numpy as np
import re
import json
#import geopy
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
#from fastf1.core import Laps
from timple.timedelta import strftimedelta
#import fastf1.plotting
from matplotlib import colormaps
from matplotlib.collections import LineCollection
import matplotlib.pyplot as plt

def load_car_data(json_file):
    with open(json_file, 'r') as f:
        car_data = json.load(f)
    return car_data

def load_sector_data(json_file):
    with open(json_file, 'r') as f:
        sector_data = json.load(f)
    return sector_data

def select_files():
    root = tk.Tk()
    root.withdraw()
    file_paths = filedialog.askopenfilenames(title='Select txt files', filetypes=[('Text Files', '*.txt')])
    return file_paths

def extract_run_and_car(filename):
    """Extracts the run number (X) after 'Tr' and car number (Y) after 'F4-'."""
    run_match = re.search(r'Tr(\d+)', filename)
    car_match = re.search(r'F4-(\d+)', filename)
    run_number = run_match.group(1) if run_match else "Unknown"
    car_number = car_match.group(1) if car_match else "Unknown"
    return run_number, car_number

def get_driver_engineer(car_data, car_number):
    """Looks up the driver and engineer based on the car number."""
    for entry in car_data:
        if entry["car"] == int(car_number): 
            return entry["driver"],entry["engineer"]
            
    return "Unknown", "Unknown"

from geopy.distance import geodesic  # Import geopy for distance calculation
from matplotlib.colors import LinearSegmentedColormap

def calculate_distance(point1, point2):
    """Calculates distance between two GPS points."""
    return geodesic(point1, point2).meters

def process_file(file_path, driver, sector_data):
    df = pd.read_csv(file_path, sep=';', decimal=',')
    print(df.columns)

    # Extract brake pressure and GPS coordinates
    pBrakeF = df['pBrakeF'].to_numpy().astype(int)
    latitudes = df['GPS_Lat'].to_numpy()
    longitudes = df['GPS_Long'].to_numpy()

    # Find the first point where brake pressure is greater than 90%
    brake_idx = np.argmax(pBrakeF > 90)
    if pBrakeF[brake_idx] <= 90:
        print(f"No brake pressure greater than 90% found in {file_path}. Plotting the highest brake pressure point instead.")
        # Use the point of maximum brake pressure if none exceeds 90%
        brake_idx = np.argmax(pBrakeF)

    brake_point = (latitudes[brake_idx], longitudes[brake_idx])

    # Calculate distance from brake point to each sector's first coordinate
    distances = []
    for sector in sector_data:
        sector_point = (float(sector["GPS_Lat1"]), float(sector["GPS_Long1"]))
        distance = calculate_distance(brake_point, sector_point)
        distances.append({
            "sector": sector["Sector"],  # Correct key is "Sector" instead of "name"
            "distance_to_brake_point": distance
        })

    # Select a sector to annotate on the plot (taking the first sector for simplicity)
    first_sector = sector_data[0]
    first_sector_point = (float(first_sector["GPS_Lat1"]), float(first_sector["GPS_Long1"]))
    distance_to_first_sector = calculate_distance(brake_point, first_sector_point)

    # Define a custom colormap from green to yellow to red
    green_yellow_red = LinearSegmentedColormap.from_list("GreenYellowRed", ["green", "yellow", "red"])

    # Plotting logic
    points = np.array([longitudes, latitudes]).T.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)
    
    # Apply the custom colormap
    lc_comp = LineCollection(segments, norm=plt.Normalize(pBrakeF.min(), pBrakeF.max()), cmap=green_yellow_red)
    lc_comp.set_array(pBrakeF)
    lc_comp.set_linewidth(2)
    
    plt.gca().add_collection(lc_comp)
    plt.axis('equal')
    plt.tick_params(labelleft=False, left=False, labelbottom=False, bottom=False)
    
    title = plt.suptitle(f"Fastest Lap brake pressure Visualization\n {driver} - Round 1 MIC 2024")
    
    cbar = plt.colorbar(mappable=lc_comp, label="Front Brake pressure",
                    boundaries=np.arange(0, 100))
    cbar.set_ticks(np.arange(0, 100, 10))
    cbar.set_ticklabels(np.arange(0, 100, 10))

    # Annotate the distance on the plot at the brake point (either >90% or max)
    plt.annotate(
        f'Distance to {first_sector["Sector"]}: {distance_to_first_sector:.2f} m',
        xy=(longitudes[brake_idx], latitudes[brake_idx]),
        xytext=(longitudes[brake_idx] + 0.001, latitudes[brake_idx] + 0.001),  # Offset to avoid overlap
        arrowprops=dict(facecolor='red', shrink=0.05),
        fontsize=9,
        color='red',
        backgroundcolor='white'
    )

    plt.show()

    return distances

def main():
    # Load car data from JSON file
    car_data = load_car_data("cardrivers.json")
    sector_data = load_sector_data("chennai_sectors.json")
    
    file_paths = select_files()
    report_data = []
    
    for file in file_paths:
        file_name = file.split('/')[-1]
        run_number, car_number = extract_run_and_car(file_name)
        
        driver, engineer = get_driver_engineer(car_data, car_number)
        print(driver, engineer)
        
        distances = process_file(file, driver, sector_data)
        report_data.append(distances)

if __name__ == "__main__":
    main()
