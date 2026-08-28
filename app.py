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
app.secret_keys="your_secret_key_here"

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


## =========================================================
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
        
        # 🟢 ပြင်ဆင်ထားသည့်နေရာ (type(model).name)
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

                    "message":
                        "Please login first."

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
# ဝင်ချင်တဲ့ Website Page ရဲ့ လိပ်စာ (သိုမဟုတ် Dashboard)
# ဥပမာ - QR ဖတ်လိုက်တာနဲ့ https://yourwebsite.com/welcome ဆီ တိုက်ရိုက်ရောက်စေချင်တာ
TARGET_PAGE_URL = "https://healthydigitallife-production.up.railway.app/" 

@app.route('/generate-qr')
def generate_qr():
    # ဒီ QR Code ထဲမှာ Target Page ရဲ့ Link တိုက်ရိုက်ပါဝင်မှာ ဖြစ်ပါတယ်
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(TARGET_PAGE_URL)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    qr_code_img = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    return render_template('show_qr.html', qr_code=qr_code_img, target_url=TARGET_PAGE_URL)

# QR Code ဖတ်လိုက်တာနဲ့ တိုက်ရိုက်ရောက်မယ့် Page
@app.route('/welcome-page')
def welcome_page():
    return """
        <h2>Welcome! 🎉</h2>
        <p>QR Code ကို Scan ဖတ်ပြီး ဤစာမျက်နှာသို အောင်မြင်စွာ ရောက်ရှိလာပါပြီ။</p>
    """


# =========================================================
# ROOT & HOME ROUTES (404 Error ဖြေရှင်းရန်)
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
# @app.route('/dashboard')
# @login_required
# def dashboard():
#     user_id = session.get('user', {}).get('id')
#     goal = Goal.query.filter_by(user_id=user_id).order_by(Goal.goal_id.desc()).first() if user_id else None
    
#     percentage = 0
#     if goal and goal.target_minutes and goal.target_minutes > 0:
#         percentage = (goal.current_minutes / goal.target_minutes) * 100
#         percentage = min(round(percentage, 1), 100) 

#     return render_template('home.html', goal=goal, percentage=percentage)


# =========================================================
# DASHBOARD PAGE
# =========================================================

@app.route('/dashboard')
@login_required
def dashboard():
    user_id = session.get('user', {}).get('id')
    
    # 1. Goal များကို ရယူရန်
    goal = Goal.query.filter_by(user_id=user_id).order_by(Goal.goal_id.desc()).first() if user_id else None
    
    percentage = 0
    if goal and goal.target_hours and goal.target_hours > 0:
        current_usage = getattr(goal, 'current_usage', 0)
        target_in_minutes = goal.target_hours * 60
        percentage = (current_usage / target_in_minutes) * 100
        percentage = min(round(percentage, 1), 100) 

    # 2. နောက်ဆုံး Daily Usage ကို ရယူရန်
    latest_usage = DailyUsage.query.filter_by(user_id=user_id).order_by(DailyUsage.usage_id.desc()).first() if user_id else None

    # 3. နောက်ဆုံး Assessment Log ကို ရယူရန်
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

        data = request.get_json(
            silent=True
        )

        if not data:

            return jsonify({

                "success": False,

                "message":
                    "No registration data received."

            }), 400


        name = str(
            data.get(
                "name",
                ""
            )
        ).strip()


        email = str(
            data.get(
                "email",
                ""
            )
        ).strip().lower()


        password = str(
            data.get(
                "password",
                ""
            )
        ).strip()


        if (
            not name
            or not email
            or not password
        ):

            return jsonify({

                "success": False,

                "message":
                    "Please fill in all fields."

            }), 400


        if len(name) < 2:

            return jsonify({

                "success": False,

                "message":
                    "Name must be at least 2 characters."

            }), 400


        if len(password) < 6:

            return jsonify({

                "success": False,

                "message":
                    "Password must be at least 6 characters."

            }), 400


        existing_user = (
            User.query
            .filter_by(
                email=email
            )
            .first()
        )
        if existing_user:

            return jsonify({

                "success": False,

                "message":
                    "Email already registered."

            }), 409


        new_user = User(

            username=name,

            email=email,

            password=
                generate_password_hash(
                    password
                )
        )


        db.session.add(
            new_user
        )

        db.session.commit()


        return jsonify({

            "success": True,

            "message":
                "Registration successful! Please login.",

            "redirect":
                url_for("auth")

        }), 200


    except Exception as e:

        db.session.rollback()

        print(
            "❌ Registration Error:",
            str(e)
        )

        return jsonify({

            "success": False,

            "message":
                "Registration failed: " + str(e)

        }), 500


