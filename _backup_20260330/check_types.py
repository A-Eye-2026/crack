import os
import sys
sys.path.append(os.getcwd())
from app import app
from database import db
from sqlalchemy import text

with app.app_context():
    sql = text("SELECT report_id, confidence, damage_type FROM ai_results WHERE report_id IN (1440001, 1500001, 1530001)")
    rows = db.session.execute(sql).mappings().all()
    print("AI RESULTS FOR VIDEOS:")
    for r in rows:
        print(f"  ReportID:{r['report_id']} Conf:{r['confidence']} Type:{r['damage_type']}")
