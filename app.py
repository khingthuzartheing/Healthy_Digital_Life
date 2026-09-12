from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    session,
    redirect,
    url_for,
    flash
)

from functools import wraps

from model import (
    db,
    User,
    AssessmentLog,
    DailyUsage,
    Goal
)

import pickle
import numpy as np
import os
import qrcode
import base64
import io

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)


# =========================================================
# FLASK APP
# =========================================================

app = Flask(__name__)

app.secret_key = "digital_wellbeing_secret_key_change_this"
app.secret_keys = "your_secret_key_here"

# =========================================================
# SQLITE DATABASE CONFIGURATION
# =========================================================

basedir = os.path.abspath(
    os.path.dirname(__file__)
)

app.config["SQLALCHEMY_DATABASE_URI"] = (
    "sqlite:///"
    + os.path.join(
        basedir,
        "digital_wellbeing.db"
    )
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = False

db.init_app(app)


# =========================================================
# RANDOM FOREST MODEL CONFIGURATION
# =========================================================

MODEL_FILE = "digital_wellbeing_model.pkcls"
model = None


# =========================================================
# LOAD RANDOM FOREST MODEL
# =========================================================

def load_model():
    global model

    model_path = os.path.join(
        basedir,
        MODEL_FILE
    )

    print("")
    print("==========================================")
    print("          RANDOM FOREST MODEL")
    print("==========================================")

    if not os.path.exists(model_path):
        print("❌ MODEL FILE NOT FOUND")
        print("📁 Expected path:")
        print(model_path)
        print("==========================================")
        model = None
        return

    try:
        with open(
            model_path,
            "rb"
        ) as file:
            model = pickle.load(file)

        print(
            "✅ Random Forest Model Loaded Successfully!"
        )
        print(
            "📁 Model:",
            model_path
        )
        
        print(
            "📌 Model Type:",
            type(model).__name__
        )

        # Show model classes if available
        if hasattr(model, "classes_"):
            print(
                "🎯 Model Classes:",
                model.classes_
            )

        # Show feature names if available
        if hasattr(
            model,
            "feature_names_in_"
        ):
            print(
                "📊 Feature Names:",
                list(
                    model.feature_names_in_
                )
            )

        print("==========================================")

    except Exception as e:
        print(
            "❌ MODEL LOAD ERROR"
        )
        print(
            "❌",
            str(e)
        )
        print("==========================================")
        model = None

# =========================================================
# CREATE DATABASE TABLES
# =========================================================

with app.app_context():
    try:
        db.create_all()

        print("")
        print("==========================================")
        print(
            "✅ Database tables created successfully!"
        )
        print(
            "📊 Tables:",
            list(
                db.metadata.tables.keys()
            )
        )
        print("==========================================")

    except Exception as e:
        print(
            "❌ Database error:",
            str(e)
        )


# Load model after app/database initialization
load_model()


# =========================================================
# AUTHENTICATION DECORATOR
# =========================================================

def login_required(f):
    @wraps(f)
    def decorated_function(
        *args,
        **kwargs
    ):
        if not session.get("user"):
            if (
                request.is_json
                or request.path.startswith("/api/")
                or request.path == "/predict"
                or request.path == "/save_daily_usage"
            ):
                return jsonify({
                    "status": "error",
                    "success": False,
                    "message": "Please login first."
                }), 401

            flash(
                "ကျေးဇူးပြု၍ ပထမဦးစွာ Login ဝင်ပါ။",
                "danger"
            )

            return redirect(
                url_for("auth")
            )

        return f(
            *args,
            **kwargs
        )

    return decorated_function


TARGET_PAGE_URL = "https://30122022khaingthuzarthein.pythonanywhere.com/" 

@app.route('/generate-qr')
def generate_qr():
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(TARGET_PAGE_URL)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    qr_code_img = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return render_template('show_qr.html', qr_code=qr_code_img, target_url=TARGET_PAGE_URL)

@app.route('/welcome-page')
def welcome_page():
    return """
        <h2>Welcome! 🎉</h2>
        <p>QR Code ကို Scan ဖတ်ပြီး ဤစာမျက်နှာသို အောင်မြင်စွာ ရောက်ရှိလာပါပြီ။</p>
    """


# =========================================================
# ROOT & HOME ROUTES
# =========================================================

@app.route('/')
def home():
    user_id = session.get('user', {}).get('id')
    goal = Goal.query.filter_by(user_id=user_id).order_by(Goal.goal_id.desc()).first() if user_id else None
    
    percentage = 0
    if goal and goal.target_hours and goal.target_hours > 0:
        current_usage = getattr(goal, 'current_usage', 0)
        target_in_minutes = goal.target_hours * 60
        percentage = (current_usage / target_in_minutes) * 100
        percentage = min(round(percentage, 1), 100) 

    return render_template('home.html', goal=goal, percentage=percentage)


# =========================================================
# DASHBOARD PAGE
# =========================================================

@app.route('/dashboard')
@login_required
def dashboard():
    user_id = session.get('user', {}).get('id')
    
    goal = Goal.query.filter_by(user_id=user_id).order_by(Goal.goal_id.desc()).first() if user_id else None
    
    percentage = 0
    if goal and goal.target_hours and goal.target_hours > 0:
        current_usage = getattr(goal, 'current_usage', 0)
        target_in_minutes = goal.target_hours * 60
        percentage = (current_usage / target_in_minutes) * 100
        percentage = min(round(percentage, 1), 100) 

    latest_usage = DailyUsage.query.filter_by(user_id=user_id).order_by(DailyUsage.usage_id.desc()).first() if user_id else None
    latest_assessment = AssessmentLog.query.filter_by(user_id=user_id).order_by(AssessmentLog.log_id.desc()).first() if user_id else None

    return render_template(
        'home.html', 
        goal=goal, 
        percentage=percentage, 
        latest_usage=latest_usage, 
        latest_assessment=latest_assessment
    )


# =========================================================
# AUTH PAGE
# =========================================================

@app.route("/auth")
def auth():
    if session.get("user"):
        return redirect(
            url_for("home")
        )
    return render_template(
        "auth.html"
    )


# =========================================================
# REGISTER
# =========================================================

@app.route(
    "/register",
    methods=["POST"]
)
def register():
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"success": False, "message": "No registration data received."}), 400

        name = str(data.get("name", "")).strip()
        email = str(data.get("email", "")).strip().lower()
        password = str(data.get("password", "")).strip()

        if not name or not email or not password:
            return jsonify({"success": False, "message": "Please fill in all fields."}), 400

        if len(name) < 2:
            return jsonify({"success": False, "message": "Name must be at least 2 characters."}), 400

        if len(password) < 6:
            return jsonify({"success": False, "message": "Password must be at least 6 characters."}), 400

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({"success": False, "message": "Email already registered."}), 409

        new_user = User(
            username=name,
            email=email,
            password=generate_password_hash(password)
        )

        db.session.add(new_user)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Registration successful! Please login.",
            "redirect": url_for("auth")
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": "Registration failed: " + str(e)}), 500