# =========================================================
# LOGIN
# =========================================================

@app.route(
    "/login",
    methods=["POST"]
)
def login():

    try:

        data = request.get_json(
            silent=True
        )

        if not data:

            return jsonify({

                "success": False,

                "message":
                    "No login data received."

            }), 400


        email = str(
            data.get(
                "email",
                ""
            )
        ).strip().lower()


        password = str(
            data.get(
                "password",
                ""
            )
        ).strip()


        if (
            not email
            or not password
        ):

            return jsonify({

                "success": False,

                "message":
                    "Please enter email and password."

            }), 400


        user = (
            User.query
            .filter_by(
                email=email
            )
            .first()
        )


        if not user:

            return jsonify({

                "success": False,

                "message":
                    "Invalid email or password."

            }), 401


        if not check_password_hash(
            user.password,
            password
        ):

            return jsonify({

                "success": False,

                "message":
                    "Invalid email or password."

            }), 401


        session["user"] = {

            "id":
                user.user_id,

            "username":
                user.username,

            "email":
                user.email
        }


        session["user_data"] = {}


        return jsonify({

            "success": True,

            "message":
                "Login successful!",

            "user":
                session["user"]

        }), 200


    except Exception as e:

        print(
            "❌ Login Error:",
            str(e)
        )

        return jsonify({

            "success": False,

            "message":
                "Login failed: " + str(e)

        }), 500


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("home")
    )


# =========================================================
# CURRENT USER
# =========================================================

@app.route("/current_user")
@login_required
def current_user():

    user = session.get(
        "user"
    )

    user_data = session.get(
        "user_data",
        {}
    )


    apps_count = (

        user_data.get(
            "Number_of_Apps_Used"
        )

        or user_data.get(
            "number_of_apps"
        )

        or user_data.get(
            "number_of_apps_used"
        )

        or 0
    )


    return jsonify({

        "logged_in": True,

        "user":
            user,
        "number_of_apps":
            int(apps_count)

    })


# =========================================================
# SET GOAL
# =========================================================

@app.route('/set-goal', methods=['POST'])
@login_required
def set_goal():
    # ဖောင်မှ target_hours ကို ရယူပါ
    target_hours = request.form.get('target_hours')
    description = request.form.get('description')
    
    user_id = session.get('user', {}).get('id')
    # Always use the most recently saved usage record so a new goal shows current data.
    user_assessment = (
        DailyUsage.query.filter_by(user_id=user_id)
        .order_by(DailyUsage.usage_id.desc())
        .first()
    )
    current_usage_hours = user_assessment.screen_time_hours if user_assessment else 0
    current_usage_minutes = round(float(current_usage_hours) * 60)
    
    # ဤနေရာတွင် Database မော်ဒယ် (Goal) ၏ field အမည်များကို target_hours နှင့် current_usage သို့ ပြောင်းထားရပါမည်
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

    return render_template(
        "usage_analysis.html"
    )


# =========================================================
# DAILY USAGE API
# =========================================================

@app.route(
    "/api/daily_usage",
    methods=["GET"]
)
@login_required
def get_daily_usage_api():

    try:

        user_id = session[
            "user"
        ][
            "id"
        ]


        usage_data = (

            DailyUsage.query

            .filter_by(
                user_id=user_id
            )

            .order_by(
                DailyUsage.usage_id.desc()
            )

            .first()
        )


        if not usage_data:

            return jsonify({

                "success": False,

                "message":
                    "No data found"

            }), 404


        return jsonify({

            "success": True,

            "data": {

                "screen_time":
                    usage_data.screen_time_hours,

                "total_app_usage":
                    usage_data.total_app_usage_hours,

                "social_media_usage":
                    usage_data.social_media_hours,

                "gaming_usage":
                    usage_data.gaming_hours,

                "sleep_hours":
                    usage_data.sleep_hours

            }

        })


    except Exception as e:

        return jsonify({

            "success": False,

            "message":
                str(e)

        }), 500
