import os
import json
import pandas as pd
import psycopg2
from datetime import datetime, timedelta
from scipy.stats import zscore
from io import StringIO

# Directory where JSON files are stored
directory_path = 'received_data/20240512.json'

# Columns expected in the JSON data
columns = ['EVENT_NO_TRIP', 'ACT_TIME', 'OPD_DATE', 'VEHICLE_ID', 'METERS', 'GPS_LATITUDE', 'GPS_LONGITUDE', 'GPS_SATELLITES', 'GPS_HDOP']

def convert_to_timestamp(row):
    date_part = datetime.strptime(row['OPD_DATE'].split(':')[0], '%d%b%Y')
    full_timestamp = date_part + timedelta(seconds=int(row['ACT_TIME']))
    return full_timestamp

def calculate_speed(data):
    data['TIMESTAMP'] = data.apply(convert_to_timestamp, axis=1)
    data.sort_values(by=['EVENT_NO_TRIP', 'TIMESTAMP', 'VEHICLE_ID'], inplace=True)
    data['SPEED'] = data.groupby('EVENT_NO_TRIP')['METERS'].diff() / data.groupby('EVENT_NO_TRIP')['TIMESTAMP'].diff().dt.total_seconds()
    data['SPEED'] = data['SPEED'].fillna(method='bfill')
    data['SPEED'] = data['SPEED'].clip(lower=0)
    return data

# Function to process each JSON file
def process_json_file(file_path):
    """Process a JSON file that may contain multiple JSON objects per line."""
    data_rows = []  # List to store valid rows
    with open(file_path, 'r') as file:
        for line_number, line in enumerate(file, 1):
            try:
                item = json.loads(line.strip())
                new_row = {col: item.get(col, None) for col in columns}

                # Validate latitude and longitude
                lat = new_row['GPS_LATITUDE']
                lon = new_row['GPS_LONGITUDE']
                if lat is None or lon is None:
                    raise ValueError(f"Line {line_number}: Latitude or longitude cannot be None.")
                lat, lon = float(lat), float(lon)
                if not (45.0 <= lat <= 46.0):
                    raise ValueError(f"Line {line_number}: Latitude {lat} out of bounds.")
                if not (-124.0 <= lon <= -122.0):
                    raise ValueError(f"Line {line_number}: Longitude {lon} out of bounds.")

                # Validate meters
                meters = new_row['METERS']
                if meters is not None and float(meters) < 0:
                    raise ValueError(f"Line {line_number}: Negative meters value.")

                # Ensure EVENT_NO_TRIP column exists
                if 'EVENT_NO_TRIP' not in new_row or new_row['EVENT_NO_TRIP'] is None:
                    raise ValueError(f"Line {line_number}: EVENT_NO_TRIP column is missing or None.")

                data_rows.append(new_row)

            except json.JSONDecodeError as e:
                print(f"Error decoding JSON on line {line_number}: {e}")
            except ValueError as e:
                print(e)
                continue

    df_local = pd.DataFrame(data_rows)  # Convert collected rows to DataFrame at once
    return df_local

def get_db_connection():
    try:
        connection = psycopg2.connect(
            dbname="whimsy_data",
            user="postgres",
            password="Maskdep",
            host="localhost"
        )
        print("Database connection established")
        return connection
    except Exception as e:
        print(f"Failed to connect to database: {e}")


def copy_from_stringio(conn, df, table):
    if 'trip_id' not in df.columns:
        raise ValueError("Attempting to insert data but trip_id is missing")
    buffer = StringIO()
    df.to_csv(buffer, header=False, index=False, sep='\t')
    buffer.seek(0)
    cursor = conn.cursor()
    try:
        cursor.copy_from(buffer, table, sep='\t', columns=('tstamp', 'latitude', 'longitude', 'speed', 'trip_id'))
        conn.commit()
    except Exception as error:
        print(f"Error: {error}")
        conn.rollback()
    finally:
        cursor.close()
        buffer.close()

