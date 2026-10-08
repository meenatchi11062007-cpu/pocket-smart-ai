import json
from ..models import Recommendation
def save(db,uid,kind,budget,data,result):
    r=Recommendation(user_id=uid,planner_type=kind,budget=budget,input_summary=json.dumps(data),result_json=json.dumps(result)); db.add(r); db.commit(); db.refresh(r); return r
def history(db,uid): return db.query(Recommendation).filter(Recommendation.user_id==uid).order_by(Recommendation.created_at.desc()).all()
