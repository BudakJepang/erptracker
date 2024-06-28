from flask import Flask, jsonify
from google.cloud import bigquery
import os

app = Flask(__name__)

client = bigquery.Client()

@app.route('/')
def index():
    return "Welcome to the Flask-BigQuery app!"

@app.route('/bigquery')
def query_bigquery():
    query = """
    SELECT name, SUM(number) as total
    FROM `bigquery-public-data.usa_names.usa_1910_2013`
    WHERE state = 'TX'
    GROUP BY name
    ORDER BY total DESC
    LIMIT 10
    """
    query_job = client.query(query)  # API request
    results = query_job.result()  # Wait for the job to complete.

    names = []
    for row in results:
        names.append({"name": row.name, "total": row.total})

    return jsonify(names)

if __name__ == '__main__':
    app.run(debug=True)
