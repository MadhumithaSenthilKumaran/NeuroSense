from flask import Blueprint, jsonify, request
from knowledge_base.kb_data import KNOWLEDGE_BASE

knowledge_bp = Blueprint("knowledge", __name__)


@knowledge_bp.get("/articles")
def articles():
    """Powers the 'About Alzheimer's' page with sourced, paraphrased summaries."""
    tag = request.args.get("tag")
    items = KNOWLEDGE_BASE
    if tag:
        items = [k for k in items if tag in k["tags"]]
    return jsonify(articles=items)