import os
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

from config import Config
from extensions import jwt, init_db

load_dotenv()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["MODEL_DIR"], exist_ok=True)

    CORS(app, origins=app.config["CORS_ORIGINS"], supports_credentials=True)
    jwt.init_app(app)
    init_db(app)

    # --- Blueprints ---
    from routes.auth import auth_bp
    from routes.assessment import assessment_bp
    from routes.speech import speech_bp
    from routes.cognitive import cognitive_bp
    from routes.lifestyle import lifestyle_bp
    from routes.reports import reports_bp
    from routes.admin import admin_bp
    from routes.knowledge import knowledge_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(assessment_bp, url_prefix="/api/assessment")
    app.register_blueprint(speech_bp, url_prefix="/api/speech")
    app.register_blueprint(cognitive_bp, url_prefix="/api/cognitive")
    app.register_blueprint(lifestyle_bp, url_prefix="/api/lifestyle")
    app.register_blueprint(reports_bp, url_prefix="/api/reports")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    app.register_blueprint(knowledge_bp, url_prefix="/api/knowledge")

    @app.get("/api/health")
    def health():
        return jsonify(status="ok", service="neurosense-api")

    @app.errorhandler(404)
    def not_found(e):
        return jsonify(error="Not found"), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify(error="Internal server error"), 500

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)