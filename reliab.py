import tkinter as tk
from tkinter import filedialog, simpledialog
import pandas as pd
import numpy as np
import re
import json
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

# Load car data from the JSON file
def load_car_data(json_file):
    with open(json_file, 'r') as f:
        car_data = json.load(f)
    return car_data

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
            return entry["driver"], entry["engineer"]
    return "Unknown", "Unknown"

def process_file(file_path):
    df = pd.read_csv(file_path, sep=';', decimal=',')
    
    # Ensure 'Time' and 'DistanceLap' are treated as numeric values
    df['Time'] = pd.to_numeric(df['Time'], errors='coerce')
    df['DistanceLap'] = pd.to_numeric(df['DistanceLap'], errors='coerce')

    # Determine the first lap number to ignore
    first_lap = df['Logger_Lap'].iloc[0]
    df = df[df['Logger_Lap'] != first_lap]

    lap_numbers = df['Logger_Lap'].unique()
    report_data = []

    for lap in lap_numbers:
        lap_data = df[df['Logger_Lap'] == lap]
        
        # Calculate the required values
        avg_twater = lap_data['tWater'].mean()
        avg_vbatt = lap_data['VBatt'].mean()
        max_toil = lap_data['tOil'].max()
        max_poil = lap_data['pOil'].max()
        min_poil = lap_data['pOil'].min() if lap_data['pOil'].min() >= 1 else None
        
        
        # Top speed in the specific GPS range
        section_data = lap_data[(lap_data['GPS_Lat'].between(13.0029010, 13.0031654)) & (lap_data['GPS_Long'].between(79.9815728, 79.9837020))]
        max_speed_section = section_data['CarSpeed'].max()
        
        # Maximum TAir in the GPS section
        max_tair_section = section_data['tAir'].max()
        
        # Percentage of lap spent in full throttle
        full_throttle_time = lap_data[lap_data['rPedal'] > 96]['Time'].count()
        total_time = lap_data['Time'].count()
        full_throttle_percent = (full_throttle_time / total_time) * 100
        
        # Brake balance in another GPS range
        brake_section = lap_data[(lap_data['GPS_Lat'].between(13.0048683, 13.0050674)) & (lap_data['GPS_Long'].between(79.9828976, 79.9840276))]
        if not brake_section.empty:
            max_pbrakef = brake_section['pBrakeF'].max()
            brake_balance_row = brake_section[brake_section['pBrakeF'] == max_pbrakef]
            if not brake_balance_row.empty:
                brake_balance = brake_balance_row['BrakeBalance'].iloc[0]
            else:
                brake_balance = np.nan  # or some other default value
        else:
            brake_balance = np.nan  # or some other default value
        
        # Lockup condition time calculation with pBrakeF > 5 condition
        lockup_condition = lap_data[(np.abs(lap_data['WSpeed_FL'] - lap_data['WSpeed_FR']) > 0.1 * lap_data['WSpeed_FL']) & (lap_data['pBrakeF'] > 5)]
        
        lockup_time = len(lockup_condition) * 0.005  # Total time spent in lockup condition in seconds

        # Fuel consumption per lap
        fuel_consumption = lap_data['mFuelConsLap'].max() - lap_data['mFuelConsLap'].min()
        
        #LP fuel current
        lp_fuel = lap_data['PBX_LP_Fuel_Current'].min() #- lap_data['PBX_LP_Fuel_Current'].min()
        
        
        report_data.append([
            lap,  # Add the lap number as the first column
            round(avg_twater, 2),
            round(avg_vbatt, 2),
            round(max_toil, 2),
            round(max_poil, 2),
            round(min_poil, 2) if min_poil is not None else np.nan,
            round(max_speed_section, 2),
            round(max_tair_section, 2),
            round(full_throttle_percent, 2),
            round(brake_balance, 2),
            round(lockup_time, 2),  # lockup_time is now calculated in seconds
            round(fuel_consumption, 2),
            round(lp_fuel,2)
        ])
    
    return pd.DataFrame(report_data, columns=[
        'Lap', 'tWat_avg', 'Vbatt_avg', 'tOil_max', 'pOil_max', 'pOil_min',
        'Vmax', 'tAir_max', '%fThr', 'BB%', 'Lockup_time', 'Fuel','PBX_LP_Fuel_Current'
    ])

