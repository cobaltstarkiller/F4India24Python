import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.io as pio
from tkinter import Tk
from tkinter.filedialog import askopenfilename

# Helper function to load metadata and telemetry
def load_data(file_path):
    metadata_df = pd.read_csv(file_path, nrows=14, header=None, engine='python')
    telemetry_df = pd.read_csv(file_path, skiprows=14, low_memory=False)
    
    for col in telemetry_df.columns:
        telemetry_df[col] = pd.to_numeric(telemetry_df[col], errors='coerce')
    
    return metadata_df, telemetry_df

# Helper function to convert segment times
def convert_time_to_seconds(time_str):
    try:
        minutes, seconds = map(float, time_str.split(':'))
        return minutes * 60 + seconds
    except ValueError:
        return np.nan

# Helper function to extract fastest lap telemetry data
def get_fastest_lap_data(metadata_df, telemetry_df):
    segment_times_raw = metadata_df.iloc[12].values[1:]
    
    # Convert segment times to seconds
    segment_times = [convert_time_to_seconds(time) for time in segment_times_raw if isinstance(time, str)]
    
    # Remove outliers for lap times (acceptable range: 95 to 120 seconds)
    laps_array = [time for time in segment_times if 95 <= time <= 120]
    
    # Calculate start and end timestamps for the fastest lap
    fastest_lap_time = min(laps_array)
    fastest_lap_index = segment_times.index(fastest_lap_time)
    
    start_time_stamp = sum(segment_times[:fastest_lap_index])
    end_time_stamp = sum(segment_times[:fastest_lap_index + 1])
    
    # Filter telemetry data for the fastest lap
    telemetry_FL = telemetry_df[(telemetry_df['Time'] >= start_time_stamp) & (telemetry_df['Time'] <= end_time_stamp)]
    
    # Adjust the distance calculation to be relative to the start of the fastest lap
    start_distance = telemetry_FL['Distance on Vehicle Speed'].iloc[0]
    telemetry_FL['Distance'] = telemetry_FL['Distance on Vehicle Speed'] - start_distance
    
    return telemetry_FL

# Function to generate a track map using GPS coordinates
def generate_track_map(telemetry_FL_1, telemetry_FL_2, driver_1, car_1, driver_2, car_2):
    # Create figure
    fig = go.Figure()

    # Plot Driver 1 track with latitude and longitude in hover text
    fig.add_trace(go.Scattermapbox(
        lon=telemetry_FL_1['GPS Longitude'], 
        lat=telemetry_FL_1['GPS Latitude'],
        mode='lines',
        name=f'{driver_1} #({car_1})',
        line=dict(width=4, color='blue'),
        hoverinfo='text',
        text=[
            f"{driver_1} Speed: {speed} km/h<br>Lat: {lat}<br>Lon: {lon}"
            for speed, lat, lon in zip(
                telemetry_FL_1['Speed'], 
                telemetry_FL_1['GPS Latitude'], 
                telemetry_FL_1['GPS Longitude']
            )
        ]
    ))

    # Plot Driver 2 track with latitude and longitude in hover text
    fig.add_trace(go.Scattermapbox(
        lon=telemetry_FL_2['GPS Longitude'], 
        lat=telemetry_FL_2['GPS Latitude'],
        mode='lines',
        name=f'{driver_2} #({car_2})',
        line=dict(width=4, color='red'),
        hoverinfo='text',
        text=[
            f"{driver_2} Speed: {speed} km/h<br>Lat: {lat}<br>Lon: {lon}"
            for speed, lat, lon in zip(
                telemetry_FL_2['Speed'], 
                telemetry_FL_2['GPS Latitude'], 
                telemetry_FL_2['GPS Longitude']
            )
        ]
    ))

    # Update layout
    fig.update_layout(
        mapbox=dict(
            style="carto-darkmatter",
            center=dict(lat=telemetry_FL_1['GPS Latitude'].mean(), lon=telemetry_FL_1['GPS Longitude'].mean()),
            zoom=16,
            accesstoken="sk.eyJ1Ijoib2Z0ZW4tY2FsbGVkLXBrIiwiYSI6ImNtMnFtd3ZveTB3aWIybHNiMmJvYjVubjcifQ.FGH6BkG6vZgFF0dMCYovjg", 
        ),
        title="Track Map Comparison: Fastest Lap",
        margin={"r":0,"t":0,"l":0,"b":0}
    )

    fig.show()

# Function to prompt user to select two files
def select_files():
    Tk().withdraw()  # Close the root window
    print("Please select the first file:")
    file_path_car1 = askopenfilename()
    print(f"First file selected: {file_path_car1}")
    
    print("Please select the second file:")
    file_path_car2 = askopenfilename()
    print(f"Second file selected: {file_path_car2}")
    
    return file_path_car1, file_path_car2

# Main function to run the comparison and map generation
def main():
    # Select the files for two drivers
    file_path_car1, file_path_car2 = select_files()

    # Load data for both drivers
    metadata_df_1, telemetry_df_1 = load_data(file_path_car1)
    metadata_df_2, telemetry_df_2 = load_data(file_path_car2)

    # Get fastest lap telemetry for both drivers
    telemetry_FL_1 = get_fastest_lap_data(metadata_df_1, telemetry_df_1)
    telemetry_FL_2 = get_fastest_lap_data(metadata_df_2, telemetry_df_2)
    
    # Extract driver and car information
    driver_name_car1 = metadata_df_1.iloc[3, 1]  # Assuming 'Racer' is the 4th row 
    car_number_car1 = metadata_df_1.iloc[2, 1]  # Assuming 'Vehicle' is the 3rd row 
    
    driver_name_car2 = metadata_df_2.iloc[3, 1]  # Assuming 'Racer' is the 4th row 
    car_number_car2 = metadata_df_2.iloc[2, 1]  # Assuming 'Vehicle' is the 3rd row 
    
    # Generate track map
    generate_track_map(telemetry_FL_1, telemetry_FL_2, driver_name_car1, car_number_car1, driver_name_car2, car_number_car2)

# Run the main function
if __name__ == "__main__":
    main()
