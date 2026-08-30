import os
import json
import zen

DECISION_TABLE_PATH = os.path.join(os.path.dirname(__file__), "decision_table.json")

try:
    with open(DECISION_TABLE_PATH, "r", encoding="utf-8") as f:
        decision_content = json.load(f)
    engine = zen.ZenEngine()
    decision = engine.create_decision(decision_content)
except Exception as e:
    decision = None


def evaluate_recommendation(input_data: dict) -> dict:
    if decision is None:
        return {"result": "ALLOWED", "fallback": True}
    try:
        return decision.evaluate(input_data)
    except Exception as e:
        return {"result": "HUMAN_REVIEW", "error": str(e)}