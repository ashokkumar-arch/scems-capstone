from flask import Flask, render_template
import boto3
import logging

app = Flask(__name__)

# Initialize Timestream query client
timestream_query = boto3.client('timestream-query')

def get_timestream_endpoint():
    # Describe Timestream endpoints
    response = timestream_query.describe_endpoints()
    return response['Endpoints'][0]['Address']

@app.route('/')
def index():
    try:
        # Set the Timestream endpoint
        endpoint = get_timestream_endpoint()
        timestream_query = boto3.client('timestream-query', endpoint_url=f"https://{endpoint}")

        query_string = "SELECT * FROM \"EnvironmentalMonitoring\".\"SensorData\" ORDER BY time DESC LIMIT 10"
        response = timestream_query.query(QueryString=query_string)

        # Debugging: Log the entire response
        logging.info(f"Timestream query response: {response}")

        rows = []
        column_names = ['DeviceId', 'MeasureName', 'Time', 'Temperature', 'Humidity', 'AirQuality']
        for row in response['Rows']:
            data = {}
            for i, col in enumerate(row['Data']):
                if 'ScalarValue' in col:
                    data[column_names[i]] = col['ScalarValue']
                else:
                    data[column_names[i]] = None
            rows.append(data)

        # Debugging: Log the processed rows
        logging.info(f"Processed rows: {rows}")

        return render_template('index.html', rows=rows)
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        return f"An error occurred: {str(e)}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)

