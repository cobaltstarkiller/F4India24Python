import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import mpld3  # Use mpld3 for interactivity
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
    fastest_lap_index = laps_array.index(fastest_lap_time)
    
    start_time_stamp = sum(segment_times[:fastest_lap_index])
    end_time_stamp = sum(segment_times[:fastest_lap_index + 1])
    
    # Filter telemetry data for the fastest lap
    telemetry_FL = telemetry_df[(telemetry_df['Time'] >= start_time_stamp) & (telemetry_df['Time'] <= end_time_stamp)]
    
    # Adjust the distance calculation to be relative to the start of the fastest lap
    start_distance = telemetry_FL['Distance on GPS Speed'].iloc[0]
    telemetry_FL['Distance'] = telemetry_FL['Distance on GPS Speed'] - start_distance
    
    return telemetry_FL

# Helper function to classify telemetry actions more accurately
def classify_actions(telemetry_FL):
    throttle_threshold = 90
    brake_pos_median = telemetry_FL['Brake Pos'].median()
    brake_press_median = telemetry_FL['Brake Press'].median()
    
    # Update to classify actions more accurately
    telemetry_FL['Action'] = 'Turning'  # Default action is Turning
    telemetry_FL.loc[telemetry_FL['Throttle Pos'] > throttle_threshold, 'Action'] = 'Full Throttle'
    telemetry_FL.loc[(telemetry_FL['Brake Pos'] > brake_pos_median) & 
                     (telemetry_FL['Brake Press'] > brake_press_median), 'Action'] = 'Brake'

    return telemetry_FL

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

# Main function to generate plot
def generate_plot():
    # Select files
    file_path_car1, file_path_car2 = select_files()

    # Load data for both cars
    metadata_df_car1, telemetry_df_car1 = load_data(file_path_car1)
    metadata_df_car2, telemetry_df_car2 = load_data(file_path_car2)

    # Get fastest lap telemetry for both cars
    telemetry_FL_car1 = get_fastest_lap_data(metadata_df_car1, telemetry_df_car1)
    telemetry_FL_car2 = get_fastest_lap_data(metadata_df_car2, telemetry_df_car2)

    # Classify actions for both cars
    telemetry_FL_car1 = classify_actions(telemetry_FL_car1)
    telemetry_FL_car2 = classify_actions(telemetry_FL_car2)
    
    telemetry_FL_car1.to_csv('car1 actions mpld3.csv', index=False)
    telemetry_FL_car2.to_csv('car2 actions mpld3.csv', index=False)

    # Extract driver and vehicle information
    driver_name_car1 = metadata_df_car1.iloc[3, 1]  # Assuming 'Racer' is the first row
    car_number_car1 = metadata_df_car1.iloc[2, 1]  # Assuming 'Vehicle' is the second row

    driver_name_car2 = metadata_df_car2.iloc[3, 1]  # Assuming 'Racer' is the first row
    car_number_car2 = metadata_df_car2.iloc[2, 1]  # Assuming 'Vehicle' is the second row

    # Create subplots
    fig, ax = plt.subplots(3, figsize=(15, 10), gridspec_kw={'height_ratios': [3, 1, 1]}, sharex=True)
    fig.suptitle(f"Telemetry Data Comparison: Fastest Lap\nCar 1: {driver_name_car1} vs Car 2: {driver_name_car2}", fontsize=16)

    # Plot Speed for both cars (Top Plot)
    ax[0].plot(telemetry_FL_car1['Distance'], telemetry_FL_car1['GPS Speed'], label=f'{driver_name_car1} Speed', color='cyan')
    ax[0].plot(telemetry_FL_car2['Distance'], telemetry_FL_car2['GPS Speed'], label=f'{driver_name_car2} Speed', color='orange')
    ax[0].set_ylabel('Speed (km/h)', fontsize=12)
    ax[0].legend(loc='upper right')

    # Define action colors
    action_colors = {'Brake': 'red', 'Full Throttle': 'green', 'Turning': 'yellow'}

    # Plot telemetry actions for Car 1 (Middle Plot)
    for action_type, color in action_colors.items():
        car1_actions = telemetry_FL_car1[telemetry_FL_car1['Action'] == action_type]
        ax[1].barh([1] * len(car1_actions), car1_actions['Distance'].diff().fillna(1), left=car1_actions['Distance'], color=color, label=action_type)
    ax[1].set_yticks([])
    ax[1].set_ylabel(f"{driver_name_car1} Actions", fontsize=12)

    # Plot telemetry actions for Car 2 (Bottom Plot)
    for action_type, color in action_colors.items():
        car2_actions = telemetry_FL_car2[telemetry_FL_car2['Action'] == action_type]
        ax[2].barh([1] * len(car2_actions), car2_actions['Distance'].diff().fillna(1), left=car2_actions['Distance'], color=color, label=action_type)
    ax[2].set_yticks([])
    ax[2].set_xlabel('Distance (m)', fontsize=12)
    ax[2].set_ylabel(f"{driver_name_car2} Actions", fontsize=12)

    # Use mpld3 to display the interactive plot
    mpld3.show()

# Run the plot generation
generate_plot()
