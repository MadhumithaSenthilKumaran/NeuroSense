from datetime import datetime, timezone


def now():
    return datetime.now(timezone.utc)


def new_user_doc(
    name,
    email,
    password_hash,
    age=None,
    gender=None,
    phone=None,
    education=None,
    occupation=None,
    guardian_email=None,
    guardian_phone=None,
    consent_share=False,
):
    return {
        "name": name,
        "email": email.lower().strip(),
        "password_hash": password_hash,
        "age": age,
        "gender": gender,
        "phone": phone,
        "education": education,
        "occupation": occupation,
        "guardian_email": guardian_email,
        "guardian_phone": guardian_phone,
        "consent_share": consent_share,
        "role": "user",
        "created_at": now(),
    }


def new_assessment_doc(user_id):
    return {
        "user_id": user_id,
        "status": "in_progress",
        "created_at": now(),
        "updated_at": now(),
    }
