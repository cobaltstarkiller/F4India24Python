import json
import pandas as pd
import os
import re
from fpdf import FPDF
import tkinter as tk
from tkinter import filedialog, simpledialog

# Load sector definitions
with open('chennai_sectors.json', 'r') as f:
    sectors = json.load(f)

# Load car driver and engineer data
with open('cardrivers.json', 'r') as f:
    car_info = json.load(f)

# Convert the sector GPS coordinates to float
for sector in sectors:
    sector['GPS_Lat1'] = float(sector['GPS_Lat1'].replace(",", "."))
    sector['GPS_Long1'] = float(sector['GPS_Long1'].replace(",", "."))
    sector['GPS_Lat2'] = float(sector['GPS_Lat2'].replace(",", "."))
    sector['GPS_Long2'] = float(sector['GPS_Long2'].replace(",", "."))

# Helper function to determine if a point is within a sector
def in_sector(lat, lon, sector):
    return (min(sector['GPS_Lat1'], sector['GPS_Lat2']) <= lat <= max(sector['GPS_Lat1'], sector['GPS_Lat2']) and
            min(sector['GPS_Long1'], sector['GPS_Long2']) <= lon <= max(sector['GPS_Long1'], sector['GPS_Long2']))

# Helper function to get the driver and engineer from car number
def get_driver_engineer(car_number):
    for entry in car_info:
        if entry["car"] == car_number:
            return entry["driver"], entry["engineer"]
    return "Unknown", "Unknown"

# Process each file
def process_file(file_path):
    # Load data
    data = pd.read_csv(file_path, delimiter=';', decimal=',')
    
    # Initialize variables
    current_lap = -1  # Start at -1 since the first lap will increment it to 0
    lap_times = []
    sector_times = {sector['Sector']: [] for sector in sectors}
    sector_times['Total_Lap'] = []

    current_sector = None
    sector_start_time = 0
    lap_sector_times = None
    
    # Iterate over each row
    for i, row in data.iterrows():
        lat = float(row['GPS_Lat'])
        lon = float(row['GPS_Long'])

        for sector in sectors:
            if in_sector(lat, lon, sector):
                if sector['Sector'] == 'SF':
                    if current_lap == -1:
                        # First entry into the SF sector
                        current_lap += 1
                        lap_sector_times = {sec['Sector']: 0 for sec in sectors}
                        lap_sector_times['S'] = 0  # Initialize the combined S column
                        lap_sector_times['T10_T11'] = 0  # Initialize the combined T10_T11 column
                        sector_start_time = i
                        current_sector = 'SF'
                        break
                    
                    if current_sector != 'SF':
                        # Lap finished when entering SF again
                        time_in_sector = (i - sector_start_time) * 0.005
                        lap_sector_times[current_sector] += time_in_sector
                        
                        # Combine SA, SB, SC into S and T10E, T10_11 into T10_T11 before recording the lap time
                        lap_sector_times['S'] = (
                            lap_sector_times['SA'] +
                            lap_sector_times['SB'] +
                            lap_sector_times['SC']
                        )
                        lap_sector_times['T10_T11'] = (
                            lap_sector_times['T10E'] +
                            lap_sector_times['T10_11']
                        )

                        # Record the lap time and start a new lap
                        for sec in sectors:
                            sector_times[sec['Sector']].append(lap_sector_times[sec['Sector']])
                        sector_times['Total_Lap'].append(sum(lap_sector_times.values()) - lap_sector_times['S'] - lap_sector_times['T10_T11'])

                        # Reset for the new lap
                        current_lap += 1
                        lap_sector_times = {sec['Sector']: 0 for sec in sectors}
                        lap_sector_times['S'] = 0
                        lap_sector_times['T10_T11'] = 0
                        sector_start_time = i
                        current_sector = 'SF'
                    break
                
                elif current_sector != sector['Sector']:
                    if current_sector is not None:
                        # End the last sector
                        time_in_sector = (i - sector_start_time) * 0.005
                        lap_sector_times[current_sector] += time_in_sector

                    # Start a new sector
                    current_sector = sector['Sector']
                    sector_start_time = i

                break
    
    # Ensure the final lap's sector times are recorded
    if current_lap >= 0:
        if current_sector is not None:
            time_in_sector = (i - sector_start_time) * 0.005
            lap_sector_times[current_sector] += time_in_sector
        
        # Combine SA, SB, SC into S and T10E, T10_11 into T10_T11 before recording the final lap time
        lap_sector_times['S'] = (
            lap_sector_times['SA'] +
            lap_sector_times['SB'] +
            lap_sector_times['SC']
        )
        lap_sector_times['T10_T11'] = (
            lap_sector_times['T10E'] +
            lap_sector_times['T10_11']
        )
        
        for sec in sectors:
            sector_times[sec['Sector']].append(lap_sector_times[sec['Sector']])
        sector_times['Total_Lap'].append(sum(lap_sector_times.values()) - lap_sector_times['S'] - lap_sector_times['T10_T11'])

    # Convert to DataFrame and drop the individual SA, SB, SC, T10E, and T10_11 columns
    result_df = pd.DataFrame(sector_times)
    result_df['S'] = result_df['SA'] + result_df['SB'] + result_df['SC']  # Add the combined S column
    result_df['T10_T11'] = result_df['T10E'] + result_df['T10_11']  # Add the combined T10_T11 column
    result_df.index.name = 'Lap'
    result_df.reset_index(inplace=True)
    result_df['Lap'] = result_df['Lap'].astype(int)  # Round Lap to 0 decimal places
    result_df = result_df.drop(columns=['SA', 'SB', 'SC', 'T10E', 'T10_11'])

    # Reorder columns to place 'S' between 'T3' and 'T4_5' and 'T10_T11' before 'T12'
    columns_order = [
        'Lap', 'SF', 'T1', 'T2', 'T3', 'S', 'T4_5', 'T6_7', 'T8', 'T9', 'T10_T11', 'T12', 'Total_Lap'
    ]
    result_df = result_df[columns_order]
    
    return result_df

