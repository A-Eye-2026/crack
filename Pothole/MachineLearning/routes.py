
from flask import Blueprint, render_template, request, jsonify, session
import numpy as np
import os
import sys

from .MLService import MLService
from .MLQuizService import MLQuizService

ml_bp = Blueprint('ml', __name__, template_folder='../templates', static_folder='../static/ml_static', static_url_path='/ml_static')

@ml_bp.route('/data_analysis/<int:session_id>')
def data_analysis_session(session_id):
    if 1 <= session_id <= 18:
        # 사용자의 학습 진행 현황 페치 (v281)
        user_id = session.get('user_id')
        completed_sessions = {}
        if user_id:
            try:
                completed_sessions = MLQuizService.get_progress(user_id)
            except:
                pass
        try:
            return render_template(f'ml_learning_{session_id}.html', 
                                   active_training=True, 
                                   session_id=session_id,
                                   completed_sessions=completed_sessions)
        except Exception as e:
            # Vercel 환경에서 템플릿 에러 추적을 위한 디버깅 출력
            return f"Template Error in session {session_id}: {str(e)}", 500
    return "Session not found", 404


# Legacy route for backward compatibility if needed, or redirect to /1
@ml_bp.route('/data_analysis')
def data_analysis_index():
    # Render the introduction page
    return render_template('ml_intro.html', active_training=True, session_id=0)

@ml_bp.route('/api/ml/session/<int:session_id>/intro', methods=['GET'])
def ml_session_intro(session_id):
    """세션 진입 시 필요한 배경 데이터/시각화 리턴"""
    if session_id == 2:
        chart = MLService.session2_intro_viz()
        return jsonify({'success': True, 'chart': chart})
    elif session_id == 4:
        chart = MLService.session4_intro_viz()
        return jsonify({'success': True, 'chart': chart})
    elif session_id == 5:
        chart = MLService.session5_intro_viz()
        return jsonify({'success': True, 'chart': chart})
    elif session_id == 6:
        data = MLService.session6_intro_viz()
        return jsonify({
            'success': True, 
            'linear_chart': data['linear_chart'],
            'comparison_chart': data['comparison_chart'],
            'table_chart': data['table_chart'],
            'ridge_alpha_chart': MLService.session6_ridge_alpha_graph(),
            'lasso_alpha_chart': MLService.session6_lasso_alpha_graph(),
            'feature_explosion_chart': MLService.session6_feature_explosion()
        })
    elif session_id == 7:
        sigmoid_chart = MLService.session7_intro_viz()
        coef_chart = MLService.session7_coef_viz()
        decision_chart = MLService.session7_decision_boundary()
        hyper_chart = MLService.session7_hyperparam_viz()
        loss_chart = MLService.session7_log_loss_viz()
        
        return jsonify({
            'success': True,
            'sigmoid_chart': sigmoid_chart,
            'coef_chart': coef_chart,
            'decision_chart': decision_chart,
            'hyper_chart': hyper_chart,
            'loss_chart': loss_chart
        })
    elif session_id == 8:
        return jsonify({
            'success': True,
            'init_data': MLService.session8_init_sgd(),
            'hinge_loss_chart': MLService.session8_hinge_loss_viz(),
            'loss_chart': MLService.session7_log_loss_viz()
        })
    elif session_id == 9:
        return jsonify({
            'success': True,
            'intro_chart': MLService.session9_intro_viz(),
            'gini_chart': MLService.session9_gini_explanation_viz(),
            'tree_data': MLService.session9_decision_tree_viz(max_depth=3),
            'feature_chart': MLService.session9_feature_importance_viz(),
            'overfit_data': MLService.session9_overfitting_comparison()
        })
    elif session_id == 10:
        return jsonify({
            'success': True,
            'intro_chart': MLService.session10_intro_viz()
        })
    return jsonify({'success': False, 'message': '지원하지 않는 세션입니다.'})

