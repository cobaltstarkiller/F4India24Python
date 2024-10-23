import pandas as pd
import numpy as np
from bokeh.plotting import figure, show, output_file
from bokeh.layouts import column
from bokeh.models import ColumnDataSource

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

# Prepare data for Bokeh
car1_source = ColumnDataSource(telemetry_FL_car1)
car2_source = ColumnDataSource(telemetry_FL_car2)

# Define action colors
action_colors = {'Full Throttle': 'green', 'Turning': 'yellow', 'Brake': 'red'}

# Create Speed Plot for both cars
speed_plot = figure(width=800, height=300, title="Speed Comparison: Car 1 vs Car 2",
                    x_axis_label='Distance (m)', y_axis_label='Speed (km/h)')
speed_plot.line('Distance', 'GPS Speed', source=car1_source, line_width=2, color='cyan', legend_label='Car 1 Speed')
speed_plot.line('Distance', 'GPS Speed', source=car2_source, line_width=2, color='orange', legend_label='Car 2 Speed')
speed_plot.legend.location = 'top_left'

# Create Action Plot for Car 1
car1_action_plot = figure(width=800, height=200, title="Car 1 Actions",
                          x_axis_label='Distance (m)', y_axis_label='Action Type')

for action_type, color in action_colors.items():
    car1_action_source = telemetry_FL_car1[telemetry_FL_car1['Action'] == action_type]
    car1_action_plot.vbar(x=car1_action_source['Distance'], top=1, width=car1_action_source['Distance'].diff().fillna(1), 
                          color=color, legend_label=action_type)

# Create Action Plot for Car 2
car2_action_plot = figure(width=800, height=200, title="Car 2 Actions",
                          x_axis_label='Distance (m)', y_axis_label='Action Type')

for action_type, color in action_colors.items():
    car2_action_source = telemetry_FL_car2[telemetry_FL_car2['Action'] == action_type]
    car2_action_plot.vbar(x=car2_action_source['Distance'], top=1, width=car2_action_source['Distance'].diff().fillna(1), 
                          color=color, legend_label=action_type)

# Arrange the plots vertically
layout = column(speed_plot, car1_action_plot, car2_action_plot)

# Output the result to an HTML file and show the plot
output_file("telemetry_comparison_bokeh.html")
show(layout)
