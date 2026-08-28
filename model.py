from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date

db = SQLAlchemy()


# =========================================================
# USER
# =========================================================

class User(db.Model):
    tablename = "user"  # __ ထည့်ထားပါသည်

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

    created_at = db.Column(
        db.DateTime,
        default=datetime.now
    )


# =========================================================
# ASSESSMENT LOG
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

    created_at = db.Column(
        db.DateTime,
        default=datetime.now
    )


# =========================================================
# DAILY USAGE
# =========================================================

class DailyUsage(db.Model):
    tablename = "daily_usage"

    usage_id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.user_id"),
        nullable=False
    )

    total_app_usage_hours = db.Column(
        db.Float,
        nullable=False
    )

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

    log_date = db.Column(
        db.Date,
        default=date.today,
        nullable=False
    )



class Goal(db.Model):
    tablename = "goal"  # မှတ်ချက်။ ။ tablename နှစ်ဖက်စလုံးတွင် underscore နှစ်ခုစီပါရန်

    goal_id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.user_id"),
        nullable=True
    )

    # Target ကို နာရီ (Hours) ဖြင့် ထားရှိသည်
    target_hours = db.Column(
        db.Integer,
        nullable=False
    )

    # Current ကို မိနစ် (Minutes) ဖြင့် ဆက်လက် သိမ်းဆည်းမည် (တွက်ချက်ရ လွယ်ကူစေရန်)
    current_usage = db.Column(
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