# =========================================================
# ASSESSMENT PAGE
# =========================================================

@app.route("/assessment")
@login_required
def assessment():
    return render_template(
        "index.html"  # သင့်ရဲ့ HTML ဖိုင်နာမည်ကို ထည့်ပါ (ဥပမာ - index.html)
    )

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

        user_id = session[
            "user"
        ][
            "id"
        ]


        latest_log = (

            AssessmentLog.query

            .filter_by(
                user_id=user_id
            )

            .order_by(
                AssessmentLog.log_id.desc()
            )

            .first()
        )


        if not latest_log:

            return jsonify({

                "success": False,

                "message":
                    "No assessment found"

            }), 404


        return jsonify({

            "success": True,

            "data": {

                "wellbeing_score":
                    latest_log.wellbeing_score,

                "awareness_level":
                    latest_log.awareness_level

            }

        })


    except Exception as e:

        return jsonify({

            "success": False,

            "message":
                str(e)

        }), 500


# =========================================================
# AI PREDICTION PAGE
# =========================================================

@app.route("/ai_prediction")
@login_required
def ai_prediction():

    return render_template(
        "ai_prediction.html"
    )
# =========================================================
# WELLBEING RESULTS PAGE
# =========================================================

@app.route("/wellbeing_results")
@login_required
def wellbeing_results():

    return render_template(
        "wellbeing_results.html"
    )


# =========================================================
# RECOMMENDATIONS PAGE
# =========================================================

@app.route("/recommendations")
@login_required
def recommendations():

    return render_template(
        "recommendations.html"
    )


# =========================================================
# HELPER: NORMALIZE AWARENESS LEVEL
# =========================================================

def normalize_awareness_level(
    prediction
):

    if isinstance(
        prediction,
        np.generic
    ):

        prediction = prediction.item()


    prediction_string = str(
        prediction
    ).strip()


    prediction_lower = (
        prediction_string.lower()
    )


    if prediction_lower in [
        "high",
        "good",
        "high awareness",
        "high_awareness"
    ]:

        return "High"


    if prediction_lower in [
        "medium",
        "normal",
        "moderate",
        "medium awareness",
        "medium_awareness"
    ]:

        return "Medium"


    if prediction_lower in [
        "low",
        "poor",
        "low awareness",
        "low_awareness"
    ]:

        return "Low"


    try:

        numeric_prediction = int(
            float(
                prediction_string
            )
        )


        if numeric_prediction == 0:

            return "Low"


        if numeric_prediction == 1:

            return "Medium"


        if numeric_prediction == 2:

            return "High"


    except (
        ValueError,
        TypeError
    ):

        pass


    return prediction_string


# =========================================================
# HELPER: CALCULATE SCORE
# =========================================================

def calculate_score(
    awareness_level,
    confidence
):

    confidence = float(
        confidence
    )


    confidence = max(
        0.0,
        min(
            1.0,
            confidence
        )
    )


    if awareness_level == "High":

        score = (
            70
            + (
                confidence
                * 30
            )
        )


    elif awareness_level == "Medium":

        score = (
            45
            + (
                confidence
                * 25
            )
        )


    elif awareness_level == "Low":

        score = (
            confidence
            * 45
        )


    else:

        score = 50.0


    score = max(
        0.0,
        min(
            100.0,
            score
        )
    )


    return round(
        score,
        2
    )


# =========================================================
# HELPER: GENERATE RECOMMENDATIONS
# =========================================================