# =========================================================
# LOGIN
# =========================================================

@app.route(
    "/login",
    methods=["POST"]
)
def login():
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"success": False, "message": "No login data received."}), 400

        email = str(data.get("email", "")).strip().lower()
        password = str(data.get("password", "")).strip()

        if not email or not password:
            return jsonify({"success": False, "message": "Please enter email and password."}), 400

        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password, password):
            return jsonify({"success": False, "message": "Invalid email or password."}), 401

        session["user"] = {
            "id": user.user_id,
            "username": user.username,
            "email": user.email
        }
        session["user_data"] = {}

        return jsonify({
            "success": True,
            "message": "Login successful!",
            "user": session["user"]
        }), 200

    except Exception as e:
        return jsonify({"success": False, "message": "Login failed: " + str(e)}), 500


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


# =========================================================
# CURRENT USER
# =========================================================

@app.route("/current_user")
@login_required
def current_user():
    user = session.get("user")
    user_data = session.get("user_data", {})
    apps_count = (
        user_data.get("Number_of_Apps_Used")
        or user_data.get("number_of_apps")
        or user_data.get("number_of_apps_used")
        or 0
    )
    return jsonify({
        "logged_in": True,
        "user": user,
        "number_of_apps": int(apps_count)
    })


# =========================================================
# SET GOAL
# =========================================================

@app.route('/set-goal', methods=['POST'])
@login_required
def set_goal():
    target_hours = request.form.get('target_hours')
    description = request.form.get('description')
    
    user_id = session.get('user', {}).get('id')
    user_assessment = DailyUsage.query.filter_by(user_id=user_id).order_by(DailyUsage.usage_id.desc()).first()
    current_usage_hours = user_assessment.screen_time_hours if user_assessment else 0
    current_usage_minutes = round(float(current_usage_hours) * 60)
    
    new_goal = Goal(
        user_id=user_id,
        target_hours=float(target_hours) if target_hours else 0,
        description=description,
        current_usage=current_usage_minutes
    )
    
    db.session.add(new_goal)
    db.session.commit()
    
    return redirect(url_for('dashboard'))


