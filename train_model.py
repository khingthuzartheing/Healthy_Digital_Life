import pandas as pd
import pickle

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report


# ==========================================
# SETTINGS
# ==========================================

DATASET_FILE = "training_dataset_for_orange.csv"
MODEL_FILE = "digital_wellbeing_model.pkcls"


# ==========================================
# FEATURES - 8 INPUT FEATURES
# ==========================================

FEATURES = [
    "Age",
    "Gender",
    "Total_App_Usage_Hours",
    "Daily_Screen_Time_Hours",
    "Number_of_Apps_Used",
    "Social_Media_Usage_Hours",
    "Gaming_App_Usage_Hours",
    "Sleep_Hours"
]


# ==========================================
# TARGET
# ==========================================

TARGET = "Awareness_Level"


# ==========================================
# 1. LOAD DATASET
# ==========================================

try:

    df = pd.read_csv(DATASET_FILE)

    print("\n========================================")
    print("Dataset loaded successfully!")
    print("Dataset shape:", df.shape)
    print("========================================")

except Exception as e:

    print("Dataset Load Error:", e)
    raise


# ==========================================
# 2. CHECK COLUMNS
# ==========================================

print("\nDataset columns:")
print(df.columns.tolist())


missing_columns = [
    column
    for column in FEATURES + [TARGET]
    if column not in df.columns
]


if missing_columns:

    print("\nMissing columns:")
    print(missing_columns)

    raise ValueError(
        "Dataset columns do not match the model features."
    )


# ==========================================
# 3. SELECT FEATURES AND TARGET
# ==========================================

X = df[FEATURES].copy()
y = df[TARGET].copy()


# ==========================================
# 4. CONVERT GENDER
# ==========================================

def convert_gender(value):

    value = str(value).strip().lower()

    if value == "male":
        return 1

    elif value == "female":
        return 0

    else:
        return None


X["Gender"] = X["Gender"].apply(convert_gender)


# ==========================================
# CHECK GENDER
# ==========================================

if X["Gender"].isnull().any():

    print("\n========================================")
    print("INVALID GENDER VALUE FOUND")
    print("========================================")

    print(
        df.loc[
            X["Gender"].isnull(),
            "Gender"
        ].unique()
    )

    raise ValueError(
        "Gender must contain only Male or Female."
    )


# ==========================================
# 5. CONVERT NUMERIC COLUMNS
# ==========================================

numeric_columns = [
    "Age",
    "Total_App_Usage_Hours",
    "Daily_Screen_Time_Hours",
    "Number_of_Apps_Used",
    "Social_Media_Usage_Hours",
    "Gaming_App_Usage_Hours",
    "Sleep_Hours"
]


for column in numeric_columns:

    X[column] = pd.to_numeric(
        X[column],
        errors="coerce"
    )


# ==========================================
# 6. CHECK MISSING VALUES
# ==========================================

if X.isnull().sum().sum() > 0:

    print("\nMissing values found:")

    print(
        X.isnull().sum()
    )

    raise ValueError(
        "Please remove/fix missing values in the dataset."
    )


# ==========================================
# 7. SHOW FEATURES
# ==========================================

print("\n========================================")
print("FEATURES USED FOR TRAINING")
print("========================================")

for i, feature in enumerate(
    FEATURES,
    start=1
):

    print(
        i,
        "->",
        feature
    )


print("\nTarget:")
print(
    "->",
    TARGET
)


# ==========================================
# 8. SHOW GENDER VALUES
# ==========================================
print("\n========================================")
print("GENDER VALUES AFTER CONVERSION")
print("========================================")

print(
    X["Gender"].value_counts()
)


# ==========================================
# 9. TRAIN / TEST SPLIT
# ==========================================

X_train, X_test, y_train, y_test = train_test_split(

    X,
    y,

    test_size=0.20,

    random_state=42,

    stratify=y
)


print("\n========================================")

print(
    "Training data:",
    X_train.shape
)

print(
    "Testing data:",
    X_test.shape
)

print("========================================")


# ==========================================
# 10. RANDOM FOREST
# ==========================================

model = RandomForestClassifier(

    n_estimators=100,

    random_state=42,

    n_jobs=-1
)


# ==========================================
# 11. TRAIN MODEL
# ==========================================

model.fit(
    X_train,
    y_train
)


print(
    "\nRandom Forest training completed!"
)


# ==========================================
# 12. TEST MODEL
# ==========================================

y_pred = model.predict(
    X_test
)


accuracy = accuracy_score(
    y_test,
    y_pred
)


print("\n========================================")
print("MODEL ACCURACY")
print("========================================")

print(
    f"{accuracy * 100:.2f}%"
)


print("\n========================================")
print("CLASSIFICATION REPORT")
print("========================================")

print(
    classification_report(
        y_test,
        y_pred
    )
)


# ==========================================
# 13. SAVE MODEL
# ==========================================

with open(
    MODEL_FILE,
    "wb"
) as file:

    pickle.dump(
        model,
        file
    )


print("\n========================================")
print("MODEL SAVED SUCCESSFULLY")
print("========================================")

print(
    "File:",
    MODEL_FILE
)

print(
    "Features:",
    FEATURES
)

print(
    "Target:",
    TARGET
)

print("========================================")