import dask.dataframe as dd
import pandas as pd
import numpy as np
import multiprocessing as mp

def data(file_path):
    # Step 1: Read a small sample with Pandas to infer dtypes
    sample_df = pd.read_csv(file_path, nrows=1000)
    inferred_dtypes = sample_df.dtypes.astype(str).to_dict()

    # Step 2: Load the sample data with inferred dtypes
    sample_df = pd.read_csv(file_path, nrows=10000000, dtype=inferred_dtypes)
    sample_df.columns = sample_df.columns.str.strip("# ")

    # Step 3: Load full dataset with Dask using inferred dtypes
    df = dd.read_csv(file_path, dtype=inferred_dtypes)
    df.columns = df.columns.str.strip("# ")

    # Show column names and a small preview
    #print("Column Names:")
    #print(df.columns)

    # Compute a small sample to check data
    #print("\nSample Data:")
    #print(df.head())
    
    return df, sample_df


def detect_gps_spoofing(vessel_data):
    '''Function to detect GPS spoofing. Checks for sudden unrealistic jumps in latitude/longitude or speed.'''
    vessel_data["Timestamp"] = pd.to_datetime(vessel_data["Timestamp"], dayfirst=True) # Ensure Timestamp is a datetime object
    vessel_data = vessel_data.sort_values(by="Timestamp")  # Sort by time since the data is split before processing 

    vessel_data["TimeDiff"] = vessel_data["Timestamp"].diff().dt.total_seconds()#
    vessel_data["LatDiff"] = vessel_data["Latitude"].diff().abs()
    vessel_data["LongDiff"] = vessel_data["Longitude"].diff().abs()
    vessel_data["SpeedChange"] = vessel_data["SOG"].diff().abs()
    print(f"head start", mean(vessel_data["LatDiff"]/vessel_data["TimeDiff"]), "head stop")
    print(f"TYPE", type(vessel_data["LatDiff"]))
    #print(f"np", np.array(vessel_data["TimeDiff"])[:5])
    #print(vessel_data["LongDiff"])
    #print(vessel_data["SpeedChange"])
    #fake_event = pd.DataFrame({"LatDiff": [1], "LongDiff": [1], "SpeedChange": [1], "TimeDiff": [1]})
    #vessel_data = pd.concat([vessel_data, fake_event], ignore_index=True)
    #print("Vessel Data After Adding Fake Event:")
    #print(vessel_data.tail(5))  # Show last 5 rows, including fake event


    # Flagging unrealistic movements (adjust thresholds as needed)
    spoofing_events = vessel_data[(vessel_data["LatDiff"] > 1) |
                                  (vessel_data["LongDiff"] > 1) |
                                  (vessel_data["SpeedChange"] > 1)]
    #print(f"Number of spoofing events detected: {len(spoofing_events)}")
    #print("Spoofing Events Detected (First 10 Rows):")
    #print(spoofing_events.head(10))
    return spoofing_events

def process_vessels_parallel(data, cpu_count):
    # Group by vessel MMSI
    grouped_vessels = [group for _, group in data.groupby("MMSI")]
    print(f"Total groups: {len(grouped_vessels)}")
    #test_vessel = grouped_vessels[0]  # Pick the first group
    #print(f"test vessel:", {len(test_vessel)})
    #print(f"HERE", detect_gps_spoofing(test_vessel))
    #norway = detect_gps_spoofing(test_vessel)
    
    with mp.Pool(processes=cpu_count) as pool:
        spoofing_results = pool.map(detect_gps_spoofing, grouped_vessels)

    # Combine results
    final_spoofing_events = pd.concat(spoofing_results)
    return final_spoofing_events #norway 

if __name__ == '__main__':
    print("Number of processors: ", mp.cpu_count())

    # Path to your locally stored dataset
    file_path = "aisdk-2024-08-25.csv"

    # Download and preview data
    full_data, sample_data = data(file_path)

    # Process file to detect GPS spoofing
    spoofing_df = process_vessels_parallel(sample_data, mp.cpu_count())

    # Display results
    print("Potential GPS Spoofing Events:")
    print(spoofing_df.head())
    print(f"length",len(spoofing_df))