@ml_bp.route('/api/ml/session/<int:session_id>', methods=['POST'])
def api_ml_session(session_id):
    """세션별 ML 예측 API"""
    def get_float(d, key, default=0.0):
        val = d.get(key)
        if val is None or str(val).strip() == '':
            return default
        try:
            return float(val)
        except:
            return default

    try:
        data = request.json or {}
        result = None

        if session_id == 1:
            result = MLService.session1_predict(
                get_float(data, 'length', 25.0),
                get_float(data, 'weight', 150.0),
                int(get_float(data, 'k', 5.0))
            )
        elif session_id == 2:
            result = MLService.session2_split(
                get_float(data, 'test_ratio', 0.25),
                bool(data.get('use_stratify', True))
            )
        elif session_id == 3:
            result = MLService.session3_preprocess(
                get_float(data, 'length', 25.0),
                get_float(data, 'weight', 150.0)
            )
        elif session_id == 4:
            result = MLService.session4_predict(
                get_float(data, 'length', 30.0)
            )
        elif session_id == 5:
            result = MLService.session5_predict(
                get_float(data, 'length', 50.0)
            )
        elif session_id == 6:
            result = MLService.session6_regularization(
                get_float(data, 'alpha', 1.0)
            )
        elif session_id == 7:
            result = MLService.session7_predict(
                get_float(data, 'length', 25.0),
                get_float(data, 'height', 10.0),
                get_float(data, 'thickness', 4.0),
                get_float(data, 'weight', 250.0)
            )
        elif session_id == 9:
            result = MLService.session9_predict(
                get_float(data, 'alcohol', 10.0),
                get_float(data, 'sugar', 5.0),
                get_float(data, 'ph', 3.2),
                int(get_float(data, 'max_depth', 5))
            )
        elif session_id == 10:
            result = MLService.session10_predict(
                get_float(data, 'alcohol', 10.0),
                get_float(data, 'sugar', 5.0),
                get_float(data, 'ph', 3.2),
                data.get('model_type', 'rf')
            )
            
        if result:
            return jsonify({'success': True, 'data': result})
        return jsonify({'success': False, 'message': '세션 처리에 실패했습니다.'})

        def convert_numpy(obj):
            if isinstance(obj, np.integer): return int(obj)
            if isinstance(obj, np.floating): return float(obj)
            if isinstance(obj, np.ndarray): return obj.tolist()
            if isinstance(obj, dict): return {k: convert_numpy(v) for k, v in obj.items()}
            if isinstance(obj, list): return [convert_numpy(i) for i in obj]
            return obj

        return jsonify({'success': True, 'data': convert_numpy(result)})
    except Exception as e:
        import traceback
        print(f"ML API Error: {traceback.format_exc()}")
        return jsonify({'success': False, 'message': str(e)})

@ml_bp.route('/api/ml/session/6/intro', methods=['GET'])
def ml_session6_intro():
    try:
        intro_viz = MLService.session6_intro_viz() # 반환값이 dict
        feature_exp = MLService.session6_feature_explosion()
        poly_3d = MLService.session6_poly_3d_viz()
        ridge_graph = MLService.session6_ridge_alpha_graph()
        lasso_graph = MLService.session6_lasso_alpha_graph()
        
        return jsonify({
            'success': True,
            'linear_chart': intro_viz['linear_chart'],
            'comparison_chart': intro_viz['comparison_chart'],
            'table_chart': intro_viz['table_chart'],
            'feature_explosion_chart': feature_exp,
            'poly_3d_chart': poly_3d,
            'ridge_alpha_chart': ridge_graph,
            'lasso_alpha_chart': lasso_graph
        })
    except Exception as e:
        import traceback
        print(f"Session 6 Intro Error: {traceback.format_exc()}")
        return jsonify({'success': False, 'message': str(e)})

@ml_bp.route('/api/ml/session/7/random-binary', methods=['POST'])
def ml_session7_random_binary():
    try:
        data = request.json
        s1_idx = int(data.get('s1_idx', 0))
        s2_idx = int(data.get('s2_idx', 6))
        result = MLService.session7_dynamic_binary_viz(s1_idx, s2_idx)
        if result is None:
            return jsonify({'success': False, 'message': '어종 데이터가 부족합니다.'})
        def convert_numpy(obj):
            if isinstance(obj, np.integer): return int(obj)
            if isinstance(obj, np.floating): return float(obj)
            if isinstance(obj, np.ndarray): return obj.tolist()
            if isinstance(obj, dict): return {k: convert_numpy(v) for k, v in obj.items()}
            return obj
        return jsonify({'success': True, 'data': convert_numpy(result)})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@ml_bp.route('/api/ml/session/8/partial', methods=['POST'])
def ml_session8_partial():
    try:
        data = request.json
        curr = int(data.get('current_epochs', 1))
        add = int(data.get('add_epochs', 1))
        loss = data.get('loss', 'log_loss')
        result = MLService.session8_partial_fit(curr, add, loss)
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@ml_bp.route('/api/ml/session/8/optimize', methods=['POST'])
def ml_session8_optimize():
    try:
        data = request.json
        max_e = int(data.get('max_epochs', 300))
        result = MLService.session8_epoch_optimization(max_e)
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@ml_bp.route('/api/ml/session/8/raw-samples', methods=['GET'])
def ml_session8_raw_samples():
    try:
        samples = MLService.session8_get_raw_samples(n=10)
        return jsonify({'success': True, 'data': samples})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@ml_bp.route('/api/ml/session/8/intro', methods=['GET'])
