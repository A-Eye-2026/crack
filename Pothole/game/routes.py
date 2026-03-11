from flask import Blueprint, render_template, request, jsonify

# ---------------------------------------------------------
# Aeye 전용 Game Blueprint (장기 게임 전용)
# ---------------------------------------------------------
game_bp = Blueprint(
    'game',
    __name__,
    template_folder='../templates',
    static_folder='../static/game_static',
    static_url_path='/game_static'
)

# ---------------------------------------------------------
# 장기 (Janggi) 라우트
# ---------------------------------------------------------

@game_bp.route('/janggi')
def janggi():
    """장기 게임 페이지 (AI: 클라이언트 사이드 미니맥스)"""
    return render_template('janggi_game.html', active_training=True)

# 체스/큐브는 기존 프로젝트에 유지되므로 Aeye에서는 제거됨