# Create the PDF report with highlighted lowest non-zero values and Ideal Lap
def create_pdf_report(dataframes, output_filename):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    page_width = pdf.w - 2 * pdf.l_margin  # Page width minus margins

    pdf.set_font("Arial", size=12)
    pdf.cell(page_width, 10, txt="Race Sector Report", ln=True, align='C')

    for df in dataframes:
        pdf.add_page()
        pdf.set_font("Arial", size=10)
        
        # Extracting Run number, Car number, Driver and Engineer
        file_name = df['File Name'][0]
        run_number = re.search(r"Tr(\d+)", file_name).group(1)
        car_number = int(re.search(r"F4-(\d+)", file_name).group(1))
        driver, engineer = get_driver_engineer(car_number)
        
        # Create the custom title
        title = f"Run {run_number} for Car {car_number} / {driver} / {engineer}"
        pdf.cell(page_width, 10, txt=title, ln=True, align='L')

        # Drop the 'File Name' column before generating the table
        df = df.drop(columns=["File Name"])

        # Calculate the width for each column
        col_width = page_width / len(df.columns)

        # Find the minimum non-zero value for each sector except 'Lap' and 'Total_Lap'
        min_values = df.replace(0, float('inf')).drop(columns=['Lap', 'Total_Lap']).min()

        # Find the minimum value for the 'Total_Lap' column, ignoring the last lap
        total_lap_min = df['Total_Lap'][:-1].min()

        # Column names
        pdf.set_font("Arial", 'B', 10)
        for col_name in df.columns:
            pdf.cell(col_width, 10, col_name, 1, 0, 'C')
        pdf.ln()

        # Table data
        pdf.set_font("Arial", size=10)
        for index, row in df.iterrows():
            for col_name in df.columns:
                cell_value = row[col_name]
                if col_name == 'Total_Lap' and index != len(df) - 1 and cell_value == total_lap_min and cell_value > 0:
                    pdf.set_fill_color(173, 216, 230)  # Light blue fill for the lowest value in Total_Lap
                    pdf.cell(col_width, 10, f"{cell_value:.3f}", 1, 0, 'C', fill=True)
                    pdf.set_fill_color(255, 255, 255)  # Reset fill color
                elif col_name not in ['Lap', 'Total_Lap'] and cell_value == min_values[col_name] and cell_value > 0:
                    pdf.set_fill_color(173, 216, 230)  # Light blue fill for the lowest value
                    pdf.cell(col_width, 10, f"{cell_value:.3f}", 1, 0, 'C', fill=True)
                    pdf.set_fill_color(255, 255, 255)  # Reset fill color
                else:
                    pdf.cell(col_width, 10, f"{cell_value:.3f}", 1, 0, 'C')
            pdf.ln()

        # Add Ideal Lap row
        ideal_lap_total = min_values.sum()

        pdf.set_font("Arial", 'B', 10)
        pdf.cell(col_width * (len(df.columns) - 2), 10, 'Ideal Lap', 1, 0, 'C')  # Span all columns except Lap and Total_Lap
        pdf.cell(col_width, 10, f"{ideal_lap_total:.3f}", 1, 0, 'C')  # Sum of the minimum values
        pdf.cell(col_width, 10, "", 1, 0, 'C')  # Empty cell for Total_Lap
        pdf.ln()

        # Ideal Lap values
        for col_name in df.columns:
            if col_name in ['Lap', 'Total_Lap']:
                pdf.cell(col_width, 10, "", 1, 0, 'C')  # Empty cells for Lap and Total_Lap
            else:
                pdf.cell(col_width, 10, f"{min_values[col_name]:.3f}", 1, 0, 'C')
        pdf.ln()

    pdf.output(output_filename)

# Main logic to process multiple files
def main():
    # Initialize tkinter root
    root = tk.Tk()
    root.withdraw()  # Hide the root window

    # Open a file dialog to select multiple files
    files_to_process = filedialog.askopenfilenames(
        title="Select GPS Data Files",
        filetypes=[("Text files", "*.txt")]
    )

    if not files_to_process:
        print("No files selected.")
        return

    dataframes = []
    for file_path in files_to_process:
        df = process_file(file_path)
        df['File Name'] = os.path.basename(file_path)
        dataframes.append(df)

    # Prompt the user for the PDF file name and location
    output_filename = filedialog.asksaveasfilename(
        defaultextension=".pdf",
        filetypes=[("PDF files", "*.pdf")],
        title="Save PDF Report As"
    )

    if not output_filename:
        print("PDF generation canceled.")
        return

    # Create the PDF report
    create_pdf_report(dataframes, output_filename)
    print(f"PDF report generated: {output_filename}")

if __name__ == "__main__":
    main()
