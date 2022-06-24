import json
from flask import Flask, request, jsonify
from mongoDB import store_to_database

app = Flask(__name__)


@app.route('/', methods=['POST'])
def create_record():
    record = request.json
    print(record)
    if store_to_database(record):
        return {"Status Code": "201"}
    return {"message": "something went wrong"}


app.run(debug=True)
