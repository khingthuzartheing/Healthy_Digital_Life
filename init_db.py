from app import app
from model import db, User, AssessmentLog, DailyUsage, Goal
from werkzeug.security import generate_password_hash

def init_db():
    with app.app_context():
        try:
            # 1. Table အဟောင်း/ပျက်နေသည်များကို ရှင်းထုတ်မည်
            db.drop_all()
            
            # 2. Table အသစ်များကို ပြန်ဆောက်မည်
            db.create_all()
            print("✅ Database tables created successfully!")
            print("📊 Tables:", list(db.metadata.tables.keys()))
            
            # 3. Test user ဖန်တီးမည်
            if not User.query.filter_by(email="admin@example.com").first():
                test_user = User(
                    username=" ",
                    email=" ",
                    password=generate_password_hash(" ")
                )
                db.session.add(test_user)
                db.session.commit()
                print("👤 Test user created: admin@example.com / admin123")
            
            print("✅ Database initialized successfully!")
            
        except Exception as e:
            print(f"❌ Error: {e}")

# Double Underscores (__) ကို အမှန်အတိုင်း ပြင်ထားသည်
if __name__ == "__main__":
    init_db()