def insert_trip_data(df, conn):
    # Convert OPD_DATE to datetime
    df['NEW_OPD_DATE'] = pd.to_datetime(df['OPD_DATE'].str.split(':').str[0], format='%d%b%Y')
    df['DAY_OF_WEEK'] = df['NEW_OPD_DATE'].dt.dayofweek

    # Mapping day of the week to service key
    day_names = {0: 'Weekday', 1: 'Weekday', 2: 'Weekday', 3: 'Weekday', 4: 'Weekday', 5: 'Saturday', 6: 'Sunday'}
    df['DAY_NAME'] = df['DAY_OF_WEEK'].map(day_names)

    # Prepare data for insertion using the new column names already assigned before calling this function
    df_trip = df[['trip_id', 'vehicle_id', 'DAY_NAME']].drop_duplicates()
    df_trip = df_trip.rename(columns={'DAY_NAME': 'service_key'})
    df_trip['route_id'] = 0  # Default value
    df_trip['direction'] = 'Out'  # Default value

    # Database insertion
    cursor = conn.cursor()
    for _, row in df_trip.iterrows():
        cursor.execute("""
            INSERT INTO Trip (trip_id, route_id, vehicle_id, service_key, direction)
            VALUES (%s, %s, %s, %s, %s) ON CONFLICT (trip_id) DO NOTHING;
        """, (row['trip_id'], row['route_id'], row['vehicle_id'], row['service_key'], row['direction']))
    conn.commit()
    cursor.close()


def save_data(df):
    print('transforming')
    if df.empty:
        print("No valid data to save for today.")
        return
    # Calculate speed and assign it to the DataFrame
    df = calculate_speed(df)

    # Rename DataFrame columns to match the database schema
    df = df.rename(columns={
        'TIMESTAMP': 'tstamp',
        'GPS_LATITUDE': 'latitude',
        'GPS_LONGITUDE': 'longitude',
        'SPEED': 'speed',
        'EVENT_NO_TRIP': 'trip_id',
        'VEHICLE_ID':'vehicle_id'
    })

    try:

        # Check and print negative speeds
        if (df['speed'] < 0).any():
            print("Negative speed records:")
            print(df[df['speed'] < 0])

        # Calculate z-scores for speeds to detect outliers
        df['z_scores'] = zscore(df['speed'])
        if (df['z_scores'].abs() > 3).any():
            print("Significant outliers in speeds:")
            print(df[df['z_scores'].abs() > 3])
        df.drop(columns='z_scores', inplace=True)  # Remove z_scores after checking

        # Check for trips with average speeds exceeding 30 meters per second
        high_speed_trips = df.groupby('trip_id')['speed'].mean() > 30
        if high_speed_trips.any():
            print("Trips with average speeds exceeding 30 meters per second:")
            print(df[df['trip_id'].isin(high_speed_trips[high_speed_trips].index)])


        # Verify chronological order of timestamps within each trip
        if not df.groupby('trip_id').apply(lambda x: x['tstamp'].is_monotonic_increasing).all():
            print("Non-chronological timestamp records:")
            problematic_trips = df.groupby('trip_id').filter(lambda x: not x['tstamp'].is_monotonic_increasing)
            print(problematic_trips)

        # Check for duplicate timestamps within the same trip
        if df.duplicated(subset=['tstamp', 'trip_id']).any():
            print("Duplicate timestamp records:")
            print(df[df.duplicated(subset=['tstamp', 'trip_id'],keep=False)])
            df=df.drop_duplicates(subset=['tstamp','trip_id'],keep='first')

        # Check median speed constraint
        median_speed = df['speed'].median()
        below_median = df[df['speed'] < median_speed]
        if below_median.shape[0] <= df.shape[0] / 2:
            print("More than 50% of breadcrumb records do not have speeds below the median speed:")
            print(df[df['speed'] >= median_speed])

        # Insert data into the database
        conn = get_db_connection()
        insert_trip_data(df,conn)
        copy_from_stringio(conn, df[['tstamp', 'latitude', 'longitude', 'speed', 'trip_id']], 'breadcrumb')

    except Exception as e:
        print(f"Error during processing: {e}")
    finally:
        if 'conn' in locals():
            conn.close()
        print("Data processed successfully.")
        df = pd.DataFrame(columns=['tstamp', 'latitude', 'longitude', 'speed', 'trip_id'])  # Clear DataFrame for next batch


if __name__ == '__main__':
    try:
        df = process_json_file(directory_path)
        if not df.empty:
            save_data(df)
        else:
            print("No valid data to process.")
    except Exception as e:
        print("An error occurred during processing:")
        print(e)
    finally:
        print("Processing complete.")
