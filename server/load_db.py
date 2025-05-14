import pymongo
import gridfs

MODELS = "model_pts"
MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "billsmart"

client = pymongo.MongoClient(MONGO_URI)
db = client[DB_NAME]
fs = gridfs.GridFS(db)

print("✅ Connected to MongoDB")


def upload_model(store_name, model_path):
    """Upload a model file and link it to a store."""
    with open(model_path, "rb") as f:
        model_id = fs.put(f, filename=f"{store_name}_model.pt")

    # Update or insert store information
    store_data = {
        "name": store_name,
        "address": "123, Market Street, City",
        # Example item prices
        "items": {"Apple": 50, "Banana": 20, "Milk": 60},
        "model_ref": model_id  # Store the reference to model.pt
    }

    db.stores.update_one({"name": store_name}, {
                         "$set": store_data}, upsert=True)
    print(f"✅ Model stored for {store_name} with ID: {model_id}")


# Example usage
upload_model("XYZ Supermarket", f"./{MODELS}/XYZ_model.pt")
# upload_model("ABC Mart", f"./{MODELS}/ABC_model.pt")
