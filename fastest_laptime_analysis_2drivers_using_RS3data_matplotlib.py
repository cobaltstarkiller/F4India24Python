import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

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
    print(telemetry_df.columns)

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

telemetry_FL_car1.to_csv('car1 actions matplot.csv', index=False)
telemetry_FL_car2.to_csv('car2 actions matplot.csv', index=False)

# Plotting with shared x-axis
plt.style.use('dark_background')

# Create subplots for speed and telemetry actions, sharing the x-axis
fig, ax = plt.subplots(3, figsize=(20, 15), gridspec_kw={'height_ratios': [3, 1, 1]}, sharex=True)

# Plot Speed vs Distance (Top Plot)
ax[0].plot(telemetry_FL_car1['Distance'], telemetry_FL_car1['GPS Speed'], label='Car 1 Speed', color='cyan', linewidth=2)
ax[0].plot(telemetry_FL_car2['Distance'], telemetry_FL_car2['GPS Speed'], label='Car 2 Speed', color='orange', linewidth=2)
ax[0].set_ylabel('Speed (km/h)', fontweight='bold', fontsize=25)
ax[0].set_ylim(0, 210)  # Adjust y-axis to speed range of 0 to 210 km/h
ax[0].tick_params(axis='y', which='major', labelsize=22)
ax[0].tick_params(axis='x', which='major', labelsize=15)

# Add grid lines with less prominent appearance
ax[0].grid(which='major', color='gray', linestyle='-', linewidth=0.5)
ax[0].grid(which='minor', color='gray', linestyle=':', linewidth=0.5)
ax[0].minorticks_on()

# Add legend for speed plot
ax[0].legend(fontsize=18)

# Define action colors
actions = ['Full Throttle', 'Turning', 'Brake']
action_colors = {'Full Throttle': 'green', 'Turning': 'yellow', 'Brake': 'red'}

# Plot Telemetry Actions for Car 1 (Middle Plot)
for driver in ['Car 1']:  # Placeholder car name
    driver_data = telemetry_FL_car1.copy()
    action_changes = driver_data['Action'].ne(driver_data['Action'].shift()).cumsum()
    driver_data['ActionID'] = action_changes
    grouped_actions = driver_data.groupby('ActionID')
    for _, group in grouped_actions:
        action_type = group['Action'].iloc[0]
        color = action_colors[action_type]
        ax[1].barh(driver, group['Distance'].max() - group['Distance'].min(), 
                   left=group['Distance'].min(), color=color)

# Plot Telemetry Actions for Car 2 (Bottom Plot)
for driver in ['Car 2']:  # Placeholder car name
    driver_data = telemetry_FL_car2.copy()
    action_changes = driver_data['Action'].ne(driver_data['Action'].shift()).cumsum()
    driver_data['ActionID'] = action_changes
    grouped_actions = driver_data.groupby('ActionID')
    for _, group in grouped_actions:
        action_type = group['Action'].iloc[0]
        color = action_colors[action_type]
        ax[2].barh(driver, group['Distance'].max() - group['Distance'].min(), 
                   left=group['Distance'].min(), color=color)

# Set x-label for both plots
ax[2].set_xlabel('Distance (m)', fontweight='bold', fontsize=25)
ax[2].invert_yaxis()

# Add grid lines with less prominent appearance
for i in [1, 2]:
    ax[i].grid(which='major', color='gray', linestyle='-', linewidth=0.5)
    ax[i].grid(which='minor', color='gray', linestyle=':', linewidth=0.5)
    ax[i].minorticks_on()

# Remove frame from the second and third plot
for i in [1, 2]:
    ax[i].spines['top'].set_visible(False)
    ax[i].spines['right'].set_visible(False)
    ax[i].spines['left'].set_visible(False)

# Adjust the legend for the actions (bottom of the last plot)
labels = list(action_colors.keys())
handles = [plt.Rectangle((0, 0), 1, 1, color=action_colors[label]) for label in labels]
ax[2].legend(handles, labels, fontsize=10, ncol=3, bbox_to_anchor=(0.0, -0.3), loc='upper left', borderaxespad=0.1)

# Set overall title
plot_title = f"Telemetry Data Comparison: Fastest Lap \nCar 1 vs Car 2"
plt.suptitle(plot_title, fontsize=20, fontweight='bold')

# Show the plot
plt.show()