# =========================================================
# USAGE ANALYSIS PAGE
# =========================================================

@app.route("/usage_analysis")
@login_required
def usage_analysis():
    return render_template("usage_analysis.html")


# =========================================================
# DAILY USAGE API
# =========================================================

@app.route("/api/daily_usage", methods=["GET"])
@login_required
def get_daily_usage_api():
    try:
        user_id = session["user"]["id"]

        # Latest Daily Usage
        usage_data = (
            DailyUsage.query
            .filter_by(user_id=user_id)
            .order_by(DailyUsage.usage_id.desc())
            .first()
        )

        # Latest Assessment
        latest_log = (
            AssessmentLog.query
            .filter_by(user_id=user_id)
            .order_by(AssessmentLog.log_id.desc())
            .first()
        )

        if not usage_data and not latest_log:
            return jsonify({
                "success": False,
                "message": "No assessment or usage data found."
            }), 404

        # Get values safely
        screen_time = getattr(
            usage_data, "screen_time_hours", 0
        ) if usage_data else 0

        social_media = getattr(
            usage_data, "social_media_hours", 0
        ) if usage_data else 0

        gaming = getattr(
            usage_data, "gaming_hours", 0
        ) if usage_data else 0

        sleep = getattr(
            usage_data, "sleep_hours", 0
        ) if usage_data else 0

        # Optional fields
        apps_count = getattr(
            usage_data, "number_of_apps_used", 0
        ) if usage_data else 0

        notifications = getattr(
            usage_data, "notification_count", 0
        ) if usage_data else 0

        physical_activity = getattr(
            usage_data, "physical_activity", 0
        ) if usage_data else 0

        night_usage = getattr(
            usage_data, "night_time_usage_hours", 0
        ) if usage_data else 0

        # Assessment result
        score = (
            getattr(latest_log, "wellbeing_score", 0)
            if latest_log else 0
        )

        awareness = (
            getattr(latest_log, "awareness_level", "N/A")
            if latest_log else "N/A"
        )

        # User information
        user_id_value = user_id
        age = "-"
        gender = "-"

        if latest_log:
            age = getattr(latest_log, "age", "-")
            
            # gender တန်ဖိုးကို စာသားသို့ ပြန်ပြောင်းရန်
            raw_gender = str(getattr(latest_log, "gender", "-"))
            if raw_gender == "0.0" or raw_gender == "0":
                gender = "Male"
            elif raw_gender == "1.0" or raw_gender == "1":
                gender = "Female"
            else:
                gender = raw_gender

        return jsonify({
            "success": True,
            "data": {
                # User Information
                "User_ID":user_id_value,
                "Age": age,
                "Gender": gender,

                # Usage Data (Column Names များကို Frontend နှင့် အတိအကျ ကိုက်ညီစေရန်)
                "Daily_Screen_Time_Hours": screen_time,
                "Number_of_Apps_Used": apps_count,
                "Social_Media_Usage_Hours": social_media,
                "Gaming_App_Usage_Hours": gaming,
                "Notification_Count": notifications,
                "Physical_Activity_Hours_Week": physical_activity,  # Space အစား underscore ပြောင်းလိုက်သည်
                "Night_Time_Usage_Hours": night_usage,
                "Sleep_Hours": sleep,

                # Assessment Result
                "Digital_Wellbeing_Score": score,
                "Awareness_Level": awareness
            }
        })

    except Exception as e:
        print("❌ Daily Usage API Error:", str(e))

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

# =========================================================
# ASSESSMENT PAGE
# =========================================================

@app.route("/assessment")
@login_required
def assessment():
    return render_template("index.html")


# =========================================================
# LATEST ASSESSMENT API
# =========================================================

