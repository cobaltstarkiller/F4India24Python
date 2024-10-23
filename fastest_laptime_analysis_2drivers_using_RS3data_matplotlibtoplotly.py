import pandas as pd
import numpy as np
import plotly.graph_objs as go
from plotly.subplots import make_subplots

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
    segment_times = []
    for time in segment_times_raw:
        if isinstance(time, str):
            segment_times.append(convert_time_to_seconds(time))
    
    # Remove outliers for lap times (acceptable range: 95 to 120 seconds)
    laps_array = [time for time in segment_times if 95 <= time <= 120]
    
    # Calculate start and end timestamps for the fastest lap
    fastest_lap_time = min(laps_array)
    fastest_lap_index = laps_array.index(fastest_lap_time)
    
    start_time_stamp = sum(segment_times[:fastest_lap_index])
    end_time_stamp = sum(segment_times[:fastest_lap_index + 1])
    
    # Filter telemetry data for the fastest lap
    telemetry_FL = telemetry_df[(telemetry_df['Time'] >= start_time_stamp) & (telemetry_df['Time'] <= end_time_stamp)]

    # Adjust the distance calculation to be relative to the start of the fastest lap
    start_distance = telemetry_FL['Distance on GPS Speed'].iloc[0]
    telemetry_FL['Distance'] = telemetry_FL['Distance on GPS Speed'] - start_distance
    
    return telemetry_FL

# Helper function to classify telemetry actions
def classify_actions(telemetry_FL):
    throttle_threshold = 90
    brake_pos_median = telemetry_FL['Brake Pos'].median()
    brake_press_median = telemetry_FL['Brake Press'].median()

    telemetry_FL['Action'] = 'Turning'  # Default action is Turning
    telemetry_FL.loc[telemetry_FL['Throttle Pos'] > throttle_threshold, 'Action'] = 'Full Throttle'
    telemetry_FL.loc[(telemetry_FL['Brake Pos'] > brake_pos_median) & 
                     (telemetry_FL['Brake Press'] > brake_press_median), 'Action'] = 'Brake'
    
    return telemetry_FL

# Load data for both cars
file_path_car1 = 'Jaden Pariat Round 3 Race 1 Telemetry.csv'
file_path_car2 = 'Abhay Mohan Round 3 Race 1 Telemetry.csv'

metadata_df_car1, telemetry_df_car1 = load_data(file_path_car1)
metadata_df_car2, telemetry_df_car2 = load_data(file_path_car2)

# Get fastest lap telemetry for both cars
telemetry_FL_car1 = get_fastest_lap_data(metadata_df_car1, telemetry_df_car1)
telemetry_FL_car2 = get_fastest_lap_data(metadata_df_car2, telemetry_df_car2)

# Classify actions for both cars
telemetry_FL_car1 = classify_actions(telemetry_FL_car1)
telemetry_FL_car2 = classify_actions(telemetry_FL_car2)

# Define action colors for Plotly
action_colors = {'Full Throttle': 'green', 'Turning': 'yellow', 'Brake': 'red'}

# Create subplots with shared x-axis
fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.05,
                    subplot_titles=("Speed vs Distance", "Car 1 Telemetry Actions", "Car 2 Telemetry Actions"),
                    row_heights=[0.6, 0.2, 0.2])

# Plot Speed vs Distance (Top Plot)
fig.add_trace(go.Scatter(x=telemetry_FL_car1['Distance'], y=telemetry_FL_car1['GPS Speed'], 
                         mode='lines', name='Car 1 Speed', line=dict(color='cyan', width=2)), row=1, col=1)
fig.add_trace(go.Scatter(x=telemetry_FL_car2['Distance'], y=telemetry_FL_car2['GPS Speed'], 
                         mode='lines', name='Car 2 Speed', line=dict(color='orange', width=2)), row=1, col=1)

# Plot Telemetry Actions for Car 1 (Middle Plot)
for action_type in telemetry_FL_car1['Action'].unique():
    action_data = telemetry_FL_car1[telemetry_FL_car1['Action'] == action_type]
    fig.add_trace(go.Bar(x=action_data['Distance'], y=['Car 1']*len(action_data), 
                         orientation='h', marker=dict(color=action_colors[action_type]), 
                         showlegend=False, name=action_type), row=2, col=1)

# Plot Telemetry Actions for Car 2 (Bottom Plot)
for action_type in telemetry_FL_car2['Action'].unique():
    action_data = telemetry_FL_car2[telemetry_FL_car2['Action'] == action_type]
    fig.add_trace(go.Bar(x=action_data['Distance'], y=['Car 2']*len(action_data), 
                         orientation='h', marker=dict(color=action_colors[action_type]), 
                         showlegend=False, name=action_type), row=3, col=1)

# Update layout for appearance
fig.update_layout(height=900, width=1200, title_text="Telemetry Data Comparison: Fastest Lap Car 1 vs Car 2",
                  plot_bgcolor='black', paper_bgcolor='black', font=dict(color='white'))

# Update y-axes and x-axes labels
fig.update_yaxes(title_text="Speed (km/h)", row=1, col=1)
fig.update_xaxes(title_text="Distance (m)", row=3, col=1)

# Add a legend for actions at the bottom
fig.update_layout(
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=-0.2,
        xanchor="center",
        x=0.5,
        title="Actions",
    )
)

# Show the figure
fig.show()