def generate_pdf_report(report_data, file_paths, car_data):
    # Initialize tkinter root window
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    
    # Prompt for a PDF file name
    base_name = "24_F4 India R01 Reliability Session"
    pdf_name = simpledialog.askstring("Save PDF", "Enter a name for the PDF file:", initialvalue=base_name, parent=root)
    
    #Cancel generation if name not provided (could be user trialling the code)
    if not pdf_name:
        print("PDF generation canceled.")
        return
    
    # Check if the user provided a name; use the base name if not
    #if not pdf_name:
        #pdf_name = base_name
    
    # Ensure the filename ends with .pdf
    if not pdf_name.endswith(".pdf"):
        pdf_name += ".pdf"
    
    pdf = SimpleDocTemplate(pdf_name, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()

    # Page width and margins
    page_width, page_height = letter
    margin = 50
    usable_width = page_width - 2 * margin
    
    for i, file_path in enumerate(file_paths):
        # Extract run number and car number from the filename
        filename = file_path.split('/')[-1]
        run_number, car_number = extract_run_and_car(filename)
        
        # Look up driver and engineer names based on car number
        driver, engineer = get_driver_engineer(car_data, car_number)
        
        title = f"Run {run_number} of Car {car_number}/{driver}/{engineer}"
        
        elements.append(Paragraph(title, styles['Heading2']))
        elements.append(Spacer(1, 12))
        
        # Get the data for the current file
        data = report_data[i]
        
        # Calculate column widths to fit the table on the page
        num_columns = len(data.columns)
        col_width = usable_width / num_columns
        
        # Convert the data to a list of lists for easier processing
        table_data = [data.columns.tolist()] + data.values.tolist()
        
        # Determine indices for the highlights
        highlight_styles = []
        
        # Get the data (excluding header) for highlighting
        data_values = data.iloc[:, 1:]  # Exclude 'Lap' column

        max_twat = data_values['tWat_avg'].idxmax() + 1  # +1 because table_data includes the header
        min_vbatt = data_values['Vbatt_avg'].idxmin() + 1
        max_toil = data_values['tOil_max'].idxmax() + 1
        max_poil_max = data_values['pOil_max'].idxmax() + 1
        min_poil_min = data_values[data_values['pOil_min'] >= 1]['pOil_min'].idxmin() + 1
        max_vmax = data_values['Vmax'].idxmax() + 1
        max_tair = data_values['tAir_max'].idxmax() + 1
        max_fthr = data_values['%fThr'].idxmax() + 1
        max_lockup = data_values['Lockup_time'].idxmax() + 1
        max_fuel = data_values['Fuel'].idxmax() + 1
        avg_bb = abs(data_values['BB%'] - data_values['BB%'].mean()).idxmin() + 1
        min_lp = data_values['PBX_LP_Fuel_Current'].idxmin()+1

        # Highlighting the values
        highlight_styles.extend([
            ('BACKGROUND', (1, max_twat), (1, max_twat), colors.yellow),
            ('BACKGROUND', (2, min_vbatt), (2, min_vbatt), colors.yellow),
            ('BACKGROUND', (3, max_toil), (3, max_toil), colors.yellow),
            ('BACKGROUND', (4, max_poil_max), (4, max_poil_max), colors.yellow),
            ('BACKGROUND', (5, min_poil_min), (5, min_poil_min), colors.yellow),
            ('BACKGROUND', (6, max_vmax), (6, max_vmax), colors.yellow),
            ('BACKGROUND', (7, max_tair), (7, max_tair), colors.yellow),
            ('BACKGROUND', (8, max_fthr), (8, max_fthr), colors.yellow),
            ('BACKGROUND', (9, avg_bb), (9, avg_bb), colors.yellow),
            ('BACKGROUND', (10, max_lockup), (10, max_lockup), colors.yellow),
            ('BACKGROUND', (11, max_fuel), (11, max_fuel), colors.yellow),
            ('BACKGROUND', (12, min_lp), (12, min_lp), colors.yellow)
        ])

        # Create the table with highlighted values
        data_table = Table(table_data, colWidths=[col_width] * num_columns)
        data_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),  # Smaller font size for headers
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),  # Adjust padding if needed
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ] + highlight_styles))
        
        elements.append(data_table)
        elements.append(Spacer(1, 24))
    
    pdf.build(elements)
    print(f"PDF report '{pdf_name}' generated successfully!")

def main():
    # Load car data from JSON file
    json_file = "cardrivers.json"  # Adjust the path if necessary
    car_data = load_car_data(json_file)
    
    file_paths = select_files()
    report_data = []
    
    for file_path in file_paths:
        report_data.append(process_file(file_path))
    
    generate_pdf_report(report_data, file_paths, car_data)

if __name__ == "__main__":
    main()
