from pymongo import MongoClient
from dotenv import load_dotenv
import hashlib
import os

load_dotenv()

# ------------------------
# USER MODEL
# ------------------------
class UserModel:
    def __init__(self, collection):
        self.collection = collection

    def create_user(self, user):
        user["email"] = user["email"].strip().lower()
        return self.collection.insert_one(user).inserted_id

    def get_user_by_email(self, email):
        return self.collection.find_one({"email": email.strip().lower()})

    def update_user(self, email, update_data):
        email = email.strip().lower()
        return self.collection.update_one({"email": email}, {"$set": update_data})


# ------------------------
# LOGIN MODEL
# ------------------------
class LoginModel:
    def __init__(self, collection):
        self.collection = collection

    def create_login(self, email, password):
        email = email.strip().lower()
        hashed_pw = hashlib.sha256(password.encode()).hexdigest()

        login_doc = {"email": email, "password": hashed_pw}
        return self.collection.insert_one(login_doc).inserted_id
    
    def get_user_by_email(self, email):
        return self.collection.find_one({"email": email.strip().lower()})

    def authenticate(self, email, password):
        email = email.strip().lower()
        hashed_pw = hashlib.sha256(password.encode()).hexdigest()
        return self.collection.find_one({"email": email, "password": hashed_pw})

    def update_password(self, email, new_password):
        email = email.strip().lower()
        hashed_pw = hashlib.sha256(new_password.encode()).hexdigest()
        return self.collection.update_one(
            {"email": email},
            {"$set": {"password": hashed_pw}}
        )


# ------------------------
# SAVED MEDICATION MODEL
# ------------------------
class SavedMedsModel:
    def __init__(self, collection):
        self.collection = collection
        self.collection.create_index([("email", 1)("medication", 1)], unique=True)

    def save_medication(self, email, medication):
        email = email.strip().lower()
        entry = {"email": email, "medication": medication}
        try:
            return self.collection.insert_one(entry).inserted_id
        except Exception as e:
            print(f"Error saving medication: {e}")
            return None
    def get_meds_by_email(self, email):
        """Fetch all saved medicines for a given user email"""
        email = email.strip().lower()
        return list(self.collection.find({"email": email}))

    def remove_medication(self, email, medication):
        email = email.strip().lower()
        result = self.collection.delete_one({"email": email, "medication": medication})
        return result.deleted_count > 0

# ------------------------
# SCHEDULED MEDS MODEL
# ------------------------
class ScheduledMedsModel:
    def __init__(self, collection):
        self.collection = collection

    def schedule_medication(self, email, medication, schedule_time):
        email = email.strip().lower()
        entry = {
            "email": email,
            "medication": medication,
            "schedule_time": schedule_time
        }
        return self.collection.insert_one(entry).inserted_id

    def get_schedule_by_email(self, email):
        email = email.strip().lower()
        return list(self.collection.find({"email": email}))


# ------------------------
# DB WRAPPER
# ------------------------
class DB:
    def __init__(self):
        mongo_uri = os.getenv("MONGO_URI")
        if not mongo_uri:
            raise ValueError("MONGO_URI not set in environment")

        self.client = MongoClient(mongo_uri)
        db = self.client["MedInfo"]

        self.users = UserModel(db["User_info"])
        self.logins = LoginModel(db["Login_info"])
        self.saved_meds = SavedMedsModel(db["Saved_meds"])
        self.scheduled_meds = ScheduledMedsModel(db["Scheduled_meds"])

    def authenticate_user(self, email, password):
        return self.logins.authenticate(email, password)

    def get_user_by_email(self, email):
        return self.users.get_user_by_email(email)

    def close(self):
        self.client.close()