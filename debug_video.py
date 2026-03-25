import os
import sys
import cv2

# 프로젝트 루트 경로 추가
sys.path.insert(0, '.')

from app import app, db
from models import Report, VideoDetection, AiResult

def debug_analysis(report_id):
    with app.app_context():
        rpt = Report.query.get(report_id)
        if not rpt:
            print(f"Error: Report {report_id} not found")
            return
        
        print(f"Analyzing Report {report_id}: {rpt.file_path}")
        
        # 기존 데이터 삭제 (재실험을 위해)
        VideoDetection.query.filter_by(report_id=report_id).delete()
        AiResult.query.filter_by(report_id=report_id).delete()
        db.session.commit()
        
        # app.py의 분석 로직 수동 실행
        # (app.py의 run_ai_analysis 로직을 그대로 복사해오거나 호출)
        from app import run_ai_analysis
        
        # Thread 대신 직접 실행하여 로그 확인
        run_ai_analysis(rpt.id, rpt.file_path, rpt.file_type)
        
        # 결과 확인
        dets = VideoDetection.query.filter_by(report_id=report_id).all()
        print(f"\nFinal VideoDetection count: {len(dets)}")
        for d in dets[:3]:
            print(f"  {d.frame_time}s: {d.class_name} ({d.confidence:.2f})")
            
        ai = AiResult.query.filter_by(report_id=report_id).first()
        print(f"AiResult: {ai.damage_type} ({ai.confidence}%)" if ai else "AiResult: NOT SAVED")
        
        rt = Report.query.get(report_id)
        print(f"Report status: {rt.status}")
        print(f"Report thumbnail: {rt.thumbnail_path}")

if __name__ == '__main__':
    # 1380002번 (mp4 경로가 살아있는 최신 제보)로 테스트
    debug_analysis(1380002)
