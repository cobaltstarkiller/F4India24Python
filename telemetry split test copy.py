import pandas as pd
import numpy as np
import plotly.graph_objects as go
from tkinter import Tk
from tkinter.filedialog import askopenfilename

# Helper function to load metadata and telemetry
def load_data(file_path):
    metadata_df = pd.read_csv(file_path, nrows=14, header=None, engine='python')
    telemetry_df = pd.read_csv(file_path, skiprows=14, low_memory=False)
    
    for col in telemetry_df.columns:
        telemetry_df[col] = pd.to_numeric(telemetry_df[col], errors='coerce')
    
    return metadata_df, telemetry_df

# Helper function to extract fastest lap telemetry data
def get_fastest_lap_data(metadata_df, telemetry_df):
    segment_times_raw = metadata_df.iloc[12].values[1:]
    
    # Convert segment times to seconds
    segment_times = []
    for time in segment_times_raw:
        if isinstance(time, str):  # Only split if it's a string
            try:
                minutes, seconds = map(float, time.split(':'))
                segment_times.append(minutes * 60 + seconds)
            except ValueError:
                continue
        elif isinstance(time, (float, int)):  # Handle if it's already a number
            segment_times.append(float(time))
    
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

# Function to plot the track with color-coded sections based on speed
def generate_colored_track(telemetry_FL_1, telemetry_FL_2, driver_1, driver_2):
    min_len = min(len(telemetry_FL_1), len(telemetry_FL_2))
    telemetry_FL_1 = telemetry_FL_1.iloc[:min_len]
    telemetry_FL_2 = telemetry_FL_2.iloc[:min_len]

    # Create figure for the map
    fig = go.Figure()

    # Calculate speed difference
    speed_diff = telemetry_FL_1['Speed'] - telemetry_FL_2['Speed']

    # Initialize lists to store segment data
    lons = []
    lats = []
    hover_texts = []
    current_color = 'blue' if speed_diff.iloc[0] > 0 else 'red'

    for i in range(min_len - 1):
        # Check if the driver with the higher speed changes
        new_color = 'blue' if speed_diff.iloc[i] > 0 else 'red'
        
        # Add points to the current segment
        lons.extend([telemetry_FL_1['GPS Longitude'].iloc[i], telemetry_FL_1['GPS Longitude'].iloc[i + 1]])
        lats.extend([telemetry_FL_1['GPS Latitude'].iloc[i], telemetry_FL_1['GPS Latitude'].iloc[i + 1]])
        hover_texts.append(f'{driver_1} Speed: {telemetry_FL_1["Speed"].iloc[i]:.2f} | {driver_2} Speed: {telemetry_FL_2["Speed"].iloc[i]:.2f}')

        # If the color changes or it's the last segment, plot the current segment
        if new_color != current_color or i == min_len - 2:
            fig.add_trace(go.Scattermapbox(
                lon=lons,
                lat=lats,
                mode='lines',
                line=dict(width=6, color=current_color),
                hoverinfo='text',
                text=hover_texts
            ))
            lons = []
            lats = []
            hover_texts = []
            current_color = new_color

    # Add dummy traces for the legend (for drivers)
    # fig.add_trace(go.Scattermapbox(
    #     lon=[None], lat=[None],
    #     mode='lines',
    #     line=dict(width=6, color='blue'),
    #     name=f'{driver_1} Faster',
    #     showlegend=True
    # ))
    # fig.add_trace(go.Scattermapbox(
    #     lon=[None], lat=[None],
    #     mode='lines',
    #     line=dict(width=6, color='red'),
    #     name=f'{driver_2} Faster',
    #     showlegend=True
    # ))

    # Update layout with legend positioning
    fig.update_layout(
        mapbox_style="open-street-map",
        mapbox=dict(
            center=dict(lat=telemetry_FL_1['GPS Latitude'].mean(), lon=telemetry_FL_1['GPS Longitude'].mean()),
            zoom=14
        ),
        title="Track Map: Speed Comparison",
        legend=dict(
            x=0.99,  # Positioning near the right edge
            y=0.01,  # Positioning near the bottom
            xanchor='right',
            yanchor='bottom',
            bgcolor='rgba(255,255,255,0.5)',  # Semi-transparent background
            bordercolor='black',
            borderwidth=1
        ),
        margin={"r": 0, "t": 0, "l": 0, "b": 0}
    )

    fig.show()

# Main function to run the comparison and map generation
def main():
    # Select the files for two drivers
    Tk().withdraw()  # Close the root window
    file_path_car1 = askopenfilename()
    file_path_car2 = askopenfilename()

    # Load data for both drivers
    metadata_df_1, telemetry_df_1 = load_data(file_path_car1)
    metadata_df_2, telemetry_df_2 = load_data(file_path_car2)

    # Extract driver information
    driver_name_car1 = metadata_df_1.iloc[3, 1]
    driver_name_car2 = metadata_df_2.iloc[3, 1]

    # Get fastest lap telemetry for both drivers
    telemetry_FL_1 = get_fastest_lap_data(metadata_df_1, telemetry_df_1)
    telemetry_FL_2 = get_fastest_lap_data(metadata_df_2, telemetry_df_2)

    # Generate the track map with color switching
    generate_colored_track(telemetry_FL_1, telemetry_FL_2, driver_name_car1, driver_name_car2)

if __name__ == "__main__":
    main()
