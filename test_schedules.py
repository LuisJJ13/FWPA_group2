

from pymongo import MongoClient
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta

def test_schedule_conversion():
    print("=" * 70)
    print("TESTING SCHEDULE STRING TO DATETIME CONVERSION")
    print("=" * 70)
    
    load_dotenv()
    uri = os.getenv('MONGODB_URI')
    db_name = os.getenv('DATABASE_NAME')
    
    print("\n📧 Enter your email:")
    email = input("   Email: ").strip()
    
    if not email:
        print("❌ No email")
        return
    
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=10000)
        db = client[db_name]
        
        schedules_collection = db["Scheduled_meds"]
        
        # Get ALL schedules for this user
        schedules = list(schedules_collection.find({"email": email}))
        
        print(f"\n✅ Found {len(schedules)} schedule(s)")
        
        if not schedules:
            print("❌ No schedules found")
            return
        
        # Date range
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        next_week = today + timedelta(days=7)
        
        print(f"\n📅 Looking for schedules between:")
        print(f"   {today}")
        print(f"   {next_week}")
        
        print(f"\n{'='*70}")
        print("PROCESSING EACH SCHEDULE:")
        print("=" * 70)
        
        scheduled_meds = []
        
        for i, schedule in enumerate(schedules, 1):
            print(f"\n--- Schedule #{i} ---")
            
            schedule_time_str = schedule.get("schedule_time")
            medication = schedule.get("medication")
            
            print(f"Raw schedule_time: '{schedule_time_str}'")
            print(f"Type: {type(schedule_time_str).__name__}")
            print(f"Medication: '{medication}'")
            
            if schedule_time_str:
                try:
                    # Try to convert
                    if isinstance(schedule_time_str, str):
                        print(f"→ Converting string to datetime...")
                        scheduled_time = datetime.fromisoformat(schedule_time_str)
                        print(f"→ Converted to: {scheduled_time}")
                    elif isinstance(schedule_time_str, datetime):
                        print(f"→ Already datetime")
                        scheduled_time = schedule_time_str
                    else:
                        print(f"❌ Unknown type, skipping")
                        continue
                    
                    # Check date range
                    print(f"→ Checking if in range...")
                    print(f"   >= today? {scheduled_time >= today}")
                    print(f"   < next_week? {scheduled_time < next_week}")
                    
                    if today <= scheduled_time < next_week:
                        formatted = scheduled_time.strftime('%B %d at %I:%M %p')
                        scheduled_meds.append({
                            'medicine': medication if medication else 'Unknown',
                            'time': formatted
                        })
                        print(f"✅ ADDED: {medication} - {formatted}")
                    else:
                        if scheduled_time < today:
                            print(f"⚠️  SKIPPED: This is in the past")
                        else:
                            print(f"⚠️  SKIPPED: More than 7 days away")
                        
                except Exception as e:
                    print(f"❌ ERROR converting: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print(f"⚠️  No schedule_time field")
        
        print(f"\n{'='*70}")
        print("FINAL RESULT:")
        print("=" * 70)
        
        print(f"\n📊 Total schedules processed: {len(schedules)}")
        print(f"📊 Schedules in next 7 days: {len(scheduled_meds)}")
        
        if scheduled_meds:
            print(f"\n✅ SHOULD DISPLAY ON PROFILE:")
            for med in scheduled_meds:
                print(f"   • {med['medicine']} - {med['time']}")
            
            print(f"\n{'='*70}")
            print("✅ THIS SHOULD WORK!")
            print("=" * 70)
            
            print("\nIf it's STILL not showing on your profile page:")
            print("\n1. Check Flask console - does it print the DEBUG messages?")
            print("2. Add this BEFORE the return statement in profile_routes.py:")
            print("   print(f'SENDING TO TEMPLATE: {scheduled_medications}')")
            print("\n3. Check HTML template - is it using 'scheduled_medications'?")
            
        else:
            print(f"\n⚠️  No schedules in the next 7 days")
            print("\nEither:")
            print("  1. All schedules are more than 7 days away")
            print("  2. All schedules are in the past")
            print("\nCreate a new schedule for tomorrow to test!")
        
        client.close()
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_schedule_conversion()