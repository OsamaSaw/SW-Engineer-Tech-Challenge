import pymongo

myclient = pymongo.MongoClient("mongodb://localhost:27017/")

mydb = myclient["mydatabase"]
mycol = mydb["Patients"]


def store_to_database(json_data):
    print("Data Received To database")
    if mycol.insert_one(json_data):
        return True
    return False