def generate_recommendations(
    total_app,
    screen_time,
    apps_count,
    social,
    gaming,
    sleep,
    awareness_level
):

    recommendations = []


    if gaming >= 4:

        recommendations.append(
            "🎮 Gaming အသုံးပြုချိန်ကို လျှော့ချပြီး အချိန်ကန့်သတ်ချက်ထားပါ။"
        )

    elif gaming >= 2:

        recommendations.append(
            "🎮 Gaming အတွက် သတ်မှတ်ထားသော daily time limit ကို အသုံးပြုပါ။"
        )


    if social >= 4:

        recommendations.append(
            "📱 Social Media အသုံးပြုချိန်ကို လျှော့ချပြီး notification များကို ထိန်းချုပ်ပါ။"
        )

    elif social >= 2:

        recommendations.append(
            "📱 Social Media အသုံးပြုချိန်အတွက် daily limit သတ်မှတ်ပါ။"
        )


    if screen_time >= 8:

        recommendations.append(
            "⏰ Daily Screen Time မြင့်နေသောကြောင့် ပုံမှန် digital breaks ယူပါ။"
        )

    elif screen_time >= 6:

        recommendations.append(
            "⏰ Screen အသုံးပြုနေစဉ် 20–30 မိနစ်တိုင်း အနားယူရန် ကြိုးစားပါ။"
        )
    if total_app >= 8:

        recommendations.append(
            "📱 Total App Usage မြင့်နေသောကြောင့် မလိုအပ်သော App အသုံးပြုမှုကို လျှော့ချပါ။"
        )


    if apps_count >= 20:

        recommendations.append(
            "🗑️ အသုံးမပြုတော့သော Apps များကို ဖယ်ရှားပြီး App notifications များကို လျှော့ချပါ။"
        )


    if sleep < 6:

        recommendations.append(
            "😴 Sleep Hours နည်းနေသောကြောင့် အိပ်ချိန်ကို ပိုမိုတိုးမြှင့်ပါ။"
        )

    elif sleep < 7:

        recommendations.append(
            "😴 တစ်နေ့လျှင် အနည်းဆုံး 7 နာရီခန့် အိပ်စက်နိုင်ရန် ကြိုးစားပါ။"
        )

    elif sleep > 10:

        recommendations.append(
            "😴 Sleep pattern ကို ပုံမှန်ဖြစ်အောင် ထိန်းသိမ်းပါ။"
        )


    if awareness_level == "Low":

        recommendations.append(
            "🧠 Healthy Digital Life ပိုမိုကောင်းမွန်စေရန် daily usage ကို စောင့်ကြည့်ပါ။"
        )

    elif awareness_level == "Medium":

        recommendations.append(
            "🧠 လက်ရှိ digital habits ကို ဆက်လက်စောင့်ကြည့်ပြီး screen time ကို တဖြည်းဖြည်း လျှော့ချပါ။"
        )

    elif awareness_level == "High":

        recommendations.append(
            "🌱 လက်ရှိကောင်းမွန်သော digital habits များကို ဆက်လက်ထိန်းသိမ်းပါ။"
        )


    recommendations.append(
        "⏰ Device အသုံးပြုနေစဉ် ပုံမှန် break ယူပါ။"
    )


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

                "message":
                    "Random Forest model is not loaded on server."

            }), 500


        if request.is_json:

            data = request.get_json(
                silent=True
            )

        else:

            data = request.form.to_dict()


        if not data:

            return jsonify({

                "status": "error",

                "success": False,

                "message":
                    "No prediction data provided."

            }), 400


        try:

            age = float(data.get("age"))
            gender_value = float(data.get("gender", 0))
            total_app = round(float(data.get("total_app_usage", 0)), 2)
            screen_time = round(float(data.get("daily_screen_time", 0)), 2)
            apps_count = int(data.get("number_of_apps", 0))
            social = round(float(data.get("social_media_hours", 0)), 2)
            gaming = round(float(data.get("gaming_hours", 0)), 2)
            sleep = round(float(data.get("sleep_hours", 0)), 2)

        except (
            ValueError,
            TypeError
        ):

            return jsonify({

                "status": "error",

                "success": False,

                "message":
                    "Invalid numeric input received."

            }), 400


        feature_values = [

            age,

            gender_value,

            total_app,

            screen_time,

            apps_count,

            social,

            gaming,

            sleep
        ]


        features = np.array(
            [
                feature_values
            ],
            dtype=float
        )


        prediction = model.predict(
            features
        )


        raw_prediction = prediction[0]


        awareness_level = (
            normalize_awareness_level(
                raw_prediction
            )
        )


        confidence = 0.0


        if hasattr(
            model,
            "predict_proba"
        ):

            try:

                probabilities = (
                    model.predict_proba(
                        features
                    )
                )


                if (
                    probabilities is not None
                    and len(probabilities) > 0
                ):

                    confidence = float(
                        np.max(
                            probabilities[0]
                        )
                    )


            except Exception:

                confidence = 0.0


        score = calculate_score(

            awareness_level,

            confidence

        )


        recommendations_list = (
            generate_recommendations(

                total_app=
                    total_app,

                screen_time=
                    screen_time,

                apps_count=
                    apps_count,

                social=
                    social,

                gaming=
                    gaming,

                sleep=
                    sleep,

                awareness_level=
                    awareness_level

            )
        )


        user_id = session[
            "user"
        ][
            "id"
        ]


        assessment = AssessmentLog(

            user_id=user_id,

            wellbeing_score=
                score,

            awareness_level=
                awareness_level
        )


        db.session.add(
            assessment
        )


        daily_usage = DailyUsage(

            user_id=user_id,

            total_app_usage_hours=
                total_app,

            screen_time_hours=
                screen_time,

            social_media_hours=
                social,

            gaming_hours=
                gaming,

            sleep_hours=
                sleep
        )


        db.session.add(
            daily_usage
        )


        db.session.commit()


        session["user_data"] = {

            "Age":
                age,

            "Gender":
                gender_value,

            "Total_App_Usage_Hours":
                total_app,

            "Daily_Screen_Time_Hours":
                screen_time,

            "Number_of_Apps_Used":
                apps_count,

            "Social_Media_Usage_Hours":
                social,

            "Gaming_App_Usage_Hours":
                gaming,

            "Sleep_Hours":
                sleep,

            "Digital_Wellbeing_Score":
                score,

            "Awareness_Level":
                awareness_level,

            "Model_Prediction":
                str(raw_prediction),

            "Confidence":
                confidence

        }


        response_data = {

            "status":
                "success",

            "success":
                True,

            "prediction":
                str(raw_prediction),

            "score":
                score,

            "awareness_level":
                awareness_level,

            "confidence":
                round(
                    confidence,
                    4
                ),

            "recommendations":
                recommendations_list,

            "daily_usage_saved":
                True

        }


        return jsonify(
            response_data
        ), 200


    except Exception as e:

        db.session.rollback()

        return jsonify({

            "status":
                "error",

            "success":
                False,

            "message":
                "Prediction failed: "
                + str(e)

        }), 500


