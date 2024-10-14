## Brake pressure changes

import tkinter as tk
from tkinter import filedialog, simpledialog
import pandas as pd
import numpy as np
import re
import json
import geopy
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from fastf1.core import Laps
from timple.timedelta import strftimedelta
import fastf1.plotting
from matplotlib import colormaps
from matplotlib.collections import LineCollection
from matplotlib.colors import LinearSegmentedColormap
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

def process_file(file_path,driver ):
    df = pd.read_csv(file_path, sep=';', decimal=',')
    print(df.columns)
    
    x = np.array(df['GPS_Lat'].values)
    y = np.array(df['GPS_Long'].values)
    
    points = np.array([y, x]).T.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)
    pBrakeF = df['pBrakeF'].to_numpy().astype(int)
    
    cmap = LinearSegmentedColormap.from_list("GreenYellowRed", ["green","yellow","red"])
    lc_comp = LineCollection(segments, norm=plt.Normalize(pBrakeF.min(), pBrakeF.max()), cmap=cmap)
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


    plt.show()


def main():
    # Load car data from JSON file
    json_file = "cardrivers.json"  # Adjust the path if necessary
    car_data = load_car_data(json_file)
    
    json_file = "chennai_sectors.json"
    sector_data = load_sector_data
    
    file_paths = select_files()
    report_data = []
    
    for file in file_paths:
        file = file.split('/')[-1]
        run_number, car_number = extract_run_and_car(file)
        
         # Extract run number and car number from the filename
        driver, engineer = get_driver_engineer(car_data, car_number)
        print(driver,engineer)
        
    for file_path in file_paths:
        report_data.append(process_file(file_path,driver))
    
    #generate_pdf_report(report_data, file_paths, car_data)

if __name__ == "__main__":
    main()