@app.route(
    "/api/latest_assessment",
    methods=["GET"]
)
@login_required
def get_latest_assessment_api():
    try:
        user_id = session["user"]["id"]
        latest_log = AssessmentLog.query.filter_by(user_id=user_id).order_by(AssessmentLog.log_id.desc()).first()

        if not latest_log:
            return jsonify({"success": False, "message": "No assessment found"}), 404

        return jsonify({
            "success": True,
            "data": {
                "wellbeing_score": latest_log.wellbeing_score,
                "awareness_level": latest_log.awareness_level
            }
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# =========================================================
# AI PREDICTION PAGE
# =========================================================

@app.route("/ai_prediction")
@login_required
def ai_prediction():
    return render_template("ai_prediction.html")


# =========================================================
# WELLBEING RESULTS PAGE
# =========================================================

@app.route("/wellbeing_results")
@login_required
def wellbeing_results():
    return render_template("wellbeing_results.html")


# =========================================================
# RECOMMENDATIONS PAGE
# =========================================================

@app.route("/recommendations")
@login_required
def recommendations():
    return render_template("recommendations.html")


# =========================================================
# HELPER: NORMALIZE AWARENESS LEVEL
# =========================================================

def normalize_awareness_level(prediction):
    if isinstance(prediction, np.generic):
        prediction = prediction.item()

    prediction_string = str(prediction).strip()
    prediction_lower = prediction_string.lower()

    if prediction_lower in ["high", "good", "high awareness", "high_awareness"]:
        return "High"
    if prediction_lower in ["medium", "normal", "moderate", "medium awareness", "medium_awareness"]:
        return "Medium"
    if prediction_lower in ["low", "poor", "low awareness", "low_awareness"]:
        return "Low"

    try:
        numeric_prediction = int(float(prediction_string))
        if numeric_prediction == 0:
            return "Low"
        if numeric_prediction == 1:
            return "Medium"
        if numeric_prediction == 2:
            return "High"
    except (ValueError, TypeError):
        pass

    return prediction_string


# =========================================================
# HELPER: CALCULATE SCORE
# =========================================================

def calculate_score(awareness_level, confidence):
    confidence = float(confidence)
    confidence = max(0.0, min(1.0, confidence))

    if awareness_level == "High":
        score = 70 + (confidence * 30)
    elif awareness_level == "Medium":
        score = 45 + (confidence * 25)
    elif awareness_level == "Low":
        score = confidence * 45
    else:
        score = 50.0

    return round(max(0.0, min(100.0, score)), 2)


# =========================================================
# HELPER: GENERATE RECOMMENDATIONS
# =========================================================

def generate_recommendations(screen_time, apps_count, social, gaming, sleep, awareness_level):
    recommendations = []

    if gaming >= 4:
        recommendations.append("🎮 Gaming အသုံးပြုချိန်ကို လျှော့ချပြီး အချိန်ကန့်သတ်ချက်ထားပါ။")
    elif gaming >= 2:
        recommendations.append("🎮 Gaming အတွက် သတ်မှတ်ထားသော daily time limit ကို အသုံးပြုပါ။")

    if social >= 4:
        recommendations.append("📱 Social Media အသုံးပြုချိန်ကို လျှော့ချပြီး notification များကို ထိန်းချုပ်ပါ။")
    elif social >= 2:
        recommendations.append("📱 Social Media အသုံးပြုချိန်အတွက် daily limit သတ်မှတ်ပါ။")

    if screen_time >= 8:
        recommendations.append("⏰ Daily Screen Time မြင့်နေသောကြောင့် ပုံမှန် digital breaks ယူပါ။")
    elif screen_time >= 6:
        recommendations.append("⏰ Screen အသုံးပြုနေစဉ် 20–30 မိနစ်တိုင်း အနားယူရန် ကြိုးစားပါ။")

    if apps_count >= 20:
        recommendations.append("🗑 အသုံးမပြုတော့သော Apps များကို ဖယ်ရှားပြီး App notifications များကို လျှော့ချပါ။")

    if sleep < 6:
        recommendations.append("😴 Sleep Hours နည်းနေသောကြောင့် အိပ်ချိန်ကို ပိုမိုတိုးမြှင့်ပါ။")
    elif sleep < 7:
        recommendations.append("😴 တစ်နေ့လျှင် အနည်းဆုံး 7 နာရီခန့် အိပ်စက်နိုင်ရန် ကြိုးစားပါ။")
    elif sleep > 10:
        recommendations.append("😴 Sleep pattern ကို ပုံမှန်ဖြစ်အောင် ထိန်းသိမ်းပါ။")

    if awareness_level == "Low":
        recommendations.append("🧠 Healthy Digital Life ပိုမိုကောင်းမွန်စေရန် daily usage ကို စောင့်ကြည့်ပါ။")
    elif awareness_level == "Medium":
        recommendations.append("🧠 လက်ရှိ digital habits ကို ဆက်လက်စောင့်ကြည့်ပြီး screen time ကို တဖြည်းဖြည်း လျှော့ချပါ။")
    elif awareness_level == "High":
        recommendations.append("🌱 လက်ရှိကောင်းမွန်သော digital habits များကို ဆက်လက်ထိန်းသိမ်းပါ။")

    recommendations.append("⏰ Device အသုံးပြုနေစဉ် ပုံမှန် break ယူပါ။")
    return recommendations


# =========================================================
# PREDICTION API
# =========================================================

@app.route(
    "/predict",
    methods=["POST"]
)
@login_required
def predict():
    try:
        if model is None:
            return jsonify({
                "status": "error",
                "success": False,
                "message": "Random Forest model is not loaded on server."
            }), 500

        if request.is_json:
            data = request.get_json(silent=True)
        else:
            data = request.form.to_dict()

        if not data:
            return jsonify({
                "status": "error",
                "success": False,
                "message": "No input data provided for prediction."
            }), 400

        try:
            age = float(data.get("Age", 25))
            gender_val = float(data.get("Gender", 0)) # Frontend က 0 သို့မဟုတ် 1 ပို့ပြီးသားဖြစ်므로
            notification_count = float(data.get("Notification_Count", 0))
            screen_time = float(data.get("Daily_Screen_Time_Hours", 0))
            number_of_apps = float(data.get("Number_of_Apps_Used", 0))
            social_media = float(data.get("Social_Media_Usage_Hours", 0))
            gaming = float(data.get("Gaming_App_Usage_Hours", 0))
            # HTML ဖောင် သို့မဟုတ် API မှ နာမည်အမျိုးမျိုးဖြင့် ပို့လာနိုင်သည်များကို အကုန်စစ်ဆေးဖမ်းယူရန်
            # Physical Activity တန်ဖိုးကို နာမည်အမျိုးမျိုးဖြင့် လိုက်ရှာပြီး ဖမ်းယူခြင်း
            physical_activity = float(
                data.get("Physical_Activity_Hours_Week") or 
                data.get("Physical_Activity") or 
                data.get("physical_activity") or 
                0
            )
            night_time = float(data.get("Night_Time_Usage_Hours", 0))
            sleep = float(data.get("Sleep_Hours", 0))
            features = np.array([[
                age,
                gender_val,
                notification_count,
                screen_time,
                number_of_apps,
                social_media,
                gaming,
                physical_activity,
                night_time,
                sleep
            ]])

            prediction = model.predict(features)[0]
            
            if hasattr(model, "predict_proba"):
                probabilities = model.predict_proba(features)[0]
                confidence = float(np.max(probabilities))
            else:
                confidence = 1.0

            awareness_level = normalize_awareness_level(prediction)
            wellbeing_score = calculate_score(awareness_level, confidence)

            recommendations = generate_recommendations(
                screen_time,
                number_of_apps,
                social_media,
                gaming,
                sleep,
                awareness_level
            )

            user_id = session.get("user", {}).get("id")
            if user_id:
                # 1. Assessment Log သိမ်းခြင်း
                new_log = AssessmentLog(
                    user_id=user_id,
                    wellbeing_score=wellbeing_score,
                    awareness_level=awareness_level,
                    age=int(age),
                    gender=str(gender_val)
                )
                db.session.add(new_log)

                # 2. Daily Usage Data ပါ Database ထဲသို့ ထည့်သွင်းသိမ်းဆည်းခြင်း (အသفتထည့်ရန်)
                new_usage = DailyUsage(
                    user_id=user_id,
                    screen_time_hours=screen_time,
                    social_media_hours=social_media,
                    gaming_hours=gaming,
                    sleep_hours=sleep,
                    number_of_apps_used=int(number_of_apps),
                    notification_count=int(notification_count),
                    physical_activity=physical_activity,
                    night_time_usage_hours=night_time
                )
                db.session.add(new_usage)
                
                db.session.commit()
            return jsonify({
                "status": "success",
                "success": True,
                "awareness_level": awareness_level,
                "wellbeing_score": wellbeing_score,
                "confidence": confidence,
                "recommendations": recommendations
            }), 200

        except ValueError as ve:
            return jsonify({
                "status": "error",
                "success": False,
                "message": f"Invalid input data format: {str(ve)}"
            }), 400

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "success": False,
            "message": f"Prediction failed: {str(e)}"
        }), 500


if __name__ == "__main__":
    app.run(debug=True)