# =========================================================
# SAVE DAILY USAGE
# =========================================================

@app.route(
    "/save_daily_usage",
    methods=["POST"]
)
@login_required
def save_daily_usage():

    try:

        if request.is_json:

            data = request.get_json(
                silent=True
            )

        else:

            data = request.form.to_dict()


        if not data:

            return jsonify({

                "success":
                    False,

                "message":
                    "No usage data received."

            }), 400


        user_id = session[
            "user"
        ][
            "id"
        ]
        total_app = round(float(data.get("total_app_usage", data.get("Total_App_Usage_Hours", 0))), 2)
        screen_time = round(float(data.get("screen_time", data.get("Daily_Screen_Time_Hours", 0))), 2)
        social = round(float(data.get("social_media", data.get("Social_Media_Usage_Hours", 0))), 2)
        gaming = round(float(data.get("gaming", data.get("Gaming_App_Usage_Hours", 0))), 2)
        sleep = round(float(data.get("sleep_hours", data.get("Sleep_Hours", 0))), 2)


        usage = DailyUsage(

            user_id=user_id,

            total_app_usage_hours=
                total_app,

            screen_time_hours=
                screen_time,

            social_media_hours=
                social,

            gaming_hours=
                gaming,

            sleep_hours=
                sleep
        )


        db.session.add(
            usage
        )

        db.session.commit()


        return jsonify({

            "success":
                True,

            "message":
                "Daily usage saved successfully."

        }), 200


    except Exception as e:

        db.session.rollback()

        return jsonify({

            "success":
                False,

            "message":
                str(e)

        }), 500


# =========================================================
# RUN FLASK SERVER
# =========================================================

if __name__ == "__main__":

    print("")
    print("==========================================")
    print("   HEALTHY DIGITAL LIFE SYSTEM")
    print("==========================================")

    print(
        "🌐 Server: http://0.0.0.0:5000"
    )

    print(
        "🤖 Model:",
        "Loaded" if model is not None else "NOT LOADED"
    )

    print(
        "=========================================="
    )

    app.run(

        debug=True,

        host="0.0.0.0",

        port=5000

    )