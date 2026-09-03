from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date

db = SQLAlchemy()


# =========================================================
# USER MODEL (Dataset: User_ID, Age, Gender)
# =========================================================

class User(db.Model):
    __tablename__ = "user"

    user_id = db.Column(
        db.Integer,
        primary_key=True
    )

    username = db.Column(
        db.String(50),
        nullable=False,
        unique=True
    )

    email = db.Column(
        db.String(100),
        nullable=False,
        unique=True
    )

    password = db.Column(
        db.String(255),
        nullable=False
    )

    # Dataset ထဲပါသော User ၏ အသက်နှင့် ကျား/မ (Gender) ကို ထည့်သွင်းခြင်း
    age = db.Column(
        db.Integer,
        nullable=True
    )

    gender = db.Column(
        db.String(20),
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.now
    )


# =========================================================
# ASSESSMENT LOG MODEL (Dataset: Digital_Wellbeing_Score, Awareness_Level)
# =========================================================

class AssessmentLog(db.Model):
    tablename = "assessment_log"

    log_id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.user_id"),
        nullable=False
    )

    wellbeing_score = db.Column(
        db.Float,
        nullable=False
    )

    awareness_level = db.Column(
        db.String(50),
        nullable=False
    )

    # အသက် နှင့် ကျား/မ ဒေတာများ ဝင်ရန် အသစ်ထည့်ရမည့် ကော်လံများ
    age = db.Column(
        db.Float,
        nullable=True
    )

    gender = db.Column(
        db.String(20),
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.now
    )

# =========================================================
# DAILY USAGE MODEL (Dataset ၏ Column အားလုံးနှင့် ကိုက်ညီရန်)
# =========================================================

class DailyUsage(db.Model):
    __tablename__ = "daily_usage"

    usage_id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.user_id"),
        nullable=False
    )

    # app1.txt နှင့် အတိအကျ ကိုက်ညီစေရန် ပြင်ဆင်ထားသော Column နာမည်များ
    screen_time_hours = db.Column(
        db.Float,
        nullable=False
    )

    social_media_hours = db.Column(
        db.Float,
        nullable=False
    )

    gaming_hours = db.Column(
        db.Float,
        nullable=False
    )

    sleep_hours = db.Column(
        db.Float,
        nullable=False
    )

    notification_count = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    number_of_apps_used = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    physical_activity = db.Column(
        db.Float,
        nullable=False,
        default=0.0
    )

    night_time_usage_hours = db.Column(
        db.Float,
        nullable=False,
        default=0.0
    )

    log_date = db.Column(
        db.Date,
        default=date.today,
        nullable=False
    )


# =========================================================
# GOAL MODEL
# =========================================================

class Goal(db.Model):
    tablename = "goal"

    goal_id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.user_id"),
        nullable=True
    )

    target_hours = db.Column(
        db.Integer,
        nullable=False
    )

    # 🟢 ဤနေရာတွင် current_usage ကော်လံကို ထည့်ပေးပါ
    current_usage = db.Column(
        db.Integer,
        default=0,
        nullable=False
    )

    current_minutes = db.Column(
        db.Integer,
        default=0,
        nullable=False
    )

    description = db.Column(
        db.String(200),
        nullable=False
    )

    is_completed = db.Column(
        db.Boolean,
        default=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.now
    )

    # 🟢 1. နာရီ သီးသန့် ထုတ်ယူရန် Property (ဥပမာ - 130 မိနစ်ဆိုလျှင် 2 နာရီရမည်)
    @property
    def current_hour_part(self):
        return self.current_minutes // 60

    # 🟢 2. နာရီမပြည့်သော ကျန်မိနစ်များကို ထုတ်ယူရန် Property (ဥပမာ - 130 မိနစ်ဆိုလျှင် 10 မိနစ်ကျန်မည်)
    @property
    def current_minute_part(self):
        return self.current_minutes % 60