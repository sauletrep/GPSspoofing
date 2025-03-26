import pandas as pd
import multiprocessing as mp
import matplotlib.pyplot as plt
import random

def data(file_path):
    '''Function to read data and infer dtypes, then load full dataset.'''
    # Step 1: Read a small sample with Pandas to infer dtypes since collumns have mixed data types and many NaNs
    infersample_df = pd.read_csv(file_path, nrows=1000) # Read first 1000 rows 
    inferred_dtypes = infersample_df.dtypes.astype(str).to_dict() # Infer dtypes from small sample data

    # Step 2: Load the sample data with inferred dtypes
    sample_df = pd.read_csv(file_path, nrows=10000000, dtype=inferred_dtypes) # Read first 10,000,000 rows with inferred dtypes
    sample_df.columns = sample_df.columns.str.strip("# ") # Remove trailing whitespaces and "#" from column names

    # Step 3: Load full dataset with panda using inferred dtypes
    df = pd.read_csv(file_path, dtype=inferred_dtypes) # Read full dataset with inferred dtypes
    df.columns = df.columns.str.strip("# ") 

    # Show column names 
    print("Column Names:") 
    print(df.columns)

    # A small preview of data
    print("\nData Preview:")
    print(df.head())
    
    return df, sample_df

def iqr_outliers(series):
    '''Function to detect outliers using the Interquartile Range (IQR) method.'''
    Q1 = series.quantile(0.25)  # Calculate the first quartile
    Q3 = series.quantile(0.75) # Calculate the third quartile
    IQR = Q3 - Q1 # Calculate the Interquartile Range (IQR) 
    lower_bound = Q1 - 1.5 * IQR   # Calculate the lower bound
    upper_bound = Q3 + 1.5 * IQR   # Calculate the upper bound
    return (series < lower_bound) | (series > upper_bound) # Return (a boolean mask of) outliers
    
def plot_spoofing(vessel_data, spoofing_events):
    '''Function to plot vessel path and GPS spoofing events.'''
    plt.figure()
    plt.plot(vessel_data["Longitude"], vessel_data["Latitude"], label="Vessel Path", color="blue", alpha=0.5) # Vessel path
    plt.scatter(spoofing_events["Longitude"], spoofing_events["Latitude"], color="red", label="Potential Spoofing", marker="x") # Spoofing events
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.title(f"Vessel Path & GPS Spoofing Events", vessel_data["MMSI"].iloc[0])
    plt.legend()
    plt.show()

def detect_gps_spoofing(vessel_data):
    '''Function to detect GPS spoofing. Checks for sudden unrealistic jumps in latitude/longitude or speed.'''
    vessel_data["Timestamp"] = pd.to_datetime(vessel_data["Timestamp"], dayfirst=True) # Ensure Timestamp is a datetime object
    vessel_data = vessel_data.sort_values(by="Timestamp")  # Sort by time since the data is split before processing 
    
    # Calculate time difference between consecutive rows. Will be important calibrating the changes in position and speed
    vessel_data["dt"] = vessel_data["Timestamp"].diff().dt.total_seconds() 
    
    # Calculate absolute difference in Latitude, Longitude, and Speed
    vessel_data["LatDiff"] = vessel_data["Latitude"].diff().abs()
    vessel_data["LongDiff"] = vessel_data["Longitude"].diff().abs()
    vessel_data["SpeedChange"] = vessel_data["SOG"].diff().abs()

    # Avoid NaN issues
    vessel_data = vessel_data.dropna()

    # Finding potential spoofing events using IQR method
    vessel_data["LatOutlier"] = iqr_outliers(vessel_data["LatDiff"])
    vessel_data["LongOutlier"] = iqr_outliers(vessel_data["LongDiff"])
    vessel_data["SpeedOutlier"] = iqr_outliers(vessel_data["SpeedChange"])

    # Flagging potential spoofing
    spoofing_events = vessel_data[vessel_data["LatOutlier"] | 
                                  vessel_data["LongOutlier"] | 
                                  vessel_data["SpeedOutlier"]]

    
    #plot_spoofing(vessel_data, spoofing_events) # Uncomment to plot spoofing events Note: It will plot for each vessel
    
    return spoofing_events

def process_vessels_parallel(data, cpu_count):
    # Group by vessel MMSI
    grouped_vessels = [group for _, group in data.groupby("MMSI")]
    
    # Detect GPS spoofing in parallel
    with mp.Pool(processes=cpu_count) as pool:
        spoofing_results = pool.map(detect_gps_spoofing, grouped_vessels, chunksize=4)
        # grouped_vessels is split into chunks of 4 for each worker process to balance the workload
        #   whilst using simplified thresholds to detect spoofing

    # Combine results from all workers into a single DataFrame
    final_spoofing_events = pd.concat(spoofing_results) 

    return final_spoofing_events

if __name__ == '__main__':
    print("Number of processors: ", mp.cpu_count())

    # Path to locally stored dataset
    file_path = "aisdk-2024-08-25.csv"

    # Download and preview data, both full and sample
    full_data, sample_data = data(file_path)

    # Process file to detect GPS spoofing events in parallel with all available CPU cores (processeors)
    spoofing_df = process_vessels_parallel(full_data, mp.cpu_count())

    # Display results
    print(f"Number of potential GPS Spoofing Events", len(spoofing_df))
    print(f"Potential GPS Spoofing Events:", spoofing_df.head())