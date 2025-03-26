import pandas as pd
import multiprocessing as mp
import time
import matplotlib.pyplot as plt
import psutil

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

### -------------------------------------- ###
# 4. Evaluating Parallel Processing Efficiency

def process_vessels_sequential(data):
    '''Sequential processing function to detect GPS spoofing in vessels. 
    Note: Even though I am iterating over chunks (grouped by MMSI), each vessel is processed one at a time, using a normal loop.
    So it is not parallel computing because all tasks run in a single process on one CPU core.'''
    
    grouped_vessels = [group for _, group in data.groupby("MMSI")] # Group by vessel MMSI 
    results = [detect_gps_spoofing(vessel) for vessel in grouped_vessels] # Process each vessel sequentially
    return pd.concat(results)

def process_vessels_parallel(data, cpu_count, chunksize=4):
    '''Parallel processing function to detect GPS spoofing in vessels.'''
    grouped_vessels = [group for _, group in data.groupby("MMSI")]
    
    with mp.Pool(processes=cpu_count) as pool:
        spoofing_results = pool.imap_unordered(detect_gps_spoofing, grouped_vessels, chunksize=chunksize)
    
    return pd.concat(spoofing_results)

# Run tests to evaluate the parallel peocessing efficiency
if __name__ == '__main__':
    file_path = "aisdk-2024-08-25.csv"
    _, sample_data = data(file_path) # Since I am comparing processing efficiency, I will only use the sample data

    # Measure sequential execution time
    start_seq = time.time() # Start timer for sequential execution
    sequential_result = process_vessels_sequential(sample_data) 
    end_seq = time.time() # End timer for sequential execution
    sequential_time = end_seq - start_seq # Sequential execution time
    print(f"Sequential Execution Time: {sequential_time:.2f} seconds")

    # Measure parallel execution time
    cpu_count = mp.cpu_count() 
    start_par = time.time() # Start timer for parallel execution
    parallel_result = process_vessels_parallel(sample_data, cpu_count)
    end_par = time.time() # End timer
    parallel_time = end_par - start_par # Parallel execution time
    print(f"Parallel Execution Time ({cpu_count} CPUs): {parallel_time:.2f} seconds")

    # Compute speedup
    speedup = sequential_time / parallel_time
    print(f"Speedup: {speedup:.2f}")

    cpu_counts = [1, 2, 4, 8]
    chunk_sizes = [1, 4, 8, 16]
    results = []

    for cpu in cpu_counts:
        # Measure execution time for different chunk sizes
        for chunk in chunk_sizes:
            start = time.time() # Start timer
            process_vessels_parallel(sample_data, cpu, chunksize=chunk) # Process data in parallel with specified CPU count and chunk size
            end = time.time() # End timer
            exec_time = end - start 
            results.append((cpu, chunk, exec_time)) 
            print(f"CPU: {cpu}, Chunk: {chunk}, Time: {exec_time:.2f} sec")


    # Convert to DataFrame for plotting
    df_results = pd.DataFrame(results, columns=["CPUs", "Chunk Size", "Execution Time"]) 

    # Plot Execution Time vs. CPUs
    plt.figure()
    # Plot each chunk size separately for comparison 
    for chunk in chunk_sizes: 
        subset = df_results[df_results["Chunk Size"] == chunk] 
        plt.plot(subset["CPUs"], subset["Execution Time"], marker="o", label=f"Chunk {chunk}") 
 
    plt.xlabel("Number of CPUs")
    plt.ylabel("Execution Time (seconds)")
    plt.title("Parallel Execution Time vs. CPUs")
    plt.legend()
    plt.grid()
    plt.show()

    def monitor_resources():
        print(f"CPU Usage: {psutil.cpu_percent(interval=1)}%")
        print(f"Memory Usage: {psutil.virtual_memory().percent}%")

    # Call monitor_resources() before and after processing to track changes.
