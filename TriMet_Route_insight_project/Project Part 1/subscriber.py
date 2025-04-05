import json
import datetime
from google.cloud import pubsub_v1
import os

def main():
    # Set Google Cloud credentials
    credential_path = "/home/sumanasn/.config/gcloud/application_default_credentials.json"
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credential_path

    # Initialize subscriber
    project_id = "dataengineeringproject-420806"
    subscription_id = "my-sub"
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(project_id, subscription_id)

    received_messages = []
    current_day = datetime.datetime.now().strftime("%Y%m%d")
    message_count = 0  # Initialize the message count

    def write_messages_to_file():
        nonlocal message_count
        if received_messages:  # Check if there are messages to write
            file_path = f'received_msg/rmsg_{current_day}.json'
            count_file_path = f'received_msg/count_{current_day}.txt'  # File to keep count of messages
            with open(file_path, 'a') as f:
                for message in received_messages:
                    f.write(json.dumps(message) + '\n')
            with open(count_file_path, 'w') as cf:
                cf.write(f'Total messages received on {current_day}: {message_count}\n')
            received_messages.clear()

    def callback(message):
        nonlocal current_day, message_count
        data = json.loads(message.data.decode('utf-8'))
        received_messages.append(data)
        message_count += 1  # Increment the message count
        message.ack()

        # Check if the day has changed
        new_day = datetime.datetime.now().strftime("%Y%m%d")
        if new_day != current_day:
            write_messages_to_file()  # Write messages and count to file
            current_day = new_day
            message_count = 0  # Reset message count for the new day

    # Listen for messages
    streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)
    print(f"Listening for messages on {subscription_path}...")
    try:
        streaming_pull_future.result()  # Block indefinitely
    except Exception as e:
        streaming_pull_future.cancel()
        print(f"An error occurred: {e}")
    finally:
        write_messages_to_file()  # Write remaining messages and count when the process is stopped

if __name__ == "__main__":
    main()