def ml_session8_intro():
    try:
        init_res = MLService.session8_init_sgd(loss='log_loss')
        loss_chart = MLService.session7_log_loss_viz()
        hinge_chart = MLService.session8_hinge_loss_viz()
        return jsonify({
            'success': True, 
            'init_data': init_res,
            'loss_chart': loss_chart,
            'hinge_loss_chart': hinge_chart
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@ml_bp.route('/api/ml/session/8/weight-evolution', methods=['POST'])
def ml_session8_weight_evolution():
    try:
        data = request.json
        max_e = int(data.get('max_epochs', 100))
        loss = data.get('loss', 'log_loss')
        chart = MLService.session8_weight_evolution_viz(max_e, loss)
        return jsonify({'success': True, 'data': {'chart': chart}})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@ml_bp.route('/api/ml/session/8/hinge-interactive', methods=['POST'])
def ml_session8_hinge_interactive():
    try:
        data = request.json or {}
        target_fish = data.get('target', 'Bream')
        chart = MLService.session8_interactive_hinge_loss_viz(target_fish)
        return jsonify({'success': True, 'data': {'chart': chart}})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@ml_bp.route('/api/ml/session/8/accuracy-loss', methods=['POST'])
def ml_session8_accuracy_loss():
    try:
        data = request.json or {}
        max_e = int(data.get('max_epochs', 300))
        result = MLService.session8_accuracy_loss_dual_viz(max_e)
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@ml_bp.route('/api/ml/session/8/early-stopping', methods=['POST'])
def ml_session8_early_stopping():
    try:
        data = request.json or {}
        max_e = int(data.get('max_epochs', 300))
        patience = int(data.get('patience', 10))
        result = MLService.session8_early_stopping_viz(max_epochs=max_e, patience=patience)
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@ml_bp.route('/api/ml/session/9/distributions', methods=['GET'])
def ml_session9_distributions():
    try:
        chart = MLService.session9_distributions_viz()
        return jsonify({'success': True, 'data': {'chart': chart}})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@ml_bp.route('/api/ml/session/9/cross-validation', methods=['POST'])
def ml_session9_cross_validation():
    try:
        data = request.json or {}
        n_splits = int(data.get('n_splits', 5))
        result = MLService.session9_cross_validation_viz(n_splits)
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@ml_bp.route('/api/ml/session/9/grid-search', methods=['POST'])
def ml_session9_grid_search():
    try:
        result = MLService.session9_grid_search_viz()
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@ml_bp.route('/api/ml/session/9/random-search', methods=['POST'])
def ml_session9_random_search():
    try:
        result = MLService.session9_random_search_viz()
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@ml_bp.route('/api/ml/session/9/raw-samples', methods=['GET'])
def ml_session9_raw_samples():
    try:
        samples = MLService.session9_get_raw_samples(n=15)
        return jsonify({'success': True, 'data': samples})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@ml_bp.route('/api/ml/session/9/logistic-vs-tree', methods=['POST'])
def ml_session9_logistic_vs_tree():
    try:
        result = MLService.session9_logistic_vs_tree_viz()
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@ml_bp.route('/api/ml/session/9/scaling-compare', methods=['POST'])
def ml_session9_scaling_compare():
    try:
        result = MLService.session9_scaling_comparison_viz()
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@ml_bp.route('/api/ml/session/9/unbalanced-tree', methods=['POST'])
def ml_session9_unbalanced_tree():
    try:
        result = MLService.session9_unbalanced_tree_viz()
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@ml_bp.route('/api/ml/session/9/hyper-tuning', methods=['POST'])
def ml_session9_hyper_tuning():
    try:
        data = request.json or {}
        depth = int(data.get('depth', 5))
        impurity = float(data.get('impurity', 0.0001))
        split = int(data.get('split', 2))
        
        result = MLService.session9_hyper_tuning_viz(depth, impurity, split)
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@ml_bp.route('/api/ml/session/10/importance', methods=['POST'])
def ml_session10_importance():
    try:
        data = request.json or {}
        model_type = data.get('model_type', 'rf')
        chart = MLService.session10_importance_viz(model_type)
        return jsonify({'success': True, 'data': {'chart': chart}})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@ml_bp.route('/api/ml/session/10/importance-all', methods=['GET'])
def ml_session10_importance_all():
    try:
        chart = MLService.session10_all_importance_viz()
        return jsonify({'success': True, 'data': {'chart': chart}})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@ml_bp.route('/api/ml/session/10/forest-trees', methods=['GET'])
def ml_session10_forest_trees():
    try:
        chart = MLService.session10_forest_trees_viz()
        return jsonify({'success': True, 'data': {'chart': chart}})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@ml_bp.route('/api/ml/session/11/intro', methods=['GET'])
def ml_session11_intro():
    try:
        chart1 = MLService.session11_intro_viz()
        chart2 = MLService.session11_pixel_mean_viz()
        return jsonify({'success': True, 'data': {'chart1': chart1, 'chart2': chart2}})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@ml_bp.route('/api/ml/session/17/intro', methods=['GET'])
def ml_session17_intro():
    try:
        # CNN 필터 및 특성 맵 시각화 데이터 응답
        filter_chart = MLService.session17_cnn_filter_viz()
        feature_chart = MLService.session17_feature_map_viz()
        return jsonify({
            'success': True, 
            'data': {
                'filter_chart': filter_chart, 
                'feature_chart': feature_chart
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@ml_bp.route('/api/ml/session/18/intro', methods=['GET'])
def ml_session18_intro():
    try:
        # 실제 모델 기반 CNN 시각화 (기본값: 필터)
        result = MLService.session18_cnn_visual_viz(visual_type='filter')
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@ml_bp.route('/api/ml/session/18/visualize', methods=['POST'])
def ml_session18_visualize():
    try:
        data = request.json or {}
        v_type = data.get('type', 'filter')
        result = MLService.session18_cnn_visual_viz(visual_type=v_type)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})



@ml_bp.route('/api/ml/session/11/search', methods=['POST'])
def ml_session11_search():
    try:
        target = request.json.get('target', 'apple')
        result = MLService.session11_search_closest_target(target)
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# --- 12강 K-Means 관련 API ---

@ml_bp.route('/api/ml/session/12/cluster', methods=['POST'])
def ml_session12_cluster():
    try:
        cluster_id = request.json.get('cluster_id', 0)
        result = MLService.session12_get_cluster_fruits(cluster_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# --- 퀴즈 시스템 API ---

@ml_bp.route('/api/ml/quiz/<int:session_id>', methods=['GET'])
def api_get_quiz(session_id):
    if 'user_id' not in session:
        return jsonify({"success": False, "message": "로그인이 필요한 서비스입니다."}), 401
    
    quiz_list = MLQuizService.get_quiz(session_id)
    # 보안상 정답(answer)은 제외하고 클라이언트에 전송
    safe_quiz = []
    for q in quiz_list:
        safe_q = q.copy()
        del safe_q['answer']
        safe_quiz.append(safe_q)
        
    return jsonify({"success": True, "quiz": safe_quiz})

@ml_bp.route('/api/ml/quiz/<int:session_id>/submit', methods=['POST'])
def api_submit_quiz(session_id):
    if 'user_id' not in session:
        return jsonify({"success": False, "message": "로그인이 필요합니다."}), 401
    
    data = request.json
    answers = data.get('answers', {})
    
    success, message = MLQuizService.submit_answers(session['user_id'], session_id, answers)
    return jsonify({"success": success, "message": message})

@ml_bp.route('/api/ml/quiz/status', methods=['GET'])
def api_get_quiz_status():
    if 'user_id' not in session:
        return jsonify({"success": False, "progress": {}})
    
    progress = MLQuizService.get_progress(session['user_id'])
    return jsonify({"success": True, "progress": progress})

@ml_bp.route('/api/ml/quiz/total-progress', methods=['GET'])
def api_get_total_progress():
    if 'user_id' not in session:
        return jsonify({"success": False, "total_progress": 0})
    
    total_progress = MLQuizService.get_total_progress(session['user_id'])
    return jsonify({"success": True, "total_progress": total_progress})

# --- 코딩 분석 코드 서버 제공 API (v294) ---
@ml_bp.route('/api/ml/code/<int:session_id>', methods=['GET'])
def api_get_ml_code(session_id):
    try:
        # MachineLearning/static/codes/session_X.txt
        file_path = os.path.join(os.path.dirname(__file__), 'static', 'codes', f'session_{session_id}.txt')
        if not os.path.exists(file_path):
            return jsonify({"success": False, "message": "해당 세션의 코드가 준비되지 않았습니다."}), 404
        
        with open(file_path, 'r', encoding='utf-8') as f:
            code_text = f.read()
        return jsonify({"success": True, "code": code_text})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
