import json
from flask import Flask, request, jsonify
from mongoDB import store_to_database

app = Flask(__name__)


@app.route('/', methods=['PUT'])
def create_record():
    record = json.load(request.data)
    print(record)
    if store_to_database(record):
        return jsonify(record)
    return {"message": "something went wrong"}


@app.route('/', methods=['GET'])
def query_records():
    return jsonify({'msg': 'Testing the server'})


app.run(debug=True)
