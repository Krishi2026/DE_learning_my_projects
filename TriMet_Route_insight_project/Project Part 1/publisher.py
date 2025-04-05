import csv
import json
import requests
from google.cloud import pubsub_v1
import os

# Set Google Application Credentials
path = '/home/sumanasn/.config/gcloud/application_default_credentials.json'
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = path
count = 0  # Global count to track the number of messages published

def read_vehicle_ids_from_csv(csv_file):
    """Read vehicle IDs from a specific column in the CSV file."""
    vehicle_ids = []
    try:
        with open(csv_file, "r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                vehicle_id = row.get("Whimsy")  # Assumes "Whimsy" is the column name
                if vehicle_id:
                    vehicle_ids.append(vehicle_id)
    except Exception as e:
        print(f"Error reading vehicle IDs from CSV: {e}")
    return vehicle_ids

def retrieve_and_publish_data(vehicle_ids):
    """Retrieve data from the API for the given vehicle IDs and publish to Pub/Sub."""
    project_id = "dataengineeringproject-420806"
    topic_id = "my-vehicle"
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(project_id, topic_id)
    global count
    for vehicle_id in vehicle_ids:
        try:
            url = f"https://busdata.cs.pdx.edu/api/getBreadCrumbs?vehicle_id={vehicle_id}"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                for message in data:
                    message_bytes = json.dumps(message).encode('utf-8')
                    future = publisher.publish(topic_path, data=message_bytes)
                    count += 1
                    future.result()
                print(f"Published messages for vehicle ID {vehicle_id} to {topic_path}.")
            else:
                print(f"Failed to retrieve data for vehicle ID {vehicle_id}. Status code: {response.status_code}")
        except Exception as e:
            print(f"Error retrieving or publishing data for vehicle ID {vehicle_id}: {e}")

def main():
    csv_file = "vehicle_ids.csv"  # Path to the CSV file
    vehicle_ids = read_vehicle_ids_from_csv(csv_file)
    try:
        retrieve_and_publish_data(vehicle_ids)
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # This block ensures that the total count is always printed, regardless of any errors.
        print(f"Total number of messages received: {count}")

if __name__ == "__main__":
    main()
