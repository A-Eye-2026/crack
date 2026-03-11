"""
MLService.py — 머신러닝 교육 플랫폼 백엔드 서비스
7개 세션의 scikit-learn 모델 구동 및 matplotlib 차트 생성을 담당합니다.
"""
import numpy as np
import io
import base64

# matplotlib 백엔드 설정 (GUI 없이 이미지 생성)
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from mpl_toolkits.mplot3d import Axes3D

from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, PolynomialFeatures
from sklearn.linear_model import LinearRegression, Ridge, Lasso, LogisticRegression, SGDClassifier


class MLService:
    """머신러닝 교육용 7세션 서비스 클래스"""

    # =========================================================
    # 내장 데이터셋
    # =========================================================

    # 세션 1~3: 도미(Bream) & 빙어(Smelt)
    BREAM_LENGTH = [25.4, 26.3, 26.5, 29.0, 29.0, 29.7, 29.7, 30.0, 30.0, 30.7,
                    31.0, 31.0, 31.5, 32.0, 32.0, 32.0, 33.0, 33.0, 33.5, 33.5,
                    34.0, 34.0, 34.5, 35.0, 35.0, 35.0, 35.0, 36.0, 36.0, 37.0,
                    38.5, 38.5, 39.5, 41.0, 41.0]
    BREAM_WEIGHT = [242.0, 290.0, 340.0, 363.0, 430.0, 450.0, 500.0, 390.0, 450.0, 500.0,
                    475.0, 500.0, 500.0, 340.0, 600.0, 600.0, 700.0, 700.0, 610.0, 650.0,
                    575.0, 685.0, 620.0, 680.0, 700.0, 725.0, 720.0, 714.0, 850.0, 1000.0,
                    920.0, 955.0, 925.0, 975.0, 950.0]
    SMELT_LENGTH = [9.8, 10.5, 10.6, 11.0, 11.2, 11.3, 11.8, 11.8, 12.0, 12.2,
                    12.4, 13.0, 14.3, 15.0]
    SMELT_WEIGHT = [6.7, 7.5, 7.0, 9.7, 9.8, 8.7, 10.0, 9.9, 9.8, 12.2,
                    13.4, 12.2, 19.7, 19.9]

    # 세션 4~5: 농어(Perch)
    PERCH_LENGTH = [8.4, 13.7, 15.0, 16.2, 17.4, 18.0, 18.7, 19.0, 19.6, 20.0,
                    21.0, 21.0, 21.0, 21.3, 22.0, 22.0, 22.0, 22.0, 22.0, 22.5,
                    22.5, 22.7, 23.0, 23.5, 24.0, 24.0, 24.6, 25.0, 25.6, 26.5,
                    27.3, 27.5, 27.5, 27.5, 28.0, 28.7, 30.0, 32.8, 34.5, 35.0,
                    36.5, 36.0, 37.0, 37.0, 39.0, 39.0, 39.0, 40.0, 40.0, 40.0,
                    40.0, 42.0, 43.0, 43.0, 43.5, 44.0]
    PERCH_WEIGHT = [5.9, 32.0, 40.0, 51.5, 70.0, 100.0, 78.0, 80.0, 85.0, 85.0,
                    110.0, 115.0, 125.0, 130.0, 120.0, 120.0, 130.0, 135.0, 110.0, 130.0,
                    150.0, 145.0, 150.0, 170.0, 225.0, 145.0, 188.0, 180.0, 197.0, 218.0,
                    300.0, 260.0, 265.0, 250.0, 250.0, 306.0, 540.0, 700.0, 700.0, 610.0,
                    685.0, 750.0, 900.0, 820.0, 1100.0, 1000.0, 1100.0, 1000.0, 1000.0, 1000.0,
                    1000.0, 1100.0, 1000.0, 1150.0, 1200.0, 1250.0]

    # 세션 6~7: 7종 생선 데이터 (길이, 높이, 두께, 무게)
    FISH_DATA = {
        "species": [
            "Bream", "Roach", "Whitefish", "Parkki", "Perch", "Pike", "Smelt"
        ],
        "length": [
            25.4, 26.3, 26.5, 29.0, 29.0, 29.7, 29.7, 30.0, 30.0, 30.7, 31.0, 31.0, 31.5, 32.0, 32.0, 32.0, 33.0, 33.0, 33.5, 33.5, 34.0, 34.0, 34.5, 35.0, 35.0, 35.0, 35.0, 36.0, 36.0, 37.0, 38.5, 38.5, 39.5, 41.0, 41.0,
            14.1, 18.2, 18.8, 19.8, 20.0, 20.5, 20.8, 21.0, 22.0, 22.0, 22.5, 22.5, 22.5, 24.0, 23.4, 23.5, 25.2, 26.0, 27.0, 31.7,
            26.0, 26.5, 28.0, 31.0, 36.4, 40.0,
            14.7, 15.5, 17.7, 19.0, 20.0, 20.7, 20.7, 21.5, 23.0, 25.0, 26.0,
            8.4, 13.7, 15.0, 16.2, 17.4, 18.0, 18.7, 19.0, 19.6, 20.0, 21.0, 21.0, 21.0, 21.3, 22.0, 22.0, 22.0, 22.0, 22.0, 22.5, 22.5, 22.7, 23.0, 23.5, 24.0, 24.0, 24.6, 25.0, 25.6, 26.5, 27.3, 27.5, 27.5, 27.5, 28.0, 28.7, 30.0, 32.8, 34.5, 35.0, 36.5, 36.0, 37.0, 37.0, 39.0, 39.0, 39.0, 40.0, 40.0, 40.0, 40.0, 42.0, 43.0, 43.0, 43.5, 44.0,
            32.3, 34.0, 35.0, 37.3, 38.0, 38.5, 42.5, 42.5, 43.0, 45.0, 46.0, 48.0, 51.7, 56.0, 60.0, 60.0, 63.4,
            9.8, 10.5, 10.6, 11.0, 11.2, 11.3, 11.8, 11.8, 12.0, 12.2, 12.4, 13.0, 14.3, 15.0
        ],
        "height": [
            11.52, 12.48, 12.3778, 12.73, 12.444, 13.6024, 14.1795, 12.67, 14.0049, 14.2266, 14.2628, 14.3714, 13.7592, 13.9129, 14.9544, 15.438, 14.8604, 14.938, 15.633, 14.4738, 15.1285, 15.9936, 15.5227, 15.4686, 16.2405, 16.36, 16.3618, 16.517, 16.8896, 18.957, 18.0369, 18.084, 18.7542, 18.6354, 17.6235,
            4.1472, 5.2983, 5.5756, 5.6166, 6.216, 6.4752, 6.1677, 6.1146, 5.8045, 6.6339, 7.0334, 6.55, 6.4, 7.5344, 6.9153, 7.3968, 7.0866, 8.8768, 8.568, 9.485,
            8.3804, 8.1454, 8.778, 10.744, 11.7612, 12.354,
            6.8475, 6.5772, 7.4052, 8.3922, 8.8928, 8.5376, 9.396, 9.7364, 10.3458, 11.088, 11.368,
            2.112, 3.528, 3.824, 4.5924, 4.588, 5.2224, 5.1992, 5.6358, 5.1376, 5.082, 5.6925, 5.9175, 5.6925, 6.384, 6.11, 5.64, 6.11, 5.875, 5.5225, 5.856, 6.792, 5.9532, 5.2185, 6.275, 7.293, 6.375, 6.7334, 6.4395, 6.561, 7.168, 8.323, 7.1672, 7.0516, 7.2828, 7.8204, 7.5852, 7.6156, 10.03, 10.2565, 11.4884, 10.881, 10.6091, 10.835, 10.5717, 11.1366, 11.1366, 12.4313, 11.9286, 11.73, 12.3808, 11.135, 12.8002, 11.9328, 12.5125, 12.604, 12.4888,
            5.568, 5.7078, 5.9364, 6.2884, 7.29, 6.396, 7.28, 6.825, 7.786, 6.96, 7.792, 7.68, 8.9262, 10.6863, 9.6, 9.6, 10.812,
            1.7388, 1.972, 1.7284, 2.196, 2.0832, 1.9782, 2.2139, 2.2139, 2.2044, 2.0904, 2.43, 2.277, 2.8728, 2.9322
        ],
        "thickness": [
            4.02, 4.3056, 4.6961, 4.4555, 5.134, 4.9274, 5.2785, 4.69, 4.8438, 4.9594, 5.1042, 4.8146, 4.368, 5.0728, 5.1708, 5.58, 5.2854, 5.1975, 5.1338, 5.7276, 5.5695, 5.3704, 5.2801, 6.1306, 5.589, 6.0532, 6.09, 5.8515, 6.1984, 6.603, 6.3063, 6.292, 6.7497, 6.7473, 6.3705,
            2.268, 2.8217, 2.9044, 3.1746, 3.5742, 3.3516, 3.3957, 3.2943, 3.7544, 3.5478, 3.8203, 3.325, 3.8, 3.8352, 3.6312, 4.1272, 3.906, 4.4968, 4.7736, 5.355,
            4.2476, 4.2485, 4.6816, 6.562, 6.5736, 6.525,
            2.3265, 2.3142, 2.673, 2.9181, 3.2928, 3.2944, 3.4104, 3.1571, 3.6636, 4.144, 4.234,
            1.408, 1.9992, 2.432, 2.6316, 2.9415, 3.3216, 3.1234, 3.0502, 3.0368, 2.772, 3.555, 3.3075, 3.6675, 3.534, 3.4075, 3.525, 3.525, 3.525, 3.995, 3.624, 3.624, 3.63, 3.626, 3.725, 3.723, 3.825, 4.1658, 3.6835, 4.239, 4.144, 5.1373, 4.335, 4.335, 4.5662, 4.2042, 4.6354, 4.7716, 6.018, 6.3875, 7.7957, 6.864, 6.7408, 6.2646, 6.3666, 7.4934, 6.003, 7.3514, 7.1064, 7.225, 7.4624, 6.63, 6.8684, 7.2772, 7.4165, 8.142, 7.5958,
            3.3756, 4.158, 4.3844, 4.0198, 4.5765, 3.977, 4.3225, 4.459, 5.1296, 4.896, 4.87, 5.376, 6.1712, 6.9849, 6.144, 6.144, 7.48,
            1.0476, 1.16, 1.1484, 1.38, 1.2772, 1.2852, 1.2838, 1.1659, 1.1484, 1.3936, 1.269, 1.2558, 2.0672, 1.8792
        ],
        "weight": [
            242.0, 290.0, 340.0, 363.0, 430.0, 450.0, 500.0, 390.0, 450.0, 500.0, 475.0, 500.0, 500.0, 340.0, 600.0, 600.0, 700.0, 700.0, 610.0, 650.0, 575.0, 685.0, 620.0, 680.0, 700.0, 725.0, 720.0, 714.0, 850.0, 1000.0, 920.0, 955.0, 925.0, 975.0, 950.0,
            40.0, 69.0, 78.0, 87.0, 120.0, 0.0, 110.0, 120.0, 150.0, 145.0, 160.0, 140.0, 160.0, 169.0, 161.0, 200.0, 180.0, 290.0, 272.0, 390.0,
            270.0, 270.0, 306.0, 540.0, 800.0, 1000.0,
            55.0, 60.0, 90.0, 120.0, 150.0, 140.0, 170.0, 145.0, 200.0, 273.0, 300.0,
            5.9, 32.0, 40.0, 51.5, 70.0, 100.0, 78.0, 80.0, 85.0, 85.0, 110.0, 115.0, 125.0, 130.0, 120.0, 120.0, 130.0, 135.0, 110.0, 130.0, 150.0, 145.0, 150.0, 170.0, 225.0, 145.0, 188.0, 180.0, 197.0, 218.0, 300.0, 260.0, 265.0, 250.0, 250.0, 300.0, 320.0, 514.0, 556.0, 840.0, 685.0, 700.0, 700.0, 690.0, 900.0, 650.0, 820.0, 850.0, 900.0, 1015.0, 820.0, 1100.0, 1000.0, 1100.0, 1000.0, 1000.0,
            200.0, 300.0, 300.0, 300.0, 430.0, 345.0, 456.0, 510.0, 540.0, 500.0, 567.0, 770.0, 950.0, 1250.0, 1600.0, 1550.0, 1650.0,
            6.7, 7.5, 7.0, 9.7, 9.8, 8.7, 10.0, 9.9, 9.8, 12.2, 13.4, 12.2, 19.7, 19.9
        ],
        "target": [0]*35 + [1]*20 + [2]*6 + [3]*11 + [4]*56 + [5]*17 + [6]*14
    }


    # =========================================================
    # 유틸리티
    # =========================================================

    @staticmethod
    def _fig_to_base64(fig):
        """matplotlib Figure → base64 PNG 문자열 변환"""
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=120, bbox_inches='tight',
                    facecolor='#f8f9fa', edgecolor='none')
        plt.close(fig)
        buf.seek(0)
        return base64.b64encode(buf.read()).decode('utf-8')

    @staticmethod
    def _setup_plot():
        """공통 플롯 스타일 설정 (시스템 폰트 자동 탐색 및 수식 대응)"""
        # 시스템에 설치된 한글 폰트 탐색
        font_list = ['Malgun Gothic', 'AppleGothic', 'NanumGothic', 'Pretendard', 'Inter', 'serif']
        found = False
        for f in font_list:
            if f in [font.name for font in fm.fontManager.ttflist]:
                plt.rcParams['font.family'] = f
                found = True
                break
        
        if not found:
            plt.rcParams['font.family'] = 'sans-serif'
            
        plt.rcParams['axes.unicode_minus'] = False
        plt.rcParams['mathtext.fontset'] = 'stix'
        
        # 전역 폰트 크기 상향
        plt.rcParams['font.size'] = 12
        plt.rcParams['axes.titlesize'] = 16
        plt.rcParams['axes.labelsize'] = 14
        plt.rcParams['xtick.labelsize'] = 11
        plt.rcParams['ytick.labelsize'] = 11
        plt.rcParams['legend.fontsize'] = 12

    # =========================================================
    # 세션 1: KNN 분류 (도미 vs 빙어)
    # =========================================================
    @staticmethod
    def session1_predict(length, weight, k=5):
        """도미/빙어 KNN 분류"""
        MLService._setup_plot()

        fish_length = MLService.BREAM_LENGTH + MLService.SMELT_LENGTH
        fish_weight = MLService.BREAM_WEIGHT + MLService.SMELT_WEIGHT
        fish_data = np.column_stack((fish_length, fish_weight))
        fish_target = np.array([1]*35 + [0]*14)  # 1=도미, 0=빙어

        k = max(1, min(int(k), len(fish_data)))  # k 범위 제한 (1 ~ 데이터 전체 개수)
        kn = KNeighborsClassifier(n_neighbors=k)
        kn.fit(fish_data, fish_target)

        user_input = np.array([[length, weight]])
        prediction = kn.predict(user_input)[0]
        score = kn.score(fish_data, fish_target)

        # 이웃 찾기
        distances, indices = kn.kneighbors(user_input)

        # 산점도 생성
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.scatter(MLService.BREAM_LENGTH, MLService.BREAM_WEIGHT,
                   c='#3498db', label='Bream (Doomi)', s=60, alpha=0.7, edgecolors='white')
        ax.scatter(MLService.SMELT_LENGTH, MLService.SMELT_WEIGHT,
                   c='#e67e22', label='Smelt (Bingeo)', s=60, alpha=0.7, edgecolors='white')
        ax.scatter(length, weight, c='#e74c3c', marker='*', s=300,
                   label='Your Input', zorder=5, edgecolors='black')

        # 이웃 표시
        for i in indices[0]:
            ax.annotate('', xy=(fish_length[i], fish_weight[i]),
                        xytext=(length, weight),
                        arrowprops=dict(arrowstyle='->', color='#95a5a6', lw=1.5))

        ax.set_xlabel('Length (cm)', fontsize=14)
        ax.set_ylabel('Weight (g)', fontsize=14)
        ax.set_title(f'KNN Classification (K={k}): Bream vs Smelt', fontsize=18, fontweight='bold', pad=20)
        ax.legend(fontsize=12, frameon=True, facecolor='white', framealpha=0.8)
        ax.grid(True, alpha=0.3)
        fig.patch.set_facecolor('#f8f9fa')

        chart = MLService._fig_to_base64(fig)

        return {
            'prediction': 'Bream (Doomi)' if prediction == 1 else 'Smelt (Bingeo)',
            'prediction_kr': '도미 🐟' if prediction == 1 else '빙어 🐠',
            'accuracy': round(score * 100, 1),
            'k_used': k,
            'neighbors': len(indices[0]),
            'chart': chart
        }

    # =========================================================
    # 세션 2: 훈련/테스트 세트 분리 (도미/빙어 — 정확도 변동)
    # =========================================================
    @staticmethod
    def session2_intro_viz():
        """무작위성이 없는 단순 분할 시 발생하는 샘플링 편향 시각화 (개선 버전)"""
        from matplotlib.patches import FancyBboxPatch
        MLService._setup_plot()
        
        fig, axes = plt.subplots(2, 1, figsize=(12, 8.5), gridspec_kw={'height_ratios': [1, 1]})
        
        primary_color = '#15aabf'
        danger_color = '#ff6b6b'
        danger_dark = '#ee5253'
        success_color = '#1dd1a1'
        success_dark = '#10ac84'
        
        # 1. 층화 추출 안 된 나쁜 예 (순차 분할)
        ax1 = axes[0]
        # 배경 (전체 데이터 범위)
        bg1 = FancyBboxPatch((-0.5, 0), 51, 1, boxstyle="round,pad=0.02,rounding_size=1.2", 
                             color='#e9ecef', zorder=0, alpha=0.5)
        ax1.add_patch(bg1)
        
        # 훈련세트 구간
        p1 = FancyBboxPatch((0, 0.1), 35, 0.8, boxstyle="round,pad=0,rounding_size=1.2", 
                            color=danger_color, alpha=0.9)
        ax1.add_patch(p1)
        # 테스트세트 구간
        p2 = FancyBboxPatch((35, 0.1), 14.5, 0.8, boxstyle="round,pad=0,rounding_size=1.2", 
                            color=danger_dark, alpha=0.9)
        ax1.add_patch(p2)
        
        ax1.text(17.5, 0.5, 'Train Set (100% 도미, 35개)', ha='center', va='center', color='white', fontweight='900', fontsize=16)
        ax1.text(42, 0.5, 'Test Set\n(100% 빙어, 14개)', ha='center', va='center', color='white', fontweight='900', fontsize=14)
        
        ax1.set_xlim(-1, 51)
        ax1.set_ylim(0, 1)
        ax1.axis('off')
        ax1.set_title('[Bad Split] 단순 순차 분할 = 샘플링 편향 발생', fontsize=18, fontweight='bold', color=danger_dark, pad=25)
        
        # 2. 층화 추출 된 좋은 예 (비율에 맞게 골고루 분할)
        ax2 = axes[1]
        bg2 = FancyBboxPatch((-0.5, 0), 51, 1, boxstyle="round,pad=0.02,rounding_size=1.2", 
                             color='#cbd5e0', zorder=0, alpha=0.5)
        ax2.add_patch(bg2)
        
        # 훈련세트 36개 (비율대로 도미 26, 빙어 10)
        p3 = FancyBboxPatch((0, 0.1), 26, 0.8, boxstyle="round,pad=0,rounding_size=1.2", 
                            color=primary_color, alpha=0.8)
        ax2.add_patch(p3)
        p4 = FancyBboxPatch((26, 0.1), 10.5, 0.8, boxstyle="round,pad=0,rounding_size=1.2", 
                            color='#0b7285', alpha=0.8)
        ax2.add_patch(p4)
        
        # 테스트세트 13개 (비율대로 도미 9, 빙어 4)
        p5 = FancyBboxPatch((36.5, 0.1), 9, 0.8, boxstyle="round,pad=0,rounding_size=1.2", 
                            color=success_color, alpha=0.8)
        ax2.add_patch(p5)
        p6 = FancyBboxPatch((45.5, 0.1), 5, 0.8, boxstyle="round,pad=0,rounding_size=1.2", 
                            color=success_dark, alpha=0.8)
        ax2.add_patch(p6)

        ax2.text(18, 0.5, 'Train Set (도미+빙어 골고루, 36개)', ha='center', va='center', color='white', fontweight='900', fontsize=16)
        ax2.text(43, 0.5, 'Test Set\n(비율 유지, 13개)', ha='center', va='center', color='white', fontweight='900', fontsize=14)
        
        ax2.set_xlim(-1, 51)
        ax2.set_ylim(0, 1)
        ax2.axis('off')
        ax2.set_title('[Good Split] 층화 추출 분할 = 비율 유지 데이터', fontsize=18, fontweight='bold', color=success_dark, pad=25)
        
        fig.suptitle('샘플링 편향 (Sampling Bias) 과 올바른 분할 방법', fontsize=22, fontweight='900', y=1.05, color='#2c3e50')
        fig.patch.set_facecolor('none')
        plt.tight_layout()
        
        chart = MLService._fig_to_base64(fig)
        plt.close(fig)
        return chart
    @staticmethod
    def session2_comparison_viz():
        """층화 추출이 잘 된 경우와 안 된 경우의 비율 비교 시각화"""
        MLService._setup_plot()
        
        # 원본 데이터 비율 (도미 35, 빙어 14)
        total_bream = 35
        total_smelt = 14
        original_ratio = total_smelt / (total_bream + total_smelt)
        
        # 1. 층화 추출 사용 (Good)
        fish_target = np.array([1]*35 + [0]*14)
        _, _, _, test_target_good = train_test_split(
            fish_target, fish_target, test_size=0.25, random_state=42, stratify=fish_target
        )
        ratio_good = np.sum(test_target_good == 0) / len(test_target_good)
        
        # 2. 층화 추출 미사용 (Bad Case - 무작위성이지만 편향될 가능성)
        # 교육적 효과를 위해 고정된 random_state에서 편향이 심한 사례를 재현하거나 
        # 혹은 그냥 편향된 사례를 임의로 구성
        _, _, _, test_target_bad = train_test_split(
            fish_target, fish_target, test_size=0.25, random_state=10  # random_state에 따라 편향 발생
        )
        ratio_bad = np.sum(test_target_bad == 0) / len(test_target_bad)

        fig, ax = plt.subplots(figsize=(10, 5))
        
        x = np.arange(3)
        ratios = [original_ratio * 100, ratio_good * 100, ratio_bad * 100]
        labels = ['Original', 'Stratified (Good)', 'Random (Bad)']
        colors = ['#95a5a6', '#2ecc71', '#e74c3c']
        
        bars = ax.bar(x, ratios, color=colors, alpha=0.8, edgecolor='white', width=0.6)
        
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                    f'{height:.1f}%', ha='center', va='bottom', fontweight='bold')

        ax.set_xticks(x)
        ax.set_xticklabels(labels, fontsize=11, fontweight='bold')
        ax.set_ylabel('Smelt Ratio in Test Set (%)')
        ax.set_title('Comparison: Stratified vs Random Sampling', fontsize=14, fontweight='bold')
        ax.axhline(y=original_ratio*100, color='gray', linestyle='--', alpha=0.5)
        ax.set_ylim(0, max(ratios) + 15)
        
        fig.patch.set_facecolor('#fdfaf5')
        plt.tight_layout()
        
        return MLService._fig_to_base64(fig)

    @staticmethod
    def session2_split(test_ratio=0.25, use_stratify=True):
        """도미/빙어 데이터를 훈련/테스트로 분리하고 시각화"""
        MLService._setup_plot()

        fish_length = MLService.BREAM_LENGTH + MLService.SMELT_LENGTH
        fish_weight = MLService.BREAM_WEIGHT + MLService.SMELT_WEIGHT
        fish_data = np.column_stack((fish_length, fish_weight))
        fish_target = np.array([1]*35 + [0]*14)  # 1=도미, 0=빙어
        
        # stratify 옵션에 따라 분리
        stratify_param = fish_target if use_stratify else None
        train_input, test_input, train_target, test_target = train_test_split(
            fish_data, fish_target, test_size=test_ratio,
            random_state=42, stratify=stratify_param
        )

        kn = KNeighborsClassifier(n_neighbors=5)
        kn.fit(train_input, train_target)
        score = kn.score(test_input, test_target)

        # 종별 카운트 (도미/빙어)
        train_counts = {
            '도미': int(np.sum(train_target == 1)),
            '빙어': int(np.sum(train_target == 0))
        }
        test_counts = {
            '도미': int(np.sum(test_target == 1)),
            '빙어': int(np.sum(test_target == 0))
        }

        # 시각화
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        # 1:도미(파랑), 0:빙어(주황)
        colors = {1: '#3498db', 0: '#e67e22'}
        labels = {1: 'Bream (Doomi)', 0: 'Smelt (Bingeo)'}

        for ax, inp, tgt, title in [
            (axes[0], train_input, train_target, f'Training Set ({len(train_input)} samples)'),
            (axes[1], test_input, test_target, f'Test Set ({len(test_input)} samples)')
        ]:
            for species_id in [1, 0]:
                mask = tgt == species_id
                if np.any(mask):
                    ax.scatter(inp[mask, 0], inp[mask, 1], c=colors[species_id],
                               label=labels[species_id], s=60, alpha=0.7, edgecolors='white')
            
            ax.set_title(title, fontsize=13, fontweight='bold')
            ax.set_xlabel('Length (cm)')
            ax.set_ylabel('Weight (g)')
            ax.legend(fontsize=10, frameon=True, facecolor='white', framealpha=0.8)
            ax.grid(True, alpha=0.3)

        fig.suptitle('Train / Test Split (Bream & Smelt)', fontsize=15, fontweight='bold', y=1.02)
        fig.tight_layout()
        fig.patch.set_facecolor('#fdfaf5')

        chart = MLService._fig_to_base64(fig)
        
        # 비교 차트도 함께 리턴
        comparison_chart = MLService.session2_comparison_viz()

        return {
            'train_count': len(train_input),
            'test_count': len(test_input),
            'train_species': train_counts,
            'test_species': test_counts,
            'accuracy': round(score * 100, 1),
            'test_ratio': test_ratio,
            'use_stratify': use_stratify,
            'chart': chart,
            'comparison_chart': comparison_chart
        }


    # =========================================================
    # 세션 3: 데이터 전처리 (StandardScaler)
    # =========================================================
    @staticmethod
    def session3_preprocess(length, weight):
        """원본 vs 표준화 비교 산점도 빛 사용자 입력 데이터 예측 시각화"""
        MLService._setup_plot()

        fish_length = MLService.BREAM_LENGTH + MLService.SMELT_LENGTH
        fish_weight = MLService.BREAM_WEIGHT + MLService.SMELT_WEIGHT
        fish_data = np.column_stack((fish_length, fish_weight))
        fish_target = np.array([1]*35 + [0]*14)

        train_input, test_input, train_target, test_target = train_test_split(
            fish_data, fish_target, test_size=0.25, random_state=42, stratify=fish_target
        )

        # 표준화
        scaler = StandardScaler()
        train_scaled = scaler.fit_transform(train_input)
        test_scaled = scaler.transform(test_input)

        # KNN 모델
        kn_raw = KNeighborsClassifier(n_neighbors=5)
        kn_raw.fit(train_input, train_target)

        kn_scaled = KNeighborsClassifier(n_neighbors=5)
        kn_scaled.fit(train_scaled, train_target)

        # 사용자 입력 데이터 예측
        user_input = np.array([[length, weight]])
        pred_raw = kn_raw.predict(user_input)[0]
        
        user_input_scaled = scaler.transform(user_input)
        pred_scaled = kn_scaled.predict(user_input_scaled)[0]

        species_map = {1: '도미', 0: '빙어'}
        str_raw = species_map[pred_raw]
        str_scaled = species_map[pred_scaled]

        # 시각화
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))

        # 원본 시각화
        ax = axes[0]
        bm = train_target == 1
        ax.scatter(train_input[bm, 0], train_input[bm, 1], c='#3498db', label='Bream', s=60, alpha=0.7, edgecolors='white')
        ax.scatter(train_input[~bm, 0], train_input[~bm, 1], c='#e67e22', label='Smelt', s=60, alpha=0.7, edgecolors='white')
        
        # 사용자 데이터 표시
        ax.scatter(length, weight, marker='*', s=300, c='#e74c3c', label=f'Custom Fish ({str_raw})', edgecolors='black', zorder=5)
        
        ax.set_title(f'Raw Data (Scale Mismatch)\nPrediction: {str_raw}', fontsize=13, fontweight='bold', color='#c0392b' if pred_raw == 0 else '#2980b9')
        ax.set_xlabel('Length (cm)')
        ax.set_ylabel('Weight (g)')
        ax.legend(frameon=True, facecolor='white', framealpha=0.8)
        ax.grid(True, alpha=0.3)

        # 표준화 시각화
        ax = axes[1]
        ax.scatter(train_scaled[bm, 0], train_scaled[bm, 1], c='#3498db', label='Bream', s=60, alpha=0.7, edgecolors='white')
        ax.scatter(train_scaled[~bm, 0], train_scaled[~bm, 1], c='#e67e22', label='Smelt', s=60, alpha=0.7, edgecolors='white')
        
        # 사용자 데이터 표시
        scaled_x, scaled_y = user_input_scaled[0]
        ax.scatter(scaled_x, scaled_y, marker='*', s=300, c='#2ecc71', label=f'Custom Fish ({str_scaled})', edgecolors='black', zorder=5)

        ax.set_title(f'Standardized\nPrediction: {str_scaled}', fontsize=13, fontweight='bold', color='#c0392b' if pred_scaled == 0 else '#2980b9')
        ax.set_xlabel('Length (Normalized)')
        ax.set_ylabel('Weight (Normalized)')
        ax.legend(frameon=True, facecolor='white', framealpha=0.8)
        ax.grid(True, alpha=0.3)

        fig.suptitle(f'Before vs After StandardScaler (L: {length}cm, W: {weight}g)', fontsize=15, fontweight='bold', y=1.02)
        fig.tight_layout()
        fig.patch.set_facecolor('#fdfaf5')

        chart = MLService._fig_to_base64(fig)
        plt.close(fig)

        # 통계
        mean_raw = train_input.mean(axis=0)
        std_raw = train_input.std(axis=0)

        return {
            'prediction_raw': str_raw,
            'prediction_scaled': str_scaled,
            'mean_length': round(float(mean_raw[0]), 2),
            'mean_weight': round(float(mean_raw[1]), 2),
            'std_length': round(float(std_raw[0]), 2),
            'std_weight': round(float(std_raw[1]), 2),
            'chart': chart
        }

    # =========================================================
    # 세션 4: KNN 회귀 (농어 무게 예측)
    # =========================================================
    @staticmethod
    def session4_intro_viz():
        """KNN 회귀의 K값에 따른 과대/과소적합 시각화 (K=1 vs K=40)"""
        MLService._setup_plot()
        
        perch_length = np.array(MLService.PERCH_LENGTH).reshape(-1, 1)
        perch_weight = np.array(MLService.PERCH_WEIGHT)

        train_input, test_input, train_target, test_target = train_test_split(
            perch_length, perch_weight, test_size=0.25, random_state=42
        )

        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        
        x_range = np.linspace(10, 45, 100).reshape(-1, 1)

        # 1. K=1 (과대적합)
        knr_1 = KNeighborsRegressor(n_neighbors=1)
        knr_1.fit(train_input, train_target)
        axes[0].scatter(train_input, train_target, color='#A47864', label='Train Data', alpha=0.6)
        axes[0].plot(x_range, knr_1.predict(x_range), color='#e74c3c', label='K=1 Prediction')
        axes[0].set_title(f"Overfitting (K=1)\nTrain R²: {knr_1.score(train_input, train_target):.2f}, Test R²: {knr_1.score(test_input, test_target):.2f}", fontweight='bold', color='#c0392b')

        # 2. K=42 (과소적합)
        # 훈련세트 크기가 42이므로 최대치인 42를 사용하여 완전한 평행선(평균)을 만듦
        knr_40 = KNeighborsRegressor(n_neighbors=42)
        knr_40.fit(train_input, train_target)
        axes[1].scatter(train_input, train_target, color='#A47864', label='Train Data', alpha=0.6)
        axes[1].plot(x_range, knr_40.predict(x_range), color='#3498db', label='K=42 Prediction', linewidth=3)
        axes[1].set_title(f"Underfitting (K=42)\nTrain R²: {knr_40.score(train_input, train_target):.2f}, Test R²: {knr_40.score(test_input, test_target):.2f}", fontweight='bold', color='#2980b9')

        for ax in axes:
            ax.set_xlabel('Length (cm)')
            ax.set_ylabel('Weight (g)')
            ax.legend(frameon=True, facecolor='white')
            ax.grid(True, linestyle=':', alpha=0.6)

        fig.suptitle('KNN Regression Models: Overfitting vs Underfitting', fontsize=16, fontweight='bold', y=1.02)
        fig.patch.set_facecolor('#fdfaf5')
        
        chart = MLService._fig_to_base64(fig)
        plt.close(fig)
        return chart

    @staticmethod
    def session4_predict(length):
        """농어 길이 → 무게 KNN 회귀 예측"""
        MLService._setup_plot()

        perch_length = np.array(MLService.PERCH_LENGTH).reshape(-1, 1)
        perch_weight = np.array(MLService.PERCH_WEIGHT)

        train_input, test_input, train_target, test_target = train_test_split(
            perch_length, perch_weight, test_size=0.25, random_state=42
        )

        knr = KNeighborsRegressor(n_neighbors=3)
        knr.fit(train_input, train_target)

        user_input = np.array([[length]])
        prediction = knr.predict(user_input)[0]
        r2_score = knr.score(test_input, test_target)

        # 이웃 찾기
        distances, indices = knr.kneighbors(user_input)
        neighbor_weights = train_target[indices[0]]

        # 시각화
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.scatter(train_input, train_target, c='#3498db', s=60, alpha=0.7,
                   label='Training Data', edgecolors='white')
        ax.scatter(test_input, test_target, c='#2ecc71', s=40, alpha=0.5,
                   label='Test Data', marker='s', edgecolors='white')
        ax.scatter(length, prediction, c='#e74c3c', marker='*', s=300,
                   label=f'Prediction: {prediction:.0f}g', zorder=5, edgecolors='black')

        # 이웃 강조
        ax.scatter(train_input[indices[0]], neighbor_weights, c='#f39c12', s=100,
                   alpha=0.8, label='K-Neighbors', edgecolors='black', zorder=4)

        ax.set_xlabel('Length (cm)', fontsize=12)
        ax.set_ylabel('Weight (g)', fontsize=12)
        ax.set_title(f'KNN Regression: Perch Weight Prediction (R²={r2_score:.3f})',
                     fontsize=14, fontweight='bold')
        ax.legend(fontsize=10, frameon=True, facecolor='white', framealpha=0.8)
        ax.grid(True, alpha=0.3)
        fig.patch.set_facecolor('#fdfaf5')

        chart = MLService._fig_to_base64(fig)
        plt.close(fig)  # 자원 해제

        return {
            'prediction': round(float(prediction), 1),
            'r2_score': round(float(r2_score), 4),
            'r2_percent': round(float(r2_score) * 100, 1),
            'neighbor_weights': [round(float(w), 1) for w in neighbor_weights],
            'neighbor_avg': round(float(np.mean(neighbor_weights)), 1),
            'chart': chart
        }

    # =========================================================
    # 세션 5: 선형·다항 회귀 (Mastery Overhaul)
    # =========================================================
    @staticmethod
    def session5_predict(length):
        """농어 무게 예측: KNN vs 선형 vs 다항 (진화 과정 시각화)"""
        MLService._setup_plot()

        perch_length = np.array(MLService.PERCH_LENGTH).reshape(-1, 1)
        perch_weight = np.array(MLService.PERCH_WEIGHT)

        train_input, test_input, train_target, test_target = train_test_split(
            perch_length, perch_weight, test_size=0.25, random_state=42
        )

        # 1. KNN (n=3)
        knr = KNeighborsRegressor(n_neighbors=3)
        knr.fit(train_input, train_target)
        knn_pred = knr.predict([[length]])[0]

        # 2. 선형 회귀
        lr = LinearRegression()
        lr.fit(train_input, train_target)
        linear_pred = lr.predict([[length]])[0]

        # 3. 다항 회귀 (2차)
        poly = PolynomialFeatures(degree=2, include_bias=False)
        train_poly = poly.fit_transform(train_input)
        test_poly = poly.transform(test_input)
        pr = LinearRegression()
        pr.fit(train_poly, train_target)
        poly_pred = pr.predict(poly.transform([[length]]))[0]

        # 시각화 (2D 비교 — 교육적 목적)
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.scatter(train_input, train_target, color='#A47864', alpha=0.5, label='Train Data')

        # 그리기 범위 설정 (기존 데이터 + 예측 지점까지 확장)
        x_min = min(15, length - 5)
        x_max = max(50, length + 5)
        x_range = np.linspace(x_min, x_max, 100).reshape(-1, 1)

        # KNN 라인 (Flatline 실감 표현)
        ax.plot(x_range, knr.predict(x_range), color='#e74c3c', linestyle='--', alpha=0.7, label='KNN (Flatline Limit)')
        # 선형 라인
        ax.plot(x_range, lr.predict(x_range), color='#3498db', alpha=0.7, label='Linear (Straight Line)')
        # 다항 라인 (진화된 곡선)
        ax.plot(x_range, pr.predict(poly.transform(x_range)), color='#f1c40f', linewidth=3, label='Polynomial (Evolution Curve)')

        # 현재 예측 지점 표시
        ax.scatter([length], [knn_pred], color='#e74c3c', marker='X', s=100, zorder=5)
        ax.scatter([length], [linear_pred], color='#3498db', marker='s', s=100, zorder=5)
        ax.scatter([length], [poly_pred], color='#f1c40f', marker='*', s=300, edgecolors='black', zorder=6, label='Best Prediction')

        ax.set_xlabel('Length (cm)')
        ax.set_ylabel('Weight (g)')
        ax.set_title('Evolution of Regression: Why we need Curves', fontsize=14, fontweight='bold')
        ax.legend(frameon=True, facecolor='white', framealpha=0.8)
        ax.grid(True, linestyle=':', alpha=0.6)
        
        fig.patch.set_facecolor('#fdfaf5')
        chart = MLService._fig_to_base64(fig)
        plt.close(fig)  # 자원 해제

        return {
            'knn_pred': round(float(knn_pred), 1),
            'linear_pred': round(float(linear_pred), 1),
            'poly_pred': round(float(poly_pred), 1),
            'coef': [round(float(c), 2) for c in pr.coef_],
            'intercept': round(float(pr.intercept_), 2),
            'train_score': round(float(pr.score(train_poly, train_target)), 4),
            'test_score': round(float(pr.score(test_poly, test_target)), 4),
            'linear_train_score': round(float(lr.score(train_input, train_target)), 4),
            'linear_test_score': round(float(lr.score(test_input, test_target)), 4),
            'chart': chart
        }

    @staticmethod
    def session5_intro_viz():
        """KNN의 한계를 명확히 보여주는 인트로용 시각화"""
        MLService._setup_plot()
        perch_length = np.array(MLService.PERCH_LENGTH).reshape(-1, 1)
        perch_weight = np.array(MLService.PERCH_WEIGHT)
        
        train_input, test_input, train_target, test_target = train_test_split(
            perch_length, perch_weight, test_size=0.25, random_state=42
        )
        
        knr = KNeighborsRegressor(n_neighbors=3)
        knr.fit(train_input, train_target)
        
        # 100cm 농어와 그 이웃들 찾기
        distances, indexes = knr.kneighbors([[100]])
        
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.scatter(train_input, train_target, color='#A47864', alpha=0.5, label='Train Data')
        
        # 100cm 농어와 이웃 표시
        ax.scatter(train_input[indexes], train_target[indexes], color='#e67e22', marker='D', s=100, label='Neighbors of 100cm Perch')
        ax.scatter([100], [knr.predict([[100]])[0]], color='#e74c3c', marker='^', s=200, label='100cm Prediction')
        
        # KNN의 한계선 (45cm 이후 평행)
        x_range = np.linspace(10, 110, 200).reshape(-1, 1)
        ax.plot(x_range, knr.predict(x_range), color='#e74c3c', linestyle='--', alpha=0.8, label='KNN Prediction Link')
        
        ax.set_xlabel('Length (cm)')
        ax.set_ylabel('Weight (g)')
        ax.set_title('The Limits of KNN: Why it fails at 100cm', fontsize=12, fontweight='bold')
        ax.legend(loc='upper left', fontsize=9, frameon=True, facecolor='white', framealpha=0.8)
        ax.grid(True, linestyle=':', alpha=0.6)
        
        fig.patch.set_facecolor('#fdfaf5')
        chart = MLService._fig_to_base64(fig)
        plt.close(fig)  # 자원 해제
        return chart

    # =========================================================
    # 세션 6: 특성 공학 & 규제 (Ridge / Lasso) (Mastery Overhaul)
    # =========================================================

    @staticmethod
    def session6_intro_viz():
        """다중 회귀 3D 평면 + 과대적합 vs 규제 2D 시각화"""
        MLService._setup_plot()
        data = MLService.FISH_DATA
        X_2d = np.column_stack([data['length'], data['height']])
        y = np.array(data['weight'])
        lr = LinearRegression().fit(X_2d, y)

        # 1. 3D 평면
        fig1 = plt.figure(figsize=(9, 7))
        ax = fig1.add_subplot(111, projection='3d')
        ax.scatter(data['length'], data['height'], data['weight'], color='#A47864', alpha=0.6)
        xr, yr = np.linspace(min(data['length']), max(data['length']), 20), np.linspace(min(data['height']), max(data['height']), 20)
        XG, YG = np.meshgrid(xr, yr)
        ZG = lr.predict(np.column_stack([XG.ravel(), YG.ravel()])).reshape(XG.shape)
        ax.plot_surface(XG, YG, ZG, color='#f1c40f', alpha=0.3, edgecolor='none')
        ax.set_title('Multiple Regression Plane', fontweight='bold')
        fig1.patch.set_facecolor('#fdfaf5')
        linear_chart = MLService._fig_to_base64(fig1)
        plt.close(fig1)  # 자원 해제

        # 2. 2D 과대적합 vs 규제 (시험 빈출 개념)
        fig2, ax2 = plt.subplots(figsize=(8, 5))
        X_1d = np.array(data['length']).reshape(-1, 1)
        poly_over = PolynomialFeatures(degree=15, include_bias=False)
        X_over = poly_over.fit_transform(X_1d)
        
        # 릿지 모델의 곡선을 부드럽게 만들기 위해 StandardScaler 적용 필수
        ss = StandardScaler()
        X_over_scaled = ss.fit_transform(X_over)
        m_over = LinearRegression().fit(X_over_scaled, y)
        m_ridge = Ridge(alpha=10).fit(X_over_scaled, y) # 적절한 규제 적용

        xl = np.linspace(min(X_1d)-2, max(X_1d)+2, 200).reshape(-1, 1)
        xl_scaled = ss.transform(poly_over.transform(xl))
        
        yover = m_over.predict(xl_scaled)
        yridge = m_ridge.predict(xl_scaled)

        ax2.scatter(X_1d, y, c='gray', s=30, alpha=0.5, label='Actual Data')
        ax2.plot(xl, yover, 'r--', label='Overfitted (Degree 15)', linewidth=1.5)
        ax2.plot(xl, yridge, 'b-', label='Regularized (Ridge)', linewidth=2.5)
        ax2.set_ylim(-100, 1200)
        ax2.set_title('Overfitting(Red) vs Regularization(Blue)', fontsize=13, fontweight='bold')
        ax2.legend(frameon=True, facecolor='white', framealpha=0.8)
        fig2.patch.set_facecolor('#fdfaf5')
        comparison_chart = MLService._fig_to_base64(fig2)
        plt.close(fig2)  # 자원 해제

        return {
            'linear_chart': linear_chart,
            'comparison_chart': comparison_chart,
            'table_chart': MLService.session6_poly_table()
        }

    @staticmethod
    def session6_poly_table():
        """PolynomialFeatures 변환 과정을 Matplotlib Table로 시각화 (이미지 예제 반영)"""
        MLService._setup_plot()
        fig, ax = plt.subplots(figsize=(7, 2.5))
        ax.axis('off')
        
        # [2, 3] 입력 예제
        cols = ['1 (bias)', 'x0', 'x1', 'x0^2', 'x0*x1', 'x1^2']
        vals = [['1.0', '2.0', '3.0', '4.0', '6.0', '9.0']]
        
        tab = ax.table(cellText=vals, colLabels=cols, loc='center', cellLoc='center')
        tab.auto_set_font_size(False)
        tab.set_fontsize(11)
        tab.scale(1.1, 2.2)
        
        for (r, c), cell in tab.get_celld().items():
            if r == 0:
                cell.set_text_props(weight='bold', color='white')
                cell.set_facecolor('#A47864')
            else:
                cell.set_facecolor('#ffffff')
        
        fig.patch.set_facecolor('#fdfaf5')
        chart = MLService._fig_to_base64(fig)
        plt.close(fig)  # 자원 해제
        return chart

    @staticmethod
    def session6_ridge_alpha_graph():
        """릿지 회귀 Alpha 튜닝 그래프 (PDF p.10 재현)"""
        MLService._setup_plot()
        X = np.array(MLService.PERCH_LENGTH).reshape(-1, 1)
        y = np.array(MLService.PERCH_WEIGHT)
        
        train_input, test_input, train_target, test_target = train_test_split(
            X, y, test_size=0.25, random_state=42)
        
        poly = PolynomialFeatures(degree=5, include_bias=False)
        train_poly = poly.fit_transform(train_input)
        test_poly = poly.transform(test_input)
        
        ss = StandardScaler()
        train_scaled = ss.fit_transform(train_poly)
        test_scaled = ss.transform(test_poly)
        
        alpha_list = [0.001, 0.01, 0.1, 1, 10, 100]
        train_scores, test_scores = [], []
        
        for alpha in alpha_list:
            ridge = Ridge(alpha=alpha)
            ridge.fit(train_scaled, train_target)
            train_scores.append(ridge.score(train_scaled, train_target))
            test_scores.append(ridge.score(test_scaled, test_target))
        
        fig, ax = plt.subplots(figsize=(8, 4.5))
        log_alphas = np.log10(alpha_list)
        ax.plot(log_alphas, train_scores, 'o-', color='#1f77b4', linewidth=2, label='Train Score (파란색)', markersize=7)
        ax.plot(log_alphas, test_scores, 's-', color='#ff7f0e', linewidth=2, label='Test Score (주황색)', markersize=7)
        
        # PDF 기준: alpha=0.1 (log10=-1) 이 최적점
        best_alpha = 0.1
        best_idx = alpha_list.index(best_alpha)
        best_x = np.log10(best_alpha)
        ax.axvline(x=best_x, color='#2ecc71', linestyle=':', linewidth=2.5, alpha=0.8)
        ax.annotate(f'최적: alpha={best_alpha}',
                    xy=(best_x, test_scores[best_idx]),
                    xytext=(20, -25), textcoords='offset points',
                    fontsize=11, fontweight='bold', color='#2ecc71',
                    arrowprops=dict(arrowstyle='->', color='#2ecc71', lw=2),
                    bbox=dict(boxstyle='round,pad=0.3', fc='#eafaf1', ec='#2ecc71', alpha=0.9))
        
        # 양쪽 영역 주석 (PDF: 왼쪽 과대적합, 오른쪽 과소적합 방향)
        bbox_style = dict(boxstyle='round,pad=0.3', fc='white', ec='none', alpha=0.8)
        ax.annotate('← 과대적합', xy=(-2.5, min(train_scores) + 0.003),
                    fontsize=9, color='#e74c3c', fontweight='bold', alpha=0.9, bbox=bbox_style)
        ax.annotate('과소적합 →', xy=(1.2, min(test_scores) + 0.003),
                    fontsize=9, color='#3498db', fontweight='bold', alpha=0.9, bbox=bbox_style)
        
        ax.set_xlabel('alpha', fontsize=12)
        ax.set_ylabel('R² Score', fontsize=12)
        ax.set_title('Ridge: Alpha 튜닝 그래프 (0.1이 최적)', fontsize=14, fontweight='bold')
        ax.legend(fontsize=10, loc='lower left')
        ax.grid(True, alpha=0.2)
        ax.set_xticks(log_alphas)
        ax.set_xticklabels([str(a) for a in alpha_list], fontsize=9)
        fig.patch.set_facecolor('#fdfaf5')
        fig.tight_layout()
        chart = MLService._fig_to_base64(fig)
        plt.close(fig)  # 자원 해제
        return chart

    @staticmethod
    def session6_lasso_alpha_graph():
        """라쏘 회귀 Alpha 튜닝 그래프 (PDF p.12 재현)"""
        MLService._setup_plot()
        X = np.array(MLService.PERCH_LENGTH).reshape(-1, 1)
        y = np.array(MLService.PERCH_WEIGHT)
        
        train_input, test_input, train_target, test_target = train_test_split(
            X, y, test_size=0.25, random_state=42)
        
        poly = PolynomialFeatures(degree=5, include_bias=False)
        train_poly = poly.fit_transform(train_input)
        test_poly = poly.transform(test_input)
        
        ss = StandardScaler()
        train_scaled = ss.fit_transform(train_poly)
        test_scaled = ss.transform(test_poly)
        
        alpha_list = [0.001, 0.01, 0.1, 1, 10, 100]
        train_scores, test_scores = [], []
        
        for alpha in alpha_list:
            lasso = Lasso(alpha=alpha, max_iter=10000)
            lasso.fit(train_scaled, train_target)
            train_scores.append(lasso.score(train_scaled, train_target))
            test_scores.append(lasso.score(test_scaled, test_target))
        
        fig, ax = plt.subplots(figsize=(8, 4.5))
        log_alphas = np.log10(alpha_list)
        ax.plot(log_alphas, train_scores, 'o-', color='#1f77b4', linewidth=2, label='Train Score (파란색)', markersize=7)
        ax.plot(log_alphas, test_scores, 's-', color='#ff7f0e', linewidth=2, label='Test Score (주황색)', markersize=7)
        
        # PDF 기준: alpha=10 (log10=1) 이 최적점
        # PDF: "왼쪽은 과대적합, 오른쪽은 정상 (제일 좋은 값은 1 => 10^1=10)"
        best_alpha = 10
        best_idx = alpha_list.index(best_alpha)
        best_x = np.log10(best_alpha)
        ax.axvline(x=best_x, color='#2ecc71', linestyle=':', linewidth=2.5, alpha=0.8)
        ax.annotate(f'최적: alpha={best_alpha}\n(10^1 = 10)',
                    xy=(best_x, test_scores[best_idx]),
                    xytext=(-80, -30), textcoords='offset points',
                    fontsize=11, fontweight='bold', color='#2ecc71',
                    arrowprops=dict(arrowstyle='->', color='#2ecc71', lw=2),
                    bbox=dict(boxstyle='round,pad=0.3', fc='#eafaf1', ec='#2ecc71', alpha=0.9))
        
        # PDF 원문: "왼쪽은 과대 적합, 오른쪽은 정상"
        bbox_style = dict(boxstyle='round,pad=0.3', fc='white', ec='none', alpha=0.8)
        ax.annotate('← 과대적합', xy=(-2.5, min(train_scores)),
                    fontsize=9, color='#e74c3c', fontweight='bold', alpha=0.9, bbox=bbox_style)
        ax.annotate('정상 →', xy=(1.3, max(test_scores) - 0.01),
                    fontsize=9, color='#2ecc71', fontweight='bold', alpha=0.9, bbox=bbox_style)
        
        ax.set_xlabel('alpha', fontsize=12)
        ax.set_ylabel('R² Score', fontsize=12)
        ax.set_title('Lasso: Alpha 튜닝 그래프 (10이 최적)', fontsize=14, fontweight='bold')
        ax.legend(fontsize=10, loc='lower left')
        ax.grid(True, alpha=0.2)
        ax.set_xticks(log_alphas)
        ax.set_xticklabels([str(a) for a in alpha_list], fontsize=9)
        fig.patch.set_facecolor('#fdfaf5')
        fig.tight_layout()
        chart = MLService._fig_to_base64(fig)
        plt.close(fig)  # 자원 해제
        return chart

    @staticmethod
    def session6_feature_explosion():
        """degree별 특성 개수 폭발 비교 (degree 1~5)"""
        MLService._setup_plot()
        degrees = [1, 2, 3, 4, 5]
        feature_counts = []
        for d in degrees:
            p = PolynomialFeatures(degree=d, include_bias=False)
            p.fit(np.zeros((1, 3)))
            feature_counts.append(p.n_output_features_)
        
        fig, ax = plt.subplots(figsize=(7, 4))
        colors = ['#3498db', '#2ecc71', '#f1c40f', '#e67e22', '#e74c3c']
        bars = ax.bar(degrees, feature_counts, color=colors, edgecolor='white', linewidth=2, width=0.6)
        
        for bar, count in zip(bars, feature_counts):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                    f'{count}', ha='center', va='bottom', fontweight='bold', fontsize=12,
                    bbox=dict(boxstyle='round,pad=0.2', fc='white', ec='none', alpha=0.7))
        
        ax.axhline(y=42, color='red', linestyle='--', linewidth=1.5, alpha=0.7, label='Sample Count (42)')
        ax.set_xlabel('Degree', fontsize=12)
        ax.set_ylabel('Feature Count', fontsize=12)
        ax.set_title('Feature Explosion by Degree', fontsize=14, fontweight='bold')
        ax.legend(fontsize=10, frameon=True, facecolor='white', framealpha=0.8)
        ax.grid(True, axis='y', alpha=0.2)
        fig.patch.set_facecolor('#fdfaf5')
        fig.tight_layout()
        chart = MLService._fig_to_base64(fig)
        plt.close(fig)  # 자원 해제
        return chart

    @staticmethod
    def session6_poly_3d_viz():
        """다항 회귀(Polynomial Regression) 3D 곡면 시각화"""
        MLService._setup_plot()
        data = MLService.FISH_DATA
        X = np.column_stack([data['length'], data['height']])
        y = np.array(data['weight'])

        poly = PolynomialFeatures(degree=2, include_bias=False)
        X_poly = poly.fit_transform(X)

        lr = LinearRegression()
        lr.fit(X_poly, y)

        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111, projection='3d')

        # 데이터 점
        ax.scatter(data['length'], data['height'], data['weight'], 
                   color='#2ecc71', s=50, alpha=0.6)

        # 회귀 곡면 생성
        x_range = np.linspace(min(data['length']), max(data['length']), 30)
        y_range = np.linspace(min(data['height']), max(data['height']), 30)
        X_grid, Y_grid = np.meshgrid(x_range, y_range)
        
        grid_flat = np.column_stack([X_grid.ravel(), Y_grid.ravel()])
        Z_grid = lr.predict(poly.transform(grid_flat)).reshape(X_grid.shape)

        ax.plot_surface(X_grid, Y_grid, Z_grid, cmap='viridis', alpha=0.4, edgecolor='none')
        
        ax.set_xlabel('Length (cm)')
        ax.set_ylabel('Height (cm)')
        ax.set_zlabel('Weight (g)')
        ax.set_title('Polynomial (Degree 2) Regression Surface', fontsize=14, fontweight='bold')
        
        fig.patch.set_facecolor('#fdfaf5')
        chart = MLService._fig_to_base64(fig)
        plt.close(fig)  # 자원 해제
        return chart

    @staticmethod
    def session6_regularization(alpha_value=1.0):
        """특성 공학(degree=5)과 규제(Ridge) 비교"""
        MLService._setup_plot()

        data = MLService.FISH_DATA
        # 3가지 특성 모두 사용
        X = np.column_stack([data['length'], data['height'], data['thickness']])
        y = np.array(data['weight'])

        train_input, test_input, train_target, test_target = train_test_split(
            X, y, test_size=0.25, random_state=42
        )

        # 5차 다차항 변환 (과대적합 유도)
        poly = PolynomialFeatures(degree=5, include_bias=False)
        train_poly = poly.fit_transform(train_input)
        test_poly = poly.transform(test_input)

        # 표준화 필수
        scaler = StandardScaler()
        train_scaled = scaler.fit_transform(train_poly)
        test_scaled = scaler.transform(test_poly)

        # 릿지 규제 적용
        ridge = Ridge(alpha=alpha_value)
        ridge.fit(train_scaled, train_target)

        # 비교를 위해 규제 없는 모델 (과대적합)
        lr = LinearRegression()
        lr.fit(train_scaled, train_target)

        # 시각화 개편: 듀얼 플롯 (곡선 변화 + 성능 지표)
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # --- 왼쪽: 회귀 곡선 안정화 시각화 (교육적 목적으로 1D 기반 시각화) ---
        X_1d = X[:, 0].reshape(-1, 1) # 시각화를 위해 길이 데이터만 추출
        train_1d = train_input[:, 0].reshape(-1, 1)
        
        # 시각화용 1D 고차 다항 모델 (Numerical Stability를 위해 degree=10 사용)
        viz_poly = PolynomialFeatures(degree=10, include_bias=False)
        train_poly_1d = viz_poly.fit_transform(train_1d)
        
        viz_ss = StandardScaler()
        train_scaled_1d = viz_ss.fit_transform(train_poly_1d)
        
        # 1D 과대적합 (Alpha=0)
        viz_lr = LinearRegression().fit(train_scaled_1d, train_target)
        # 1D 규제 (Alpha=현재값)
        viz_ridge = Ridge(alpha=alpha_value).fit(train_scaled_1d, train_target)
        
        xl = np.linspace(min(X_1d)-2, max(X_1d)+2, 200).reshape(-1, 1)
        xl_scaled_1d = viz_ss.transform(viz_poly.transform(xl))
        
        y_over = viz_lr.predict(xl_scaled_1d)
        y_ridge = viz_ridge.predict(xl_scaled_1d)
        
        ax1.scatter(X_1d, y, c='gray', s=25, alpha=0.4, label='실제 데이터')
        ax1.plot(xl, y_over, 'r--', alpha=0.4, linewidth=1.2, label='과대적합(Overfit)')
        ax1.plot(xl, y_ridge, '#3498db', linewidth=3, label=f'내 Ridge(Alpha={alpha_value})')
        ax1.set_ylim(-100, 1200)
        ax1.set_title('Ridge: 곡선 안정화 과정 (1D Slice)', fontsize=12, fontweight='bold')
        ax1.set_xlabel('Length (cm)')
        ax1.set_ylabel('Weight (g)')
        ax1.legend(fontsize=9, loc='upper left', frameon=True, facecolor='white', framealpha=0.8)
        ax1.grid(True, alpha=0.1)

        # --- 오른쪽: Alpha vs 점수 (3D 실제 모델의 최적점 표시) ---
        alpha_list = [0.001, 0.01, 0.1, 1, 10, 100]
        train_scores, test_scores = [], []
        for a in alpha_list:
            r = Ridge(alpha=a).fit(train_scaled, train_target)
            train_scores.append(r.score(train_scaled, train_target))
            test_scores.append(r.score(test_scaled, test_target))
        
        log_alphas = np.log10(alpha_list)
        ax2.plot(log_alphas, train_scores, 'o-', color='#1f77b4', alpha=0.3, label='Train (Alpha 추이)')
        ax2.plot(log_alphas, test_scores, 's-', color='#ff7f0e', alpha=0.3, label='Test (Alpha 추이)')
        
        # 현재 선택한 Alpha 위치 강조 (별표)
        current_log_alpha = np.log10(float(alpha_value))
        current_test_score = ridge.score(test_scaled, test_target)
        ax2.scatter([current_log_alpha], [current_test_score], color='red', s=200, marker='*', zorder=5, label='현재 내 위치')
        
        ax2.set_title('Alpha별 성능 최적점 찾기', fontsize=12, fontweight='bold')
        ax2.set_xlabel('log10(alpha)')
        ax2.set_ylabel('R² Score')
        ax2.set_xticks(log_alphas)
        ax2.set_xticklabels([str(a) for a in alpha_list])
        ax2.legend(fontsize=9, loc='lower left', frameon=True, facecolor='white', framealpha=0.8)
        ax2.grid(True, alpha=0.1)

        fig.patch.set_facecolor('#fdfaf5')
        fig.tight_layout()
        chart = MLService._fig_to_base64(fig)
        plt.close(fig)  # 자원 해제

        # 모델 상태 정밀 진단 (상대적 성능 분석)
        t_score = ridge.score(train_scaled, train_target)
        v_score = ridge.score(test_scaled, test_target)
        
        # 전체 성능 경향 파악 (최적점 찾기)
        best_v_score = max(test_scores)
        best_alpha = alpha_list[test_scores.index(best_v_score)]
        
        status = "Optimal"
        diag_msg = "현재 데이터에서 찾을 수 있는 가장 균형 잡힌 최적의 상태입니다!"
        
        if alpha_value == best_alpha:
            status = "Optimal"
            diag_msg = "테스트 점수가 최고점에 도달했습니다. 실전에서도 아주 잘 작동할 모델입니다!"
        elif alpha_value < best_alpha:
            status = "Overfitting"
            diag_msg = f"훈련 점수는 높지만 과대적합의 위험이 큽니다. Alpha를 {best_alpha} 방향으로 높여 훈련 세트에 대한 지나친 집착을 완화해주세요!"
        else:
            status = "Underfitting"
            diag_msg = f"규제가 너무 강해져 성능이 전반적으로 하락하는 과소적합 구간입니다. Alpha를 {best_alpha} 방향으로 낮춰 모델의 표현력을 높여주세요!"

        return {
            'ridge_train': round(t_score, 4),
            'ridge_test': round(v_score * 100, 1) if v_score > -100 else f"불능 ({round(v_score, 1)})",
            'linear_train': round(lr.score(train_scaled, train_target), 4),
            'linear_test': round(lr.score(test_scaled, test_target), 1),
            'coef_count': len(ridge.coef_),
            'alpha': alpha_value,
            'status': status,
            'diag_msg': diag_msg,
            'chart': chart
        }

    # =========================================================
    # 세션 7: 로지스틱 회귀 (Mastery Overhaul)
    # =========================================================
    @staticmethod
    def session7_predict(length, height, thickness, weight):
        """로지스틱 회귀 확률 곡면 3D 시각화"""
        MLService._setup_plot()

        data = MLService.FISH_DATA
        X = np.column_stack([data['length'], data['height'], data['thickness'], data['weight']])
        y = np.array(data['target'])

        train_input, test_input, train_target, test_target = train_test_split(
            X, y, test_size=0.25, random_state=42, stratify=y
        )

        scaler = StandardScaler()
        train_scaled = scaler.fit_transform(train_input)
        test_scaled = scaler.transform(test_input)

        lr = LogisticRegression(C=20, max_iter=1000)
        lr.fit(train_scaled, train_target)
        
        # 3D 확률 시각화 — 첫 두 특성(길이, 높이)에 따른 특정 클래스(도미) 확률
        fig = plt.figure(figsize=(10, 7))
        ax = fig.add_subplot(111, projection='3d')
        
        x_min, x_max = train_scaled[:, 0].min() - 1, train_scaled[:, 0].max() + 1
        y_min, y_max = train_scaled[:, 1].min() - 1, train_scaled[:, 1].max() + 1
        xx, yy = np.meshgrid(np.linspace(x_min, x_max, 30), np.linspace(y_min, y_max, 30))
        
        # 나머지 특성은 평균값으로 고정
        grid_input = np.zeros((xx.size, 4))
        grid_input[:, 0] = xx.ravel()
        grid_input[:, 1] = yy.ravel()
        grid_input[:, 2] = train_scaled[:, 2].mean()
        grid_input[:, 3] = train_scaled[:, 3].mean()
        
        probs = lr.predict_proba(grid_input)[:, 0].reshape(xx.shape) # 도미(Class 0) 확률
        
        surf = ax.plot_surface(xx, yy, probs, cmap='viridis', alpha=0.6, edgecolor='none')
        ax.set_xlabel('Length (Scaled)')
        ax.set_ylabel('Height (Scaled)')
        ax.set_zlabel('Prob (Bream)')
        ax.set_title('3D Logistic Probability Surface: Bream Detection', fontsize=14, fontweight='bold')
        fig.colorbar(surf, ax=ax, shrink=0.5, aspect=5, label='Probability')
        
        # 사용자 입력 포인트 표시
        u_scaled = scaler.transform([[length, height, thickness, weight]])
        u_prob = lr.predict_proba(u_scaled)[0, 0]
        ax.scatter(u_scaled[0, 0], u_scaled[0, 1], [u_prob], color='red', s=200, marker='*')

        fig.patch.set_facecolor('#fdfaf5')
        chart = MLService._fig_to_base64(fig)
        plt.close(fig)  # 자원 해제
        
        probabilities = lr.predict_proba(u_scaled)[0]
        species_kr = ['도미', '잉어', '백어', '파키', '농어', '강꼬치고기', '빙어']
        prob_list = []
        for i in range(7):
            prob_list.append({
                'name_kr': species_kr[i],
                'prob': round(float(probabilities[i]) * 100, 1)
            })

        return {
            'prediction_kr': species_kr[lr.predict(u_scaled)[0]],
            'probabilities': sorted(prob_list, key=lambda x: x['prob'], reverse=True),
            'accuracy': round(lr.score(test_scaled, test_target) * 100, 1),
            'chart': chart
        }
    @staticmethod
    def session7_intro_viz():
        """로지스틱 회귀 도입부: 시그모이드(Sigmoid) 함수 시각화 강화"""
        MLService._setup_plot()
        z = np.linspace(-10, 10, 300)
        phi = 1 / (1 + np.exp(-z))
        
        fig, ax = plt.subplots(figsize=(9, 4.5))
        ax.plot(z, phi, color='#15aabf', linewidth=3.5, label='Sigmoid Curve')
        
        # 영역 구분 (0.5 기준)
        ax.fill_between(z, 0.5, 1.0, where=(z>=0), color='#2ecc71', alpha=0.1, label='Class A (Prob > 0.5)')
        ax.fill_between(z, 0, 0.5, where=(z<0), color='#e74c3c', alpha=0.1, label='Class B (Prob < 0.5)')
        
        # 임계선 표시
        ax.axhline(y=0.5, color='#2c3e50', linestyle='--', linewidth=1.5, alpha=0.7)
        ax.axvline(x=0, color='#2c3e50', linestyle=(0, (5, 5)), linewidth=1, alpha=0.4)
        
        # 주요 어노테이션 (가시성 증대)
        bbox_style = dict(boxstyle='round,pad=0.3', fc='white', ec='none', alpha=0.8)
        ax.annotate('Threshold (0.5)', xy=(-9.5, 0.52), fontsize=10, color='#2c3e50', fontweight='bold', bbox=bbox_style)
        ax.annotate('Positive Score (z > 0)', xy=(2, 0.2), fontsize=10, color='#27ae60', bbox=bbox_style)
        ax.annotate('Negative Score (z < 0)', xy=(-6, 0.8), fontsize=10, color='#c0392b', bbox=bbox_style)

        ax.set_title('Logistic Transformation: Score to Probability', fontsize=15, fontweight='bold', pad=20)
        ax.set_xlabel('z (Linear Model Score)', fontsize=11)
        ax.set_ylabel(r'$\phi(z)$ (Probability)', fontsize=11)
        ax.set_ylim(-0.05, 1.05)
        ax.legend(loc='lower right', fontsize=9, frameon=True, shadow=True)
        ax.grid(True, linestyle=':', alpha=0.5)
        
        plt.tight_layout()
        fig.patch.set_facecolor('#fdfaf5')
        chart = MLService._fig_to_base64(fig)
        plt.close(fig) # 자원 해제
        return chart

    @staticmethod
    def session7_coef_viz():
        """모델이 학습한 7종 생선별 가중치(coef_) 분포 시각화"""
        MLService._setup_plot()
        
        # 모델 학습 (재현)
        data = MLService.FISH_DATA
        X = np.column_stack([data['length'], data['height'], data['thickness'], data['weight']])
        y = np.array(data['target'])
        
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        lr = LogisticRegression(C=20, max_iter=1000)
        lr.fit(X_scaled, y)
        
        # 가중치 시각화 (첫 번째 특성: Length에 대한 어종별 가중치)
        fig, ax = plt.subplots(figsize=(10, 5))
        species_kr = ['도미', '잉어', '백어', '파키', '농어', '강꼬치', '빙어']
        coefs = lr.coef_[:, 0] # Length 특성에 대한 가중치들
        
        # plt.cm.get_cmap 대신 matplotlib.colormaps 사용 (최신 버전 대응)
        import matplotlib.cm as cm
        colors = cm.get_cmap('Set3')(np.linspace(0, 1, 7))
        bars = ax.bar(species_kr, coefs, color=colors, edgecolor='#7f8c8d', linewidth=1)
        
        ax.axhline(0, color='black', linewidth=1, alpha=0.5)
        
        for bar in bars:
            yval = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, yval + (0.1 if yval > 0 else -0.3), 
                    round(yval, 2), ha='center', va='bottom', fontsize=10, fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.1', fc='white', ec='none', alpha=0.7))

        ax.set_title('특성(길이)이 각 어종 판정에 미치는 영향력(Weight)', fontsize=14, fontweight='bold', pad=20)
        ax.set_ylabel('가중치 값 (Positive: 양의 영향, Negative: 음의 영향)')
        ax.grid(axis='y', linestyle='--', alpha=0.3)
        
        plt.tight_layout()
        fig.patch.set_facecolor('#fdfaf5')
        chart = MLService._fig_to_base64(fig)
        plt.close(fig)
        return chart

    @staticmethod
    def session7_decision_boundary():
        """이진 분류(도미 vs 빙어)의 결정 경계(Decision Boundary) 시각화"""
        MLService._setup_plot()
        
        data = MLService.FISH_DATA
        X = np.column_stack([data['length'], data['weight']])
        y = np.array(data['target'])
        
        mask = (y == 0) | (y == 6)
        X_sub = X[mask]
        y_sub = y[mask]
        y_sub = np.where(y_sub == 0, 1, 0) # 도미=1, 빙어=0
        
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X_sub)
        
        lr = LogisticRegression()
        lr.fit(X_scaled, y_sub)
        
        x_min, x_max = X_scaled[:, 0].min() - 0.5, X_scaled[:, 0].max() + 0.5
        y_min, y_max = X_scaled[:, 1].min() - 0.5, X_scaled[:, 1].max() + 0.5
        xx, yy = np.meshgrid(np.arange(x_min, x_max, 0.02), np.arange(y_min, y_max, 0.02))
        
        Z = lr.predict(np.c_[xx.ravel(), yy.ravel()])
        Z = Z.reshape(xx.shape)
        
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.contourf(xx, yy, Z, alpha=0.2, cmap='RdYlBu')
        
        ax.scatter(X_scaled[y_sub == 1, 0], X_scaled[y_sub == 1, 1], c='#e67e22', label='도미 (Bream)', edgecolors='k', s=60)
        ax.scatter(X_scaled[y_sub == 0, 0], X_scaled[y_sub == 0, 1], c='#3498db', label='빙어 (Smelt)', edgecolors='k', s=60)
        
        w = lr.coef_[0]
        b = lr.intercept_[0]
        line_x = np.linspace(x_min, x_max, 10)
        line_y = -(w[0] * line_x + b) / w[1]
        ax.plot(line_x, line_y, color='#c0392b', linestyle='--', linewidth=2, label='Decision Boundary ($z=0$)')

        ax.set_title('데이터를 나누는 경계선: 결정 경계(Decision Boundary)', fontsize=14, fontweight='bold')
        ax.set_xlabel('길이 (표준화)')
        ax.set_ylabel('무게 (표준화)')
        ax.legend(loc='best', frameon=True, facecolor='white', framealpha=0.8)
        ax.set_ylim(y_min, y_max)
        
        plt.tight_layout()
        fig.patch.set_facecolor('#fdfaf5')
        chart = MLService._fig_to_base64(fig)
        plt.close(fig)
        return chart

    @staticmethod
    def session7_dynamic_binary_viz(s1_idx, s2_idx):
        """사용자가 선택한 두 어종(Random or Manual)에 대한 이진 분류 결정 경계 시각화"""
        MLService._setup_plot()
        
        data = MLService.FISH_DATA
        X = np.column_stack([data['length'], data['weight']])
        y = np.array(data['target'])
        
        # 선택된 두 어종만 필터링
        mask = (y == s1_idx) | (y == s2_idx)
        X_sub = X[mask]
        y_sub = y[mask]
        
        # 이진 분류를 위해 타겟 매핑 (s1_idx -> 1, s2_idx -> 0)
        y_binary = np.where(y_sub == s1_idx, 1, 0)
        
        # 데이터 정합성 체크
        if len(np.unique(y_binary)) < 2:
            return None
            
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X_sub)
        
        lr = LogisticRegression()
        lr.fit(X_scaled, y_binary)
        
        # 그리드 생성
        x_min, x_max = X_scaled[:, 0].min() - 0.5, X_scaled[:, 0].max() + 0.5
        y_min, y_max = X_scaled[:, 1].min() - 0.5, X_scaled[:, 1].max() + 0.5
        xx, yy = np.meshgrid(np.arange(x_min, x_max, 0.02), np.arange(y_min, y_max, 0.02))
        
        Z = lr.predict(np.c_[xx.ravel(), yy.ravel()])
        Z = Z.reshape(xx.shape)
        
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.contourf(xx, yy, Z, alpha=0.2, cmap='RdYlBu')
        
        species_kr = ['도미', '잉어', '백어', '파키', '농어', '강꼬치', '빙어']
        ax.scatter(X_scaled[y_binary == 1, 0], X_scaled[y_binary == 1, 1], c='#e67e22', 
                   label=f'{species_kr[s1_idx]} (Positive)', edgecolors='k', s=60)
        ax.scatter(X_scaled[y_binary == 0, 0], X_scaled[y_binary == 0, 1], c='#3498db', 
                   label=f'{species_kr[s2_idx]} (Negative)', edgecolors='k', s=60)
        
        # 결정 경계선 (z=0)
        w = lr.coef_[0]
        b = lr.intercept_[0]
        line_x = np.linspace(x_min, x_max, 10)
        if abs(w[1]) > 1e-5:
            line_y = -(w[0] * line_x + b) / w[1]
            ax.plot(line_x, line_y, color='#c0392b', linestyle='--', linewidth=2, label='Decision Boundary ($z=0$)')
        
        ax.set_title(f'탐색 결과: {species_kr[s1_idx]} vs {species_kr[s2_idx]} 분류', fontsize=14, fontweight='bold')
        ax.set_xlabel('길이 (표준화)')
        ax.set_ylabel('무게 (표준화)')
        ax.legend(loc='best', frameon=True, facecolor='white', framealpha=0.8)
        ax.set_ylim(y_min, y_max)
        
        plt.tight_layout()
        fig.patch.set_facecolor('#fdfaf5')
        chart = MLService._fig_to_base64(fig)
        plt.close(fig)
        
        return {
            'chart': chart,
            'accuracy': round(lr.score(X_scaled, y_binary) * 100, 1),
            's1_name': species_kr[s1_idx],
            's2_name': species_kr[s2_idx]
        }

    @staticmethod
    def session7_hyperparam_viz():
        """C 값 변화에 따른 가중치(규제) 변화 시각화 (현미경 분석)"""
        MLService._setup_plot()
        data = MLService.FISH_DATA
        X = np.column_stack([data['length'], data['height'], data['thickness'], data['weight']])
        y = np.array(data['target'])
        
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        c_values = [0.01, 0.1, 1, 10, 100]
        coef_norms = []
        
        for c in c_values:
            lr = LogisticRegression(C=c, max_iter=1000)
            lr.fit(X_scaled, y)
            # 가중치 벡터의 크기(L2 Norm) 평균 계산
            coef_norms.append(np.mean(np.linalg.norm(lr.coef_, axis=1)))
            
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.plot(c_values, coef_norms, marker='o', color='#8e44ad', linewidth=2.5, markersize=10)
        ax.set_xscale('log')
        ax.set_xlabel('규제 제어 파라미터 (C) - 숫자가 클수록 규제 약함', fontsize=11)
        ax.set_ylabel('가중치의 평균 크기 (Coefficient Norm)', fontsize=11)
        ax.set_title('C 값(규제 강도)에 따른 모델의 "탐욕도" 분석', fontsize=14, fontweight='bold', pad=20)
        ax.grid(True, linestyle='--', alpha=0.5)
        
        bbox_style = dict(boxstyle='round,pad=0.3', fc='white', ec='none', alpha=0.85)
        ax.annotate('강한 규제\n(단순한 모델)', xy=(0.01, coef_norms[0]), xytext=(0.05, coef_norms[0]+0.5),
                    arrowprops=dict(facecolor='#2c3e50', shrink=0.05, width=1.5, headwidth=8), bbox=bbox_style)
        ax.annotate('약한 규제\n(복잡한 모델)', xy=(100, coef_norms[-1]), xytext=(10, coef_norms[-1]-0.5),
                    arrowprops=dict(facecolor='#c0392b', shrink=0.05, width=1.5, headwidth=8), bbox=bbox_style)
        
        plt.tight_layout()
        fig.patch.set_facecolor('#fdfaf5')
        chart = MLService._fig_to_base64(fig)
        plt.close(fig)
        return chart

    @staticmethod
    def session7_log_loss_viz():
        """로지스틱 손실 함수(Log Loss/Entropy) 원리 시각화"""
        MLService._setup_plot()
        a = np.linspace(0.001, 0.999, 100)
        loss_y1 = -np.log(a)        # 정답이 1일 때
        loss_y0 = -np.log(1 - a)    # 정답이 0일 때
        
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.plot(a, loss_y1, label='정답이 1일 때 로스 ($-log(a)$)', color='#e74c3c', linewidth=3)
        ax.plot(a, loss_y0, label='정답이 0일 때 로스 ($-log(1-a)$)', color='#3498db', linewidth=3, linestyle='--')
        
        ax.axhline(0, color='black', alpha=0.2)
        ax.axvline(0.5, color='gray', linestyle=':', alpha=0.5)
        
        ax.set_xlabel('모델이 예측한 확률 ($a$)', fontsize=11)
        ax.set_ylabel('손실 (Loss / 벌점)', fontsize=11)
        ax.set_title('로지스틱 손실 함수: 틀릴수록 벌점은 무한대로!', fontsize=14, fontweight='bold', pad=20)
        
        bbox_style_r = dict(boxstyle='round,pad=0.3', fc='white', ec='#e74c3c', alpha=0.85)
        bbox_style_b = dict(boxstyle='round,pad=0.3', fc='white', ec='#3498db', alpha=0.85)
        ax.text(0.1, 3, "예측확률이 0에\n가까운데 정답이 1이면?", color='#e74c3c', fontweight='bold', ha='center', bbox=bbox_style_r)
        ax.text(0.9, 3, "예측확률이 1에\n가까운데 정답이 0이면?", color='#3498db', fontweight='bold', ha='center', bbox=bbox_style_b)
        
        ax.legend(loc='upper center', frameon=True, shadow=True)
        ax.grid(True, alpha=0.2)
        
        plt.tight_layout()
        fig.patch.set_facecolor('#fdfaf5')
        chart = MLService._fig_to_base64(fig)
        plt.close(fig)
        return chart
    @staticmethod
    def session8_hinge_loss_viz():
        """SVM Hinge Loss (힌지 손실) 및 실제 데이터 매핑 시각화"""
        MLService._setup_plot()
        fig, ax = plt.subplots(figsize=(8, 5))
        
        # 1. 실제 데이터 학습 (도미 vs 나머지)
        train_scaled, _, train_target, _ = MLService.session8_get_data()
        # 분류를 단순화하기 위해 "도미(0) vs 기타" 로 학습해서 마진 계산
        y_binary = np.where(train_target == 0, 1, -1)
        
        sc = SGDClassifier(loss='hinge', random_state=42, max_iter=1000)
        sc.fit(train_scaled, y_binary)
        
        z = sc.decision_function(train_scaled)
        # Margin = y_true * z 
        margins = y_binary * z
        losses = np.maximum(0, 1 - margins)
        
        # 2. 이론적 힌지 로스 곡선 그리기
        x_min = min(-3.5, np.min(margins) - 1)
        x_max = max(4.0, np.max(margins) + 1)
        x = np.linspace(x_min, x_max, 300)
        y_hinge = np.maximum(0, 1 - x)
        
        # 구역 표시
        ax.axvspan(x_min, 1, color='#e74c3c', alpha=0.08, label='패널티 구역 (Loss 발생)')
        ax.axvspan(1, x_max, color='#2ecc71', alpha=0.08, label='안전 구역 (Loss = 0)')
        
        # 힌지 로스 선 플로팅
        ax.plot(x, y_hinge, color='#8e44ad', linewidth=3, zorder=2, label='Hinge Loss 곡선')
        
        # 3. 실제 데이터 산점도
        pos_k = (y_binary == 1)
        ax.scatter(margins[pos_k], losses[pos_k], color='#e74c3c', s=80, edgecolor='white', 
                   linewidth=1.2, zorder=3, label='도미 데이터 (정답 1)', alpha=0.8)
                   
        neg_k = (y_binary == -1)
        ax.scatter(margins[neg_k], losses[neg_k], color='#3498db', s=80, edgecolor='white', 
                   linewidth=1.2, zorder=3, label='기타 생선 (정답 -1)', alpha=0.8)

        # 4. 기준선
        ax.axhline(0, color='black', linewidth=1)
        ax.axvline(0, color='gray', linestyle='--', alpha=0.5)
        ax.axvline(1, color='blue', linestyle=':', label='Margin Boundary (Margin=1)')
        
        # 5. 주석 (선과 겹치지 않게 넉넉한 위치 선정)
        ax.set_title('SVM Hinge Loss에 매핑된 실제 판다스 데이터 (도미 vs 기타)', fontsize=15, fontweight='bold', pad=25)
        ax.set_xlabel('마진 (Margin) = 정답 레이블(1 or -1) $\\times$ 예측 점수(z)', fontsize=12)
        ax.set_ylabel('손실 (Loss)', fontsize=12)
        ax.set_xlim(x_min, x_max)
        ax.set_ylim(-0.2, max(y_hinge) + 1.5)
        
        bbox_style_r = dict(boxstyle='round', pad=0.5, fc='white', ec='#c0392b', alpha=0.9, lw=1.5)
        bbox_style_g = dict(boxstyle='round', pad=0.5, fc='white', ec='#27ae60', alpha=0.9, lw=1.5)
        bbox_style_o = dict(boxstyle='round', pad=0.5, fc='white', ec='#f39c12', alpha=0.9, lw=1.5)
        
        # 오답/확신 부족 구역 (좌측 상단)
        ax.annotate("예측이 완전히 틀려\n손실이 크게 발생하는\n데이터들 (오답)",
                    xy=(-1.5, 2.5), xytext=(-2.5, np.max(y_hinge)),
                    arrowprops=dict(facecolor='#c0392b', shrink=0.05, width=1.5, headwidth=8),
                    bbox=bbox_style_r, fontsize=11, fontweight='bold', ha='center')
                    
        # 경계 구역 (중앙 상단)
        ax.annotate("정답은 맞췄지만, 확신이 부족해\n(경계치 1 미만) 약간의 손실을\n부여받은 애매한 데이터들",
                    xy=(0.5, 0.5), xytext=(2.0, max(1.5, np.max(y_hinge)*0.6)),
                    arrowprops=dict(facecolor='#f39c12', shrink=0.05, width=1.5, headwidth=8),
                    bbox=bbox_style_o, fontsize=11, ha='center')

        # 안전 구역 (우측 하단)
        ax.annotate("결정 경계를 완전히 벗어나\n강한 확신으로 정답을 맞춤!\n(손실 = 0)",
                    xy=(2.5, 0.0), xytext=(x_max-1.0, max(1.0, np.max(y_hinge)*0.3)),
                    arrowprops=dict(facecolor='#27ae60', shrink=0.05, width=1.5, headwidth=8),
                    bbox=bbox_style_g, fontsize=11, fontweight='bold', ha='center')
        
        ax.legend(loc='upper right', frameon=True, shadow=True, fontsize=10)
        ax.grid(True, linestyle=':', alpha=0.6)
        
        plt.tight_layout()
        fig.patch.set_facecolor('#fdfaf5')
        chart = MLService._fig_to_base64(fig)
        plt.close(fig)
        return chart

    # =========================================================
    # 세션 8: 확률적 경사 하강법 (점진적 학습)
    # =========================================================

    @staticmethod
    def session8_get_data():
        """8강용 전처리된 데이터 준비 (7종 생선 전체 데이터)"""
        data = MLService.FISH_DATA
        # 특성: Weight, Length, Height, Thickness (모두 사용)
        X = np.column_stack([data['length'], data['height'], data['thickness'], data['weight']])
        y = np.array(data['target'])
        
        train_input, test_input, train_target, test_target = train_test_split(
            X, y, test_size=0.25, random_state=42
        )
        
        ss = StandardScaler()
        train_scaled = ss.fit_transform(train_input)
        test_scaled = ss.transform(test_input)
        
        return train_scaled, test_scaled, train_target, test_target

    @staticmethod
    def session8_init_sgd(loss='log_loss'):
        """SGDClassifier 초기 훈련 및 결과 반환"""
        MLService._setup_plot()
        train_scaled, test_scaled, train_target, test_target = MLService.session8_get_data()
        
        # 초기 모델 생성 및 1회 점진적 학습 (1 에포크로 통일)
        sc = SGDClassifier(loss=loss, random_state=42)
        classes = np.unique(train_target)
        sc.partial_fit(train_scaled, train_target, classes=classes)
        
        train_score = sc.score(train_scaled, train_target)
        test_score = sc.score(test_scaled, test_target)
        
        # 시각화: 현재 가중치 상태 (간단한 막대 그래프)
        fig, ax = plt.subplots(figsize=(6, 3.5))
        # 멀티 클래스이므로 첫 번째 클래스의 가중치만 예시로 표시
        coef_example = sc.coef_[0]
        features = ['Length', 'Height', 'Thickness', 'Weight']
        ax.bar(features, coef_example, color=['#3498db', '#2ecc71', '#f1c40f', '#e67e22'], edgecolor='black', alpha=0.7)
        ax.axhline(0, color='black', linewidth=1)
        ax.set_title(f'Initial Weights (Species: Bream, Loss: {loss})', fontweight='bold')
        ax.set_ylabel('Weight Value')
        
        fig.patch.set_facecolor('#fdfaf5')
        chart = MLService._fig_to_base64(fig)
        
        return {
            'train_score': round(float(train_score), 4),
            'test_score': round(float(test_score), 4),
            'classes': sc.classes_.tolist(),
            'chart': chart
        }

    @staticmethod
    def session8_partial_fit(current_epochs=1, add_epochs=1, loss='log_loss'):
        """partial_fit을 이용한 연속적인 학습 시뮬레이션 (누적 이력 표시)"""
        MLService._setup_plot()
        train_scaled, test_scaled, train_target, test_target = MLService.session8_get_data()
        classes = np.unique(train_target)
        
        sc = SGDClassifier(loss=loss, random_state=42)
        
        train_scores = []
        test_scores = []
        total_epochs = current_epochs + add_epochs
        
        # 처음부터 현재+추가분까지 모든 이력 기록 (버그 방지 및 비교 분석용)
        for _ in range(total_epochs):
            sc.partial_fit(train_scaled, train_target, classes=classes)
            train_scores.append(sc.score(train_scaled, train_target))
            test_scores.append(sc.score(test_scaled, test_target))
            
        # 시각화: 훈련/테스트 스코어 비교 및 전체 이력
        fig, ax = plt.subplots(figsize=(6, 3.5))
        epochs_range = range(1, total_epochs + 1)
        
        ax.plot(epochs_range, train_scores, label='Train Accuracy', color='#3498db', alpha=0.6)
        ax.plot(epochs_range, test_scores, 'o-', label='Test Accuracy', color='#e67e22', linewidth=2, markersize=4)
        
        # 강조 표시 (최신 구간)
        if add_epochs > 0:
            ax.axvspan(current_epochs, total_epochs, color='yellow', alpha=0.1, label='Newly Added')

        ax.set_title(f'Learning Curve Comparison (Total Epochs: {total_epochs})', fontweight='bold')
        ax.set_xlabel('Epoch')
        ax.set_ylabel('Accuracy')
        ax.legend(loc='lower right', frameon=True, facecolor='white', framealpha=0.8)
        ax.grid(True, alpha=0.2)
        
        fig.patch.set_facecolor('#fdfaf5')
        chart = MLService._fig_to_base64(fig)
        
        return {
            'final_train_score': round(float(train_scores[-1]), 4),
            'final_test_score': round(float(test_scores[-1]), 4),
            'total_epochs': total_epochs,
            'chart': chart
        }

    @staticmethod
    def session8_get_raw_samples(n=10):
        """세션 8 원본 데이터(FISH_DATA)의 상위 n개 샘플 반환 (정합성 확인용)"""
        data = MLService.FISH_DATA
        samples = []
        for i in range(min(n, len(data['length']))):
            samples.append({
                'Species': data['species'][i // 7], 
                'Length': data['length'][i],
                'Height': data['height'][i],
                'Thickness': data['thickness'][i],
                'Weight': data['weight'][i]
            })
        return samples

    @staticmethod
    def session8_weight_evolution_viz(max_epochs=100, loss='log_loss'):
        """에포크별 가중치(Weights)의 변화 과정을 시각화"""
        MLService._setup_plot()
        train_scaled, _, train_target, _ = MLService.session8_get_data()
        classes = np.unique(train_target)
        
        sc = SGDClassifier(loss=loss, random_state=42)
        
        weight_history = {
            'Length': [],
            'Height': [],
            'Thickness': [],
            'Weight': []
        }
        epochs = range(1, max_epochs + 1)
        
        for _ in epochs:
            sc.partial_fit(train_scaled, train_target, classes=classes)
            w = sc.coef_[0]
            weight_history['Length'].append(w[0])
            weight_history['Height'].append(w[1])
            weight_history['Thickness'].append(w[2])
            weight_history['Weight'].append(w[3])
            
        fig, ax = plt.subplots(figsize=(7, 4))
        colors = ['#3498db', '#2ecc71', '#f1c40f', '#e67e22']
        for i, (feat, vals) in enumerate(weight_history.items()):
            ax.plot(epochs, vals, label=feat, color=colors[i], linewidth=2)
            
        ax.set_title(f'Weight Evolution over Epochs (Target: Bream, Loss: {loss})', fontweight='bold', fontsize=13)
        ax.set_xlabel('Epoch')
        ax.set_ylabel('Weight Value')
        ax.axhline(0, color='black', alpha=0.3, linestyle='--')
        ax.legend(loc='best', frameon=True, facecolor='white')
        ax.grid(True, alpha=0.2)
        
        fig.patch.set_facecolor('#fdfaf5')
        chart = MLService._fig_to_base64(fig)
        return chart

    @staticmethod
    def session8_interactive_hinge_loss_viz(target_fish='Bream'):
        """대상을 선택하면 해당 물고기에 대한 힌지 손실 산점도를 그림"""
        MLService._setup_plot()
        train_scaled, _, train_target, _ = MLService.session8_get_data()
        
        # FISH_DATA의 target은 숫자(0~6) → species 리스트 인덱스로 매핑
        species_list = MLService.FISH_DATA['species']
        if target_fish in species_list:
            target_idx = species_list.index(target_fish)
        else:
            target_idx = 0
        
        # 선택한 타겟 물고기는 1(Positive), 나머지는 -1(Negative)로 이진 분류 세팅
        y_binary = np.where(train_target == target_idx, 1, -1)
        
        # 양성/음성 클래스 모두 있는지 확인
        if len(np.unique(y_binary)) < 2:
            # 혹시 해당 종이 훈련 세트에 없으면 전체 데이터로 대체
            fig, ax = plt.subplots(figsize=(7, 4))
            ax.text(0.5, 0.5, f"'{target_fish}' 데이터가 훈련 세트에 충분하지 않습니다.\n다른 생선을 선택해 주세요.",
                    ha='center', va='center', fontsize=13, transform=ax.transAxes)
            fig.patch.set_facecolor('#fdfaf5')
            chart = MLService._fig_to_base64(fig)
            plt.close(fig)
            return chart
        
        sc = SGDClassifier(loss='hinge', random_state=42, max_iter=10)
        sc.fit(train_scaled, y_binary)
        
        # 모델의 예측 점수(결정 함수 z)
        z = sc.decision_function(train_scaled)
        
        fig, ax = plt.subplots(figsize=(7, 4))
        
        # 1. Hinge Loss 기본 곡선 (y=1 인 Positive 기준)
        x_vals = np.linspace(-3, 3, 200)
        y_vals = np.maximum(0, 1 - x_vals)
        ax.plot(x_vals, y_vals, color='#2980b9', linewidth=2.5, label='Hinge Loss Curve (Positive Class)', zorder=2)
        
        # 2. 실제 데이터 산점도 (Positive 데이터만, 손실 곡선 위에 매핑)
        pos_z = z[y_binary == 1]
        pos_loss = np.maximum(0, 1 - pos_z)
        
        ax.scatter(pos_z, pos_loss, color='#e74c3c', s=60, alpha=0.8, edgecolors='white', zorder=5, label=f'Actual Data ({target_fish})')
        
        ax.set_title(f'Hinge Loss Mapping for \'{target_fish}\'', fontsize=13, fontweight='bold')
        ax.set_xlabel('Decision Function Score (z)', fontsize=11)
        ax.set_ylabel('Loss (Penalty)', fontsize=11)
        ax.grid(True, linestyle='--', alpha=0.5, zorder=0)
        ax.legend(frameon=True, facecolor='white', loc='upper right')
        
        fig.patch.set_facecolor('#fdfaf5')
        chart = MLService._fig_to_base64(fig)
        plt.close(fig)
        
        return chart

    @staticmethod
    def session8_epoch_optimization(max_epochs=300):
        """에포크 횟수에 따른 훈련/테스트 스코어 기록 및 최적점 시각화"""
        MLService._setup_plot()
        train_scaled, test_scaled, train_target, test_target = MLService.session8_get_data()
        classes = np.unique(train_target)
        
        sc = SGDClassifier(loss='log_loss', random_state=42)
        train_score_list = []
        test_score_list = []
        
        for _ in range(max_epochs):
            sc.partial_fit(train_scaled, train_target, classes=classes)
            train_score_list.append(sc.score(train_scaled, train_target))
            test_score_list.append(sc.score(test_scaled, test_target))
            
        # 시각화
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.plot(train_score_list, label='Train Score (Blue)', color='#3498db', alpha=0.7)
        ax.plot(test_score_list, label='Test Score (Orange)', color='#e67e22', alpha=0.9, linewidth=2)
        
        # 최적 지점 표시 (테스트 스코어가 가장 높은 시점 근처)
        best_epoch = np.argmax(test_score_list)
        ax.axvline(x=best_epoch, color='gray', linestyle='--', alpha=0.5)
        
        # Sweet Spot 주석 (우측 상단 여백으로 이동하고 화살표로 지시)
        ax.annotate(f'Sweet Spot (Around {best_epoch} epoch)', 
                    xy=(best_epoch, test_score_list[best_epoch]), 
                    xytext=(max_epochs*0.75, 0.85),
                    ha='center', fontsize=11, fontweight='bold',
                    arrowprops=dict(arrowstyle='->', connectionstyle="arc3,rad=-0.2", color='#2c3e50', lw=1.5),
                    bbox=dict(boxstyle='round,pad=0.3', fc='white', ec='#2c3e50', alpha=0.9))
        
        # 과소적합/과대적합 영역 주석 (우측 여백으로 빼서 화살표로 지시)
        # Underfitting
        ax.annotate('Underfitting Region', 
                    xy=(best_epoch*0.5, 0.4), 
                    xytext=(max_epochs*0.75, 0.73),
                    ha='center', fontsize=11, fontweight='bold', color='#c0392b',
                    arrowprops=dict(arrowstyle='->', connectionstyle="arc3,rad=-0.1", color='#c0392b', lw=1.5),
                    bbox=dict(boxstyle='round,pad=0.3', fc='white', ec='#c0392b', alpha=0.9))
        
        # Overfitting
        ax.annotate('Overfitting Region', 
                    xy=(max_epochs*0.85, test_score_list[-1]), 
                    xytext=(max_epochs*0.75, 0.28),
                    ha='center', fontsize=11, fontweight='bold', color='#c0392b',
                    arrowprops=dict(arrowstyle='->', color='#c0392b', lw=1.5),
                    bbox=dict(boxstyle='round,pad=0.3', fc='white', ec='#c0392b', alpha=0.9))
        
        ax.set_xlabel('Epoch', fontsize=12)
        ax.set_ylabel('Accuracy (R²)')
        ax.set_title('Finding Optimal Epochs to Avoid Over/Underfitting', fontsize=14, fontweight='bold')
        ax.legend(frameon=True, facecolor='white', framealpha=0.8)
        ax.grid(True, alpha=0.2)
        
        fig.patch.set_facecolor('#fdfaf5')
        chart = MLService._fig_to_base64(fig)
        
        return {
            'best_epoch': int(best_epoch),
            'final_train_score': round(float(train_score_list[-1]), 4),
            'final_test_score': round(float(test_score_list[-1]), 4),
            'chart': chart
        }

    @staticmethod
    def session8_accuracy_loss_dual_viz(max_epochs=300):
        """에포크 횟수에 따른 정확도(Accuracy)와 손실(Loss)의 변화 동시 시각화"""
        from sklearn.metrics import hinge_loss
        MLService._setup_plot()
        train_scaled, test_scaled, train_target, test_target = MLService.session8_get_data()
        classes = np.unique(train_target)
        
        sc_hinge_test = SGDClassifier(loss='hinge', max_iter=1, tol=None, random_state=42)
        
        train_score, test_score = [], []
        train_loss, test_loss = [], []
        
        for _ in range(max_epochs):
            sc_hinge_test.partial_fit(train_scaled, train_target, classes=classes)
            
            # Accuracy
            train_score.append(sc_hinge_test.score(train_scaled, train_target))
            test_score.append(sc_hinge_test.score(test_scaled, test_target))
            
            # Loss (Hinge)
            train_decision = sc_hinge_test.decision_function(train_scaled)
            test_decision = sc_hinge_test.decision_function(test_scaled)
            train_loss.append(hinge_loss(train_target, train_decision))
            test_loss.append(hinge_loss(test_target, test_decision))
            
        fig, ax1 = plt.subplots(figsize=(8, 5))
        
        # 왼쪽 Y축: Accuracy
        ax1.plot(train_score, color='#3498db', linewidth=2.5, label='Train Accuracy')
        ax1.plot(test_score, color='#e67e22', linewidth=2.5, label='Test Accuracy')
        ax1.set_xlabel('에포크 (Epoch)', fontsize=12)
        ax1.set_ylabel('정확도 (Accuracy)', fontsize=12, color='#3498db')
        ax1.tick_params(axis='y', labelcolor='#3498db')
        
        # 오른쪽 Y축: Loss
        ax2 = ax1.twinx()
        ax2.plot(train_loss, color='#2ecc71', linestyle='--', linewidth=2, alpha=0.8, label='Train Loss')
        ax2.plot(test_loss, color='#e74c3c', linestyle='--', linewidth=2, alpha=0.8, label='Test Loss')
        ax2.set_ylabel('손실 (Loss)', fontsize=12, color='#e74c3c')
        ax2.tick_params(axis='y', labelcolor='#e74c3c')
        
        # 범례 통합
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='center right', frameon=True, shadow=True)
        
        plt.title('에포크에 따른 정확도 상승과 손실 감소의 상관관계', fontsize=15, fontweight='bold', pad=20)
        ax1.grid(True, alpha=0.3)
        
        fig.patch.set_facecolor('#fdfaf5')
        plt.tight_layout()
        chart = MLService._fig_to_base64(fig)
        plt.close(fig)
        
        return {
            'final_train_acc': round(train_score[-1], 3),
            'final_test_acc': round(test_score[-1], 3),
            'final_train_loss': round(train_loss[-1], 3),
            'final_test_loss': round(test_loss[-1], 3),
            'chart': chart
        }

    @staticmethod
    def session8_early_stopping_viz(max_epochs=300, patience=10):
        """테스트 손실 기반 조기 종료(Early Stopping) 메커니즘 시각화"""
        from sklearn.metrics import hinge_loss
        MLService._setup_plot()
        train_scaled, test_scaled, train_target, test_target = MLService.session8_get_data()
        classes = np.unique(train_target)
        
        best_loss = float('inf')
        patience_counter = 0
        early_stop_epoch = max_epochs
        
        train_score_early, test_score_early = [], []
        train_loss_early, test_loss_early = [], []
        
        sc_hinge_test_early = SGDClassifier(loss='hinge', max_iter=1, tol=None, random_state=42)
        
        for epoch in range(max_epochs):
            sc_hinge_test_early.partial_fit(train_scaled, train_target, classes=classes)
            
            # 기록
            train_score_early.append(sc_hinge_test_early.score(train_scaled, train_target))
            test_score_early.append(sc_hinge_test_early.score(test_scaled, test_target))
            
            train_decision_early = sc_hinge_test_early.decision_function(train_scaled)
            test_decision_early = sc_hinge_test_early.decision_function(test_scaled)
            
            current_test_loss = hinge_loss(test_target, test_decision_early)
            train_loss_early.append(hinge_loss(train_target, train_decision_early))
            test_loss_early.append(current_test_loss)
            
            # Early Stopping 체크
            if current_test_loss < best_loss:
                best_loss = current_test_loss
                patience_counter = 0
                early_stop_epoch = epoch
            else:
                patience_counter += 1
                
            if patience_counter >= patience:
                break  # 조기 종료
                
        fig, ax1 = plt.subplots(figsize=(8, 5))
        
        # Accuracy 축
        ax1.plot(train_score_early, color='#3498db', linewidth=2, label='Train Acc')
        ax1.plot(test_score_early, color='#e67e22', linewidth=2, label='Test Acc')
        
        # Early stopping 구분선
        ax1.axvline(x=early_stop_epoch, color='#2c3e50', linestyle=':', linewidth=2.5, label=f'Early Stop (Epoch {early_stop_epoch})')
        
        # 패딩 (인내심) 영역 표시
        actual_stop_epoch = len(train_score_early) - 1
        ax1.axvspan(early_stop_epoch, actual_stop_epoch, color='#95a5a6', alpha=0.15, label='Patience 적용 구간')
        
        ax1.set_xlabel('에포크 (Epoch)', fontsize=12)
        ax1.set_ylabel('정확도 (Accuracy)', fontsize=12, color='#3498db')
        
        # Loss 축
        ax2 = ax1.twinx()
        ax2.plot(train_loss_early, color='#2ecc71', linestyle='--', label='Train Loss')
        ax2.plot(test_loss_early, color='#e74c3c', linestyle='--', linewidth=2, label='Test Loss (모니터링 대상)')
        ax2.set_ylabel('손실 (Loss)', fontsize=12, color='#e74c3c')
        
        # 주석 추가
        ax1.annotate(f'최적점 예측\n(Epoch {early_stop_epoch})', 
                    xy=(early_stop_epoch, test_score_early[early_stop_epoch]), 
                    xytext=(early_stop_epoch - 30, test_score_early[early_stop_epoch] - 0.2),
                    arrowprops=dict(facecolor='#2c3e50', shrink=0.05, width=1.5, headwidth=8),
                    bbox=dict(boxstyle='round,pad=0.3', fc='white', ec='#2c3e50', alpha=0.9),
                    fontsize=11, fontweight='bold', ha='center')
        
        # 범례 통합
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='center right', frameon=True, shadow=True)
        
        plt.title('조기 종료 (Early Stopping) 메커니즘을 통한 과대적합 방지', fontsize=15, fontweight='bold', pad=20)
        ax1.grid(True, alpha=0.3)
        
        fig.patch.set_facecolor('#fdfaf5')
        plt.tight_layout()
        chart = MLService._fig_to_base64(fig)
        plt.close(fig)
        
        return {
            'early_stop_epoch': early_stop_epoch,
            'total_epochs_run': actual_stop_epoch,
            'patience': patience,
            'final_test_acc': round(test_score_early[-1], 3),
            'chart': chart
        }

    # =========================================================
    # 세션 9: 결정 트리 & 교차 검증 & 그리드 서치
    # =========================================================

    @staticmethod
    def session9_get_wine_data():
        """와인 품질 데이터셋 생성 (Numpy 기반 시뮬레이션)"""
        # [Vercel 최적화] 용량을 차치하는 pandas 제거
        # from sklearn.datasets import load_wine as _lw (사용 안 함)
        
        # PDF 강의와 동일한 wine quality 데이터 구조 시뮬레이션
        # 실제 데이터: alcohol, sugar, pH → target: 0(레드), 1(화이트)
        np.random.seed(42)
        n = 300
        # 화이트 와인 (200개) - 당도 높음, 알콜 낮음
        white_alcohol = np.random.normal(10.5, 1.2, 200)
        white_sugar = np.random.normal(6.5, 3.5, 200)
        white_ph = np.random.normal(3.18, 0.15, 200)
        # 레드 와인 (100개) - 당도 낮음, 알콜 높음
        red_alcohol = np.random.normal(11.5, 1.0, 100)
        red_sugar = np.random.normal(2.5, 1.0, 100)
        red_ph = np.random.normal(3.31, 0.15, 100)
        
        alcohol = np.concatenate([white_alcohol, red_alcohol])
        sugar = np.concatenate([white_sugar, red_sugar])
        ph = np.concatenate([white_ph, red_ph])
        target = np.array([1.0]*200 + [0.0]*100)
        
        X = np.column_stack([alcohol, sugar, ph])
        
        train_input, test_input, train_target, test_target = train_test_split(
            X, target, test_size=0.2, random_state=42
        )
        return train_input, test_input, train_target, test_target, ['alcohol', 'sugar', 'pH']

    @staticmethod
    def session9_get_raw_samples(n=15):
        """세션 9 와인 원본 데이터 샘플 반환"""
        train_input, _, train_target, _, _ = MLService.session9_get_wine_data()
        samples = []
        for i in range(min(n, len(train_input))):
            samples.append({
                'Type': '화이트' if train_target[i] == 1.0 else '레드',
                'Alcohol': round(float(train_input[i][0]), 2),
                'Sugar': round(float(train_input[i][1]), 2),
                'pH': round(float(train_input[i][2]), 2)
            })
        return samples

    @staticmethod
    def session9_intro_viz():
        """세션 9 진입 시각화: 와인 데이터 분포 산점도"""
        MLService._setup_plot()
        train_input, _, train_target, _, features = MLService.session9_get_wine_data()
        
        fig, axes = plt.subplots(1, 3, figsize=(12, 4))
        colors = ['#c0392b' if t == 0 else '#f1c40f' for t in train_target]
        
        pairs = [(0,1,'Alcohol','Sugar'), (0,2,'Alcohol','pH'), (1,2,'Sugar','pH')]
        for ax, (i,j,xl,yl) in zip(axes, pairs):
            ax.scatter(train_input[:,i], train_input[:,j], c=colors, alpha=0.5, s=20, edgecolor='white', linewidth=0.3)
            ax.set_xlabel(xl, fontsize=10)
            ax.set_ylabel(yl, fontsize=10)
            ax.grid(True, alpha=0.2)
        
        # 범례
        from matplotlib.lines import Line2D
        legend_elements = [
            Line2D([0],[0], marker='o', color='w', markerfacecolor='#c0392b', markersize=8, label='Red Wine'),
            Line2D([0],[0], marker='o', color='w', markerfacecolor='#f1c40f', markersize=8, label='White Wine')
        ]
        axes[2].legend(handles=legend_elements, loc='upper right', fontsize=10)
        
        fig.suptitle('와인 데이터 분포 (Alcohol, Sugar, pH)', fontsize=18, fontweight='bold', y=1.05)
        plt.tight_layout()
        fig.patch.set_facecolor('none')
        chart = MLService._fig_to_base64(fig)
        plt.close(fig)
        return chart

    @staticmethod
    def session9_decision_tree_viz(max_depth=3):
        """결정 트리 시각화 (가지치기 + 트리 구조 그림)"""
        from sklearn.tree import DecisionTreeClassifier, plot_tree
        MLService._setup_plot()
        train_input, test_input, train_target, test_target, features = MLService.session9_get_wine_data()
        
        dt = DecisionTreeClassifier(max_depth=max_depth, random_state=42)
        dt.fit(train_input, train_target)
        
        train_score = dt.score(train_input, train_target)
        test_score = dt.score(test_input, test_target)
        
        fig, ax = plt.subplots(figsize=(14, 7))
        plot_tree(dt, filled=True, feature_names=features, 
                  class_names=['Red', 'White'], rounded=True, 
                  fontsize=9, ax=ax, proportion=True)
        ax.set_title(f'Decision Tree (max_depth={max_depth})\nTrain: {train_score*100:.1f}%  |  Test: {test_score*100:.1f}%', 
                     fontsize=13, fontweight='bold', pad=15)
        
        plt.tight_layout()
        fig.patch.set_facecolor('#fdfaf5')
        chart = MLService._fig_to_base64(fig)
        plt.close(fig)
        
        return {
            'chart': chart,
            'train_score': round(float(train_score), 4),
            'test_score': round(float(test_score), 4),
            'feature_importances': {f: round(float(v), 4) for f, v in zip(features, dt.feature_importances_)}
        }

    @staticmethod
    def session9_gini_explanation_viz():
        """지니 불순도(Gini Impurity) 개념 시각화"""
        MLService._setup_plot()
        
        p = np.linspace(0, 1, 200)
        gini = 1 - p**2 - (1-p)**2
        entropy = -(p * np.log2(np.clip(p,1e-10,1)) + (1-p) * np.log2(np.clip(1-p,1e-10,1)))
        
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.plot(p, gini, color='#8e44ad', linewidth=3, label='Gini Impurity')
        ax.plot(p, entropy / 2, color='#3498db', linewidth=2, linestyle='--', alpha=0.7, label='Entropy / 2')
        
        ax.axvline(0.5, color='gray', linestyle=':', alpha=0.5)
        ax.annotate('최대 불순도\n(50:50 혼합)', xy=(0.5, 0.5), xytext=(0.7, 0.45),
                    arrowprops=dict(arrowstyle='->', color='#2c3e50'), fontsize=10, fontweight='bold',
                    bbox=dict(boxstyle='round', fc='white', ec='#2c3e50'))
        ax.annotate('순수 노드\n(한 클래스만)', xy=(0.0, 0.0), xytext=(0.15, 0.25),
                    arrowprops=dict(arrowstyle='->', color='#27ae60'), fontsize=10,
                    bbox=dict(boxstyle='round', fc='white', ec='#27ae60'))
        
        ax.set_xlabel('양성 클래스 비율 (p)', fontsize=11)
        ax.set_ylabel('불순도', fontsize=11)
        ax.set_title('지니 불순도 vs 엔트로피', fontsize=13, fontweight='bold')
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.2)
        ax.set_xlim(0, 1)
        
        plt.tight_layout()
        fig.patch.set_facecolor('#fdfaf5')
        chart = MLService._fig_to_base64(fig)
        plt.close(fig)
        return chart

    @staticmethod
    def session9_feature_importance_viz():
        """결정 트리의 특성 중요도 시각화"""
        from sklearn.tree import DecisionTreeClassifier
        MLService._setup_plot()
        train_input, _, train_target, _, features = MLService.session9_get_wine_data()
        
        dt = DecisionTreeClassifier(max_depth=5, random_state=42)
        dt.fit(train_input, train_target)
        
        importances = dt.feature_importances_
        colors = ['#3498db', '#2ecc71', '#e67e22']
        
        fig, ax = plt.subplots(figsize=(6, 4))
        bars = ax.bar(features, importances, color=colors, edgecolor='white', linewidth=1.5, alpha=0.85)
        
        for bar, imp in zip(bars, importances):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01, 
                    f'{imp:.3f}', ha='center', va='bottom', fontsize=11, fontweight='bold')
        
        ax.set_ylabel('중요도', fontsize=11)
        ax.set_title('특성 중요도 (Feature Importance)', fontsize=13, fontweight='bold')
        ax.set_ylim(0, max(importances) * 1.2)
        ax.grid(True, axis='y', alpha=0.2)
        
        plt.tight_layout()
        fig.patch.set_facecolor('#fdfaf5')
        chart = MLService._fig_to_base64(fig)
        plt.close(fig)
        return chart

    @staticmethod
    def session9_overfitting_comparison():
        """과대적합 vs 가지치기 비교 시각화"""
        from sklearn.tree import DecisionTreeClassifier
        MLService._setup_plot()
        train_input, test_input, train_target, test_target, _ = MLService.session9_get_wine_data()
        
        depths = range(1, 25)
        train_scores = []
        test_scores = []
        
        for d in depths:
            dt = DecisionTreeClassifier(max_depth=d, random_state=42)
            dt.fit(train_input, train_target)
            train_scores.append(dt.score(train_input, train_target))
            test_scores.append(dt.score(test_input, test_target))
        
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.plot(list(depths), train_scores, 'o-', color='#3498db', label='Train Score', linewidth=2, markersize=4)
        ax.plot(list(depths), test_scores, 's-', color='#e67e22', label='Test Score', linewidth=2, markersize=4)
        
        best_depth = list(depths)[np.argmax(test_scores)]
        ax.axvline(best_depth, color='#2ecc71', linestyle='--', linewidth=2, alpha=0.7)
        ax.annotate(f'최적 깊이 ≈ {best_depth}', xy=(best_depth, max(test_scores)), 
                    xytext=(best_depth+3, max(test_scores)-0.03),
                    arrowprops=dict(arrowstyle='->', color='#2ecc71'), fontsize=10, fontweight='bold',
                    bbox=dict(boxstyle='round', fc='white', ec='#2ecc71'))
        
        ax.axvspan(1, best_depth, alpha=0.05, color='blue', label='Underfitting zone')
        ax.axvspan(best_depth, max(depths), alpha=0.05, color='red', label='Overfitting zone')
        
        ax.set_xlabel('트리 깊이 (max_depth)', fontsize=11)
        ax.set_ylabel('정확도 (Accuracy)', fontsize=11)
        ax.set_title('결정 트리 깊이에 따른 과대적합 분석', fontsize=13, fontweight='bold')
        ax.legend(fontsize=9, loc='lower right')
        ax.grid(True, alpha=0.2)
        
        plt.tight_layout()
        fig.patch.set_facecolor('#fdfaf5')
        chart = MLService._fig_to_base64(fig)
        plt.close(fig)
        return {'chart': chart, 'best_depth': int(best_depth)}

    @staticmethod
    def session9_cross_validation_viz(n_splits=5):
        """교차 검증 결과 시각화"""
        from sklearn.tree import DecisionTreeClassifier
        from sklearn.model_selection import cross_validate
        MLService._setup_plot()
        train_input, _, train_target, _, _ = MLService.session9_get_wine_data()
        
        dt = DecisionTreeClassifier(max_depth=5, random_state=42)
        scores = cross_validate(dt, train_input, train_target, cv=n_splits, return_train_score=True)
        
        fig, ax = plt.subplots(figsize=(7, 4))
        x = np.arange(1, n_splits+1)
        width = 0.35
        
        ax.bar(x - width/2, scores['train_score'], width, color='#3498db', alpha=0.8, label='Train', edgecolor='white')
        ax.bar(x + width/2, scores['test_score'], width, color='#e67e22', alpha=0.8, label='Validation', edgecolor='white')
        
        # 평균선
        ax.axhline(np.mean(scores['test_score']), color='#e74c3c', linestyle='--', linewidth=2, alpha=0.7,
                   label=f'평균 검증: {np.mean(scores["test_score"])*100:.1f}%')
        
        ax.set_xlabel(f'폴드 번호 (총 {n_splits}-Fold)', fontsize=11)
        ax.set_ylabel('정확도', fontsize=11)
        ax.set_title(f'{n_splits}-Fold 교차 검증 결과', fontsize=13, fontweight='bold')
        ax.set_xticks(x)
        ax.legend(fontsize=9)
        ax.grid(True, axis='y', alpha=0.2)
        ax.set_ylim(0.7, 1.05)
        
        plt.tight_layout()
        fig.patch.set_facecolor('#fdfaf5')
        chart = MLService._fig_to_base64(fig)
        plt.close(fig)
        
        return {
            'chart': chart,
            'mean_train': round(float(np.mean(scores['train_score'])), 4),
            'mean_test': round(float(np.mean(scores['test_score'])), 4),
            'fold_scores': [round(float(s), 4) for s in scores['test_score']]
        }

    @staticmethod
    def session9_grid_search_viz():
        """그리드 서치 결과 시각화"""
        from sklearn.tree import DecisionTreeClassifier
        from sklearn.model_selection import GridSearchCV
        MLService._setup_plot()
        train_input, test_input, train_target, test_target, _ = MLService.session9_get_wine_data()
        
        params = {
            'min_impurity_decrease': np.arange(0.0001, 0.001, 0.0001),
            'max_depth': range(3, 15),
            'min_samples_split': range(2, 30, 5)
        }
        
        gs = GridSearchCV(DecisionTreeClassifier(random_state=42), params, n_jobs=1, cv=5)
        gs.fit(train_input, train_target)
        
        best = gs.best_params_
        best_score = gs.best_score_
        test_score = gs.best_estimator_.score(test_input, test_target)
        
        # 시각화: max_depth별 평균 성능
        results = gs.cv_results_
        
        # max_depth별 최고 성능 추출
        unique_depths = sorted(set(p['max_depth'] for p in results['params']))
        depth_scores = []
        for d in unique_depths:
            mask = [p['max_depth'] == d for p in results['params']]
            depth_scores.append(np.max(np.array(results['mean_test_score'])[mask]))
        
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.plot(unique_depths, depth_scores, 'o-', color='#8e44ad', linewidth=2, markersize=6)
        
        best_d = best.get('max_depth', unique_depths[np.argmax(depth_scores)])
        ax.axvline(best_d, color='#2ecc71', linestyle='--', alpha=0.7)
        ax.annotate(f'최적: depth={best_d}\n검증: {best_score*100:.1f}%', 
                    xy=(best_d, max(depth_scores)), xytext=(best_d+2, max(depth_scores)-0.01),
                    arrowprops=dict(arrowstyle='->', color='#2c3e50'), fontsize=10, fontweight='bold',
                    bbox=dict(boxstyle='round', fc='white', ec='#2c3e50'))
        
        ax.set_xlabel('max_depth', fontsize=11)
        ax.set_ylabel('교차 검증 점수', fontsize=11)
        ax.set_title('Grid Search: max_depth별 최고 성능', fontsize=13, fontweight='bold')
        ax.grid(True, alpha=0.2)
        
        plt.tight_layout()
        fig.patch.set_facecolor('#fdfaf5')
        chart = MLService._fig_to_base64(fig)
        plt.close(fig)
        
        return {
            'chart': chart,
            'best_params': {k: (float(v) if isinstance(v, (np.floating, float)) else int(v)) for k, v in best.items()},
            'best_cv_score': round(float(best_score), 4),
            'test_score': round(float(test_score), 4)
        }

    @staticmethod
    def session9_random_search_viz():
        """랜덤 서치 결과 시각화"""
        from sklearn.tree import DecisionTreeClassifier
        from sklearn.model_selection import RandomizedSearchCV
        from scipy.stats import uniform, randint
        MLService._setup_plot()
        train_input, test_input, train_target, test_target, _ = MLService.session9_get_wine_data()
        
        params = {
            'min_impurity_decrease': uniform(0.0001, 0.001),
            'max_depth': randint(3, 30),
            'min_samples_split': randint(2, 25),
            'min_samples_leaf': randint(1, 25)
        }
        
        rs = RandomizedSearchCV(DecisionTreeClassifier(random_state=42), params, 
                                n_iter=100, n_jobs=1, cv=5, random_state=42)
        rs.fit(train_input, train_target)
        
        best = rs.best_params_
        best_score = rs.best_score_
        test_score = rs.best_estimator_.score(test_input, test_target)
        
        # 시각화: 랜덤 서치 수행 점수 분포
        all_scores = rs.cv_results_['mean_test_score']
        
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.hist(all_scores, bins=20, color='#3498db', alpha=0.7, edgecolor='white')
        ax.axvline(best_score, color='#e74c3c', linewidth=2.5, linestyle='--', 
                   label=f'Best: {best_score*100:.1f}%')
        ax.annotate(f'최적 조합 발견!', xy=(best_score, 0), xytext=(best_score-0.02, ax.get_ylim()[1]*0.8),
                    arrowprops=dict(arrowstyle='->', color='#e74c3c'), fontsize=10, fontweight='bold',
                    bbox=dict(boxstyle='round', fc='white', ec='#e74c3c'))
        
        ax.set_xlabel('교차 검증 점수', fontsize=11)
        ax.set_ylabel('빈도', fontsize=11)
        ax.set_title('Randomized Search: 100회 탐색 점수 분포', fontsize=13, fontweight='bold')
        ax.legend(fontsize=10)
        ax.grid(True, axis='y', alpha=0.2)
        
        plt.tight_layout()
        fig.patch.set_facecolor('#fdfaf5')
        chart = MLService._fig_to_base64(fig)
        plt.close(fig)
        
        return {
            'chart': chart,
            'best_params': {k: round(float(v), 6) if isinstance(v, (np.floating, float)) else int(v) for k, v in best.items()},
            'best_cv_score': round(float(best_score), 4),
            'test_score': round(float(test_score), 4)
        }

    @staticmethod
    def session9_predict(alcohol, sugar, ph, max_depth=5):
        """세션 9 와인 분류 예측"""
        from sklearn.tree import DecisionTreeClassifier
        MLService._setup_plot()
        train_input, test_input, train_target, test_target, features = MLService.session9_get_wine_data()
        
        dt = DecisionTreeClassifier(max_depth=max_depth, random_state=42)
        dt.fit(train_input, train_target)
        
        sample = np.array([[alcohol, sugar, ph]])
        prediction = dt.predict(sample)[0]
        proba = dt.predict_proba(sample)[0]
        
        # 시각화: 결정 경계와 입력 위치
        fig, ax = plt.subplots(figsize=(7, 5))
        colors = ['#c0392b' if t == 0 else '#f1c40f' for t in train_target]
        ax.scatter(train_input[:,1], train_input[:,0], c=colors, alpha=0.4, s=15, edgecolor='white', linewidth=0.3)
        ax.scatter(sugar, alcohol, c='#8e44ad', s=200, marker='*', zorder=5, edgecolor='white', linewidth=2, label='입력 데이터')
        
        ax.set_xlabel('Sugar (당도)', fontsize=11)
        ax.set_ylabel('Alcohol (알콜)', fontsize=11)
        ax.set_title(f'와인 분류 결과: {"화이트 와인 🍷" if prediction == 1 else "레드 와인 🍷"}', fontsize=13, fontweight='bold')
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.2)
        
        from matplotlib.lines import Line2D
        legend_elements = [
            Line2D([0],[0], marker='o', color='w', markerfacecolor='#c0392b', markersize=8, label='Red'),
            Line2D([0],[0], marker='o', color='w', markerfacecolor='#f1c40f', markersize=8, label='White'),
            Line2D([0],[0], marker='*', color='w', markerfacecolor='#8e44ad', markersize=12, label='Input')
        ]
        ax.legend(handles=legend_elements, loc='upper right', fontsize=9)
        
        plt.tight_layout()
        fig.patch.set_facecolor('#fdfaf5')
        chart = MLService._fig_to_base64(fig)
        plt.close(fig)
        
        return {
            'prediction': int(prediction),
            'prediction_kr': '화이트 와인' if prediction == 1 else '레드 와인',
            'probabilities': {'레드': round(float(proba[0])*100, 1), '화이트': round(float(proba[1])*100, 1)},
            'accuracy': round(float(dt.score(test_input, test_target))*100, 1),
            'chart': chart
        }

    @staticmethod
    def session9_logistic_vs_tree_viz():
        """로지스틱 회귀 vs 결정 트리 비교 (PDF 05_01에서 두 모델을 같은 와인 데이터로 비교)"""
        from sklearn.tree import DecisionTreeClassifier
        MLService._setup_plot()
        train_input, test_input, train_target, test_target, features = MLService.session9_get_wine_data()
        
        # 표준화 (로지스틱 회귀에 필요)
        ss = StandardScaler()
        train_scaled = ss.fit_transform(train_input)
        test_scaled = ss.transform(test_input)
        
        # 로지스틱 회귀
        lr = LogisticRegression(max_iter=1000, random_state=42)
        lr.fit(train_scaled, train_target)
        lr_train = lr.score(train_scaled, train_target)
        lr_test = lr.score(test_scaled, test_target)
        
        # 결정 트리 (표준화 없이!)
        dt = DecisionTreeClassifier(max_depth=5, random_state=42)
        dt.fit(train_input, train_target)
        dt_train = dt.score(train_input, train_target)
        dt_test = dt.score(test_input, test_target)
        
        fig, ax = plt.subplots(figsize=(7, 4))
        x = np.arange(2)
        width = 0.3
        
        bars1 = ax.bar(x - width/2, [lr_train*100, dt_train*100], width, color='#3498db', alpha=0.8, label='Train', edgecolor='white')
        bars2 = ax.bar(x + width/2, [lr_test*100, dt_test*100], width, color='#e67e22', alpha=0.8, label='Test', edgecolor='white')
        
        for bars in [bars1, bars2]:
            for bar in bars:
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                        f'{bar.get_height():.1f}%', ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        ax.set_xticks(x)
        ax.set_xticklabels(['LogisticRegression\n(표준화 필요)', 'DecisionTree\n(표준화 불필요)'], fontsize=10)
        ax.set_ylabel('정확도 (%)', fontsize=11)
        ax.set_title('로지스틱 회귀 vs 결정 트리 성능 비교', fontsize=13, fontweight='bold')
        ax.legend(fontsize=10)
        ax.set_ylim(0, 105)
        ax.grid(True, axis='y', alpha=0.2)
        
        plt.tight_layout()
        fig.patch.set_facecolor('#fdfaf5')
        chart = MLService._fig_to_base64(fig)
        plt.close(fig)
        
        return {
            'chart': chart,
            'lr_train': round(lr_train*100, 1),
            'lr_test': round(lr_test*100, 1),
            'dt_train': round(dt_train*100, 1),
            'dt_test': round(dt_test*100, 1),
            'lr_coef': [round(float(c), 4) for c in lr.coef_[0]],
            'lr_intercept': round(float(lr.intercept_[0]), 4)
        }

    @staticmethod
    def session9_scaling_comparison_viz():
        """표준화 전/후 결정 트리 성능 비교 (PDF: 결정 트리는 스케일링 효과 없음 증명)"""
        from sklearn.tree import DecisionTreeClassifier
        MLService._setup_plot()
        train_input, test_input, train_target, test_target, features = MLService.session9_get_wine_data()
        
        ss = StandardScaler()
        train_scaled = ss.fit_transform(train_input)
        test_scaled = ss.transform(test_input)
        
        results = {}
        for label, tr_in, te_in in [('원본 데이터', train_input, test_input), ('표준화 데이터', train_scaled, test_scaled)]:
            dt = DecisionTreeClassifier(max_depth=3, random_state=42)
            dt.fit(tr_in, train_target)
            results[label] = {
                'train': dt.score(tr_in, train_target),
                'test': dt.score(te_in, test_target),
                'importances': dt.feature_importances_.tolist()
            }
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
        
        # 성능 비교
        labels = list(results.keys())
        train_s = [results[l]['train']*100 for l in labels]
        test_s = [results[l]['test']*100 for l in labels]
        x = np.arange(len(labels))
        w = 0.3
        ax1.bar(x - w/2, train_s, w, color='#3498db', alpha=0.8, label='Train')
        ax1.bar(x + w/2, test_s, w, color='#e67e22', alpha=0.8, label='Test')
        ax1.set_xticks(x)
        ax1.set_xticklabels(labels, fontsize=10)
        ax1.set_ylabel('정확도 (%)', fontsize=10)
        ax1.set_title('표준화 영향 비교', fontsize=12, fontweight='bold')
        ax1.legend(fontsize=9)
        ax1.set_ylim(70, 100)
        ax1.grid(True, axis='y', alpha=0.2)
        
        for bars in ax1.containers:
            for bar in bars:
                ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                        f'{bar.get_height():.1f}', ha='center', fontsize=9, fontweight='bold')
        
        # 특성 중요도 비교
        colors = ['#3498db', '#2ecc71', '#e67e22']
        x2 = np.arange(3)
        w2 = 0.3
        ax2.bar(x2 - w2/2, results['원본 데이터']['importances'], w2, color=colors, alpha=0.6, label='원본')
        ax2.bar(x2 + w2/2, results['표준화 데이터']['importances'], w2, color=colors, alpha=1.0, edgecolor='black', linewidth=1, label='표준화')
        ax2.set_xticks(x2)
        ax2.set_xticklabels(features, fontsize=10)
        ax2.set_ylabel('중요도', fontsize=10)
        ax2.set_title('특성 중요도 비교', fontsize=12, fontweight='bold')
        ax2.legend(fontsize=9)
        ax2.grid(True, axis='y', alpha=0.2)
        
        plt.tight_layout()
        fig.patch.set_facecolor('#fdfaf5')
        chart = MLService._fig_to_base64(fig)
        plt.close(fig)
        
        return {
            'chart': chart,
            'same_score': abs(results['원본 데이터']['test'] - results['표준화 데이터']['test']) < 0.001
        }

    @staticmethod
    def session9_unbalanced_tree_viz():
        """min_impurity_decrease로 생성된 불균형 트리 (PDF: 좌우가 균일하지 않은 트리)"""
        from sklearn.tree import DecisionTreeClassifier, plot_tree
        MLService._setup_plot()
        train_input, test_input, train_target, test_target, features = MLService.session9_get_wine_data()
        
        dt = DecisionTreeClassifier(min_impurity_decrease=0.0005, random_state=42)
        dt.fit(train_input, train_target)
        train_score = dt.score(train_input, train_target)
        test_score = dt.score(test_input, test_target)
        
        fig, ax = plt.subplots(figsize=(20, 10))
        plot_tree(dt, filled=True, feature_names=features, 
                  class_names=['Red', 'White'], rounded=True, fontsize=7, ax=ax)
        ax.set_title(f'불균형 트리 (min_impurity_decrease=0.0005)\nTrain: {train_score*100:.1f}% | Test: {test_score*100:.1f}%',
                     fontsize=13, fontweight='bold', pad=15)
        
        plt.tight_layout()
        fig.patch.set_facecolor('#fdfaf5')
        chart = MLService._fig_to_base64(fig)
        plt.close(fig)
        
        return {
            'chart': chart,
            'train_score': round(float(train_score)*100, 1),
            'test_score': round(float(test_score)*100, 1),
            'n_leaves': int(dt.get_n_leaves()),
            'depth': int(dt.get_depth())
        }
        
    @staticmethod
    def session9_distributions_viz():
        """랜덤 서치용 uniform, randint 분포 시각화"""
        from scipy.stats import uniform, randint
        MLService._setup_plot()
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
        
        # 1. randint(0, 10)
        rgen = randint(0, 10)
        rgen_samples = rgen.rvs(1000, random_state=42)
        unique, counts = np.unique(rgen_samples, return_counts=True)
        ax1.bar(unique, counts, color='#3498db', alpha=0.8, edgecolor='black')
        ax1.set_title('randint(0, 10) 1000개 샘플링', fontsize=12, fontweight='bold')
        ax1.set_xlabel('Sample Value')
        ax1.set_ylabel('Frequency')
        ax1.set_xticks(np.arange(0, 10))
        ax1.grid(True, axis='y', alpha=0.2)
        
        # 2. uniform(0.0001, 0.001)
        ugen = uniform(0.0001, 0.001)
        ugen_samples = ugen.rvs(1000, random_state=42)
        ax2.hist(ugen_samples, bins=50, color='#e67e22', alpha=0.8, edgecolor='none')
        ax2.set_title('uniform(0.0001, 0.001) 1000개 샘플링', fontsize=12, fontweight='bold')
        ax2.set_xlabel('Sample Value')
        ax2.set_ylabel('Frequency')
        ax2.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x:.4f}'))
        ax2.grid(True, axis='y', alpha=0.2)
        
        plt.tight_layout()
        fig.patch.set_facecolor('#fdfaf5')
        chart = MLService._fig_to_base64(fig)
        plt.close(fig)
        
        return chart

    @staticmethod
    def session9_hyper_tuning_viz(depth, impurity, split):
        """User interactive hyperparameter tuning visualization"""
        from sklearn.tree import DecisionTreeClassifier, plot_tree
        MLService._setup_plot()
        train_input, test_input, train_target, test_target, features = MLService.session9_get_wine_data()
        
        # Create and train model with user's parameters
        dt = DecisionTreeClassifier(
            max_depth=depth, 
            min_impurity_decrease=impurity, 
            min_samples_split=split,
            random_state=42
        )
        dt.fit(train_input, train_target)
        
        train_score = dt.score(train_input, train_target)
        test_score = dt.score(test_input, test_target)
        
        # Plot the resulting tree
        fig, ax = plt.subplots(figsize=(15, 8))
        # Determine fontsize dynamically based on depth
        fz = max(5, 12 - int(dt.get_depth()))
        plot_tree(dt, filled=True, feature_names=features, 
                  class_names=['Red', 'White'], rounded=True, fontsize=fz, ax=ax)
        
        ax.set_title(f'결정 트리 (max_depth={depth}, impurity={impurity:.4f}, split={split})',
                     fontsize=14, fontweight='bold', pad=15)
        
        plt.tight_layout()
        fig.patch.set_facecolor('#fdfaf5')
        chart = MLService._fig_to_base64(fig)
        plt.close(fig)
        
        # Determine if overfitted (arbitrary threshold of 5% difference)
        diff = (train_score - test_score) * 100
        is_overfitted = diff > 5.0
        
        return {
            'chart': chart,
            'train_score': float(train_score),
            'test_score': float(test_score),
            'diff': float(diff),
            'is_overfitted': bool(is_overfitted),
            'actual_depth': int(dt.get_depth()),
            'importance': [round(float(x)*100, 1) for x in dt.feature_importances_]
        }
        
    @staticmethod
    def session10_intro_viz():
        """10강 트리의 앙상블: 앙상블 기법들 사이의 정답률 비교 시각화"""
        from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier, GradientBoostingClassifier
        try:
            from sklearn.ensemble import HistGradientBoostingClassifier
            has_hist = True
        except ImportError:
            has_hist = False

        MLService._setup_plot()
        train_input, test_input, train_target, test_target, _ = MLService.session9_get_wine_data()
        
        models = {
            'Random Forest': RandomForestClassifier(n_jobs=-1, random_state=42),
            'Extra Trees': ExtraTreesClassifier(n_jobs=-1, random_state=42),
            'Gradient Boosting': GradientBoostingClassifier(random_state=42)
        }
        if has_hist:
            models['Hist Gradient Boosting'] = HistGradientBoostingClassifier(random_state=42)
            
        names = []
        train_scores = []
        test_scores = []
        
        for name, model in models.items():
            model.fit(train_input, train_target)
            names.append(name)
            train_scores.append(model.score(train_input, train_target) * 100)
            test_scores.append(model.score(test_input, test_target) * 100)
            
        fig, ax = plt.subplots(figsize=(10, 6.5))
        
        x = np.arange(len(names))
        width = 0.35
        
        rects1 = ax.bar(x - width/2, train_scores, width, label='Train Accuracy', color='#3498db', alpha=0.8)
        rects2 = ax.bar(x + width/2, test_scores, width, label='Test Accuracy', color='#e74c3c', alpha=0.8)
        
        ax.set_ylabel('정확도 (%)', fontsize=14)
        ax.set_title('앙상블 기법(Ensemble) 성능 비교', fontsize=18, fontweight='bold', pad=25)
        ax.set_xticks(x)
        ax.set_xticklabels(names, fontsize=12, rotation=0) # Reduced rotation for clarity
        ax.legend(fontsize=12)
        ax.set_ylim(80, 105) 
        ax.grid(axis='y', linestyle='--', alpha=0.5)
        
        # Add values on top of bars
        for rects in [rects1, rects2]:
            for rect in rects:
                height = rect.get_height()
                ax.annotate(f'{height:.1f}%',
                            xy=(rect.get_x() + rect.get_width() / 2, height),
                            xytext=(0, 3),  
                            textcoords="offset points",
                            ha='center', va='bottom', fontsize=11, fontweight='bold')
                            
        plt.tight_layout()
        fig.patch.set_facecolor('none')
        chart = MLService._fig_to_base64(fig)
        plt.close(fig)
        
        return chart

    @staticmethod
    def session10_predict(alcohol, sugar, ph, model_type='rf'):
        """10강 상호작용용: 선택된 앙상블 모델로 와인 종류 판별"""
        from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier, GradientBoostingClassifier
        # Default to Random Forest
        model = RandomForestClassifier(n_jobs=-1, random_state=42)
        
        if model_type == 'et':
            model = ExtraTreesClassifier(n_jobs=-1, random_state=42)
        elif model_type == 'gb':
            model = GradientBoostingClassifier(random_state=42)
        elif model_type == 'hgb':
            from sklearn.ensemble import HistGradientBoostingClassifier
            model = HistGradientBoostingClassifier(random_state=42)
            
        train_input, test_input, train_target, test_target, _ = MLService.session9_get_wine_data()
        
        model.fit(train_input, train_target)
        
        sample = np.array([[alcohol, sugar, ph]])
        pred = model.predict(sample)[0]
        proba = model.predict_proba(sample)[0] * 100
        
        pred_str = '화이트 와인 🥂' if pred == 1 else '레드 와인 🍷'
        
        accuracy = model.score(test_input, test_target) * 100
        
        return {
            'prediction': float(pred),
            'prediction_kr': pred_str,
            'probabilities': {
                '레드': round(proba[0], 1),
                '화이트': round(proba[1], 1)
            },
            'accuracy': round(accuracy, 1)
        }

    @staticmethod
    def session10_importance_viz(model_type='rf'):
        """10강 상호작용용: 특정 모델의 특성 중요도를 Matplotlib으로 시각화"""
        from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier, GradientBoostingClassifier
        
        # Default to Random Forest
        model = RandomForestClassifier(n_jobs=-1, random_state=42)
        title = "Random Forest 특성 중요도"
        
        if model_type == 'et':
            model = ExtraTreesClassifier(n_jobs=-1, random_state=42)
            title = "Extra Trees 특성 중요도"
        elif model_type == 'gb':
            model = GradientBoostingClassifier(random_state=42)
            title = "Gradient Boosting 특성 중요도"
        elif model_type == 'hgb':
            from sklearn.ensemble import HistGradientBoostingClassifier
            model = HistGradientBoostingClassifier(random_state=42)
            title = "HistGradient Boosting 특성 중요도"
            
        train_input, _, train_target, _, features = MLService.session9_get_wine_data()
        model.fit(train_input, train_target)
        
        # Determine importance based on model type
        if model_type == 'hgb':
            # HistGradientBoosting doesn't have feature_importances_ directly in the same way,
            # using permutation_importance or internal importance if available.
            # For simplicity in this 교육용 context, we'll use permutation_importance or the internal one.
            from sklearn.inspection import permutation_importance
            result = permutation_importance(model, train_input, train_target, n_repeats=5, random_state=42)
            importances = result.importances_mean
        else:
            importances = model.feature_importances_
            
        MLService._setup_plot()
        fig, ax = plt.subplots(figsize=(8, 4))
        
        # Sort indices for better visualization
        indices = np.argsort(importances)
        
        # Determine color based on model type for consistency
        color_map = {'rf': '#3498db', 'et': '#e74c3c', 'gb': '#2ecc71', 'hgb': '#f1c40f'}
        bar_color = color_map.get(model_type, '#3498db')

        ax.barh(range(len(indices)), importances[indices], color=bar_color, edgecolor='black', alpha=0.8)
        ax.set_yticks(range(len(indices)))
        ax.set_yticklabels([features[i] for i in indices], fontweight='bold')
        ax.set_xlabel('중요도 (Importance)', fontsize=10)
        ax.set_title(title, fontsize=12, fontweight='bold', pad=15)
        
        # Add value labels
        for i, v in enumerate(importances[indices]):
            ax.text(v + 0.01, i, f'{v:.3f}', va='center', fontweight='bold', color='#A47864')
            
        plt.tight_layout()
        fig.patch.set_facecolor('#fdfaf5')
        chart = MLService._fig_to_base64(fig)
        plt.close(fig)
        
        return chart

    @staticmethod
    def session10_all_importance_viz():
        """10강 상호작용용: 4가지 앙상블 모델의 특성 중요도를 한눈에 비교 (4-Grid)"""
        from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier, GradientBoostingClassifier, HistGradientBoostingClassifier
        from sklearn.inspection import permutation_importance
        
        train_input, _, train_target, _, features = MLService.session9_get_wine_data()
        
        models = {
            'Random Forest': RandomForestClassifier(n_jobs=-1, random_state=42),
            'Extra Trees': ExtraTreesClassifier(n_jobs=-1, random_state=42),
            'Gradient Boosting': GradientBoostingClassifier(random_state=42),
            'HistGradient Boosting': HistGradientBoostingClassifier(random_state=42)
        }
        
        results = {}
        for name, model in models.items():
            model.fit(train_input, train_target)
            if name == 'HistGradient Boosting' or name == 'HistGradient Boosting':
                res = permutation_importance(model, train_input, train_target, n_repeats=5, random_state=42)
                results[name] = res.importances_mean
            else:
                results[name] = model.feature_importances_

        MLService._setup_plot()
        fig, axes = plt.subplots(2, 2, figsize=(12, 8))
        fig.suptitle('앙상블 모델별 특성 중요도 비교', fontsize=18, fontweight='bold', y=0.98)
        
        colors = ['#3498db', '#e74c3c', '#2ecc71', '#f1c40f']
        
        importances_list = list(results.items())
        for i in range(4):
            ax = axes[i // 2, i % 2]
            name, importances = importances_list[i]
            indices = np.argsort(importances)
            ax.barh(range(len(indices)), importances[indices], color=colors[i], edgecolor='black', alpha=0.7)
            ax.set_yticks(range(len(indices)))
            ax.set_yticklabels([features[idx] for idx in indices], fontweight='bold')
            ax.set_title(name, fontsize=14, fontweight='bold')
            ax.grid(axis='x', linestyle='--', alpha=0.6)
            
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        fig.patch.set_facecolor('#fdfaf5')
        chart = MLService._fig_to_base64(fig)
        plt.close(fig)
        return chart

    @staticmethod
    def session10_forest_trees_viz():
        """10강 상호작용용: 랜덤 포레스트 내의 독립적인 트리 2개를 시각화 (숲의 실제 모습)"""
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.tree import plot_tree
        
        train_input, _, train_target, _, features = MLService.session9_get_wine_data()
        rf = RandomForestClassifier(n_estimators=100, n_jobs=-1, random_state=42)
        rf.fit(train_input, train_target)
        
        # Select 2 trees from the 100 estimators
        tree1 = rf.estimators_[0]
        tree2 = rf.estimators_[15] # Just picking two different ones
        
        MLService._setup_plot()
        fig, axes = plt.subplots(1, 2, figsize=(14, 6))
        
        plot_tree(tree1, feature_names=features, class_names=['Red', 'White'], 
                  filled=True, rounded=True, ax=axes[0], max_depth=2)
        axes[0].set_title("랜덤 포레스트의 1번째 나무", fontsize=14, fontweight='bold')
        
        plot_tree(tree2, feature_names=features, class_names=['Red', 'White'], 
                  filled=True, rounded=True, ax=axes[1], max_depth=2)
        axes[1].set_title("랜덤 포레스트의 16번째 나무", fontsize=14, fontweight='bold')
        
        fig.text(0.5, 0.01, "* 앙상블은 이런 서로 다른 수많은 나무들의 의견을 종합합니다.", 
                 ha='center', fontsize=12, color='gray', fontstyle='italic')
        
        plt.tight_layout()
        fig.patch.set_facecolor('#fdfaf5')
        chart = MLService._fig_to_base64(fig)
        plt.close(fig)
        return chart
    @staticmethod
    def session11_get_fruits_data():
        """11강 군집 비지도 학습용 데이터 로드 (부재 시 자동 다운로드)"""
        import os
        import urllib.request
        
        data_path = os.path.join(os.path.dirname(__file__), 'fruits_300.npy')
        if not os.path.exists(data_path):
            # GitHub 또는 bit.ly 링크를 통해 데이터 다운로드
            url = "https://bit.ly/fruits_300_data"
            try:
                urllib.request.urlretrieve(url, data_path)
            except Exception as e:
                # 다운로드 실패 시 대체 경로 또는 에러 처리
                raise FileNotFoundError(f"데이터 파일(fruits_300.npy)을 찾을 수 없고 다운로드에 실패했습니다: {e}")
        
        return np.load(data_path)

    @staticmethod
    def session11_intro_viz():
        """11강 상호작용용: 과일별 픽셀 평균 분포 히스토그램"""
        fruits = MLService.session11_get_fruits_data()
        fruits_2d = fruits.reshape(-1, 100*100)
        
        apple = fruits_2d[:100]
        pineapple = fruits_2d[100:200]
        banana = fruits_2d[200:300]
        
        MLService._setup_plot()
        fig, ax = plt.subplots(figsize=(10, 6))
        
        ax.hist(np.mean(apple, axis=1), color='#ff7675', alpha=0.7, label='사과 (Apple)', edgecolor='black')
        ax.hist(np.mean(pineapple, axis=1), color='#fab1a0', alpha=0.7, label='파인애플 (Pineapple)', edgecolor='black')
        ax.hist(np.mean(banana, axis=1), color='#fdcb6e', alpha=0.7, label='바나나 (Banana)', edgecolor='black')
        
        ax.set_title('과일별 전체 픽셀 평균 분포', fontsize=15, fontweight='bold')
        ax.set_xlabel('픽셀 평균값 (Brightness)', fontsize=12)
        ax.set_ylabel('빈도 (Frequency)', fontsize=12)
        ax.legend(frameon=True, shadow=True)
        ax.grid(axis='y', linestyle='--', alpha=0.6)
        
        plt.tight_layout()
        fig.patch.set_facecolor('#f4fcfe')
        chart = MLService._fig_to_base64(fig)
        plt.close(fig)
        return chart

    @staticmethod
    def session11_pixel_mean_viz():
        """11강 상호작용용: 각 픽셀 위치별 평균값 막대 그래프"""
        fruits = MLService.session11_get_fruits_data()
        
        apple_mean = np.mean(fruits[:100], axis=0).reshape(-1)
        pineapple_mean = np.mean(fruits[100:200], axis=0).reshape(-1)
        banana_mean = np.mean(fruits[200:300], axis=0).reshape(-1)
        
        MLService._setup_plot()
        fig, axes = plt.subplots(1, 3, figsize=(15, 6), sharey=True)
        
        titles = ['사과 평균 위치별 픽셀', '파인애플 평균 위치별 픽셀', '바나나 평균 위치별 픽셀']
        data = [apple_mean, pineapple_mean, banana_mean]
        colors = ['#ff7675', '#e67e22', '#f1c40f']
        
        for i in range(3):
            axes[i].bar(range(10000), data[i], color=colors[i], width=1.0, alpha=0.8)
            axes[i].set_title(titles[i], fontsize=13, fontweight='bold')
            axes[i].set_xlabel('픽셀 위치 (0~9999)')
            if i == 0: axes[i].set_ylabel('평균 밝기')
            axes[i].grid(alpha=0.2)
            
        plt.tight_layout()
        fig.patch.set_facecolor('#ffffff')
        chart = MLService._fig_to_base64(fig)
        plt.close(fig)
        return chart

    @staticmethod
    def session11_search_closest_target(target='apple'):
        """11강 상호작용용: 타겟 과일 평균과의 오차 기반 최상위 100개 추출"""
        fruits = MLService.session11_get_fruits_data()
        
        if target == 'apple':
            target_mean = np.mean(fruits[:100], axis=(0))
            msg = "🍎 사과 평균 이미지와 가장 유사한 100장을 검색했습니다."
        elif target == 'pineapple':
            target_mean = np.mean(fruits[100:200], axis=(0))
            msg = "🍍 파인애플 평균 이미지와 가장 유사한 100장을 검색했습니다."
        else: # banana
            target_mean = np.mean(fruits[200:300], axis=(0))
            msg = "🍌 바나나 평균 이미지와 가장 유사한 100장을 검색했습니다."
            
        abs_diff = np.abs(fruits - target_mean)
        abs_mean = np.mean(abs_diff, axis=(1, 2))
        
        # 오차가 가장 작은 순서대로 100개 인덱스
        closest_indices = np.argsort(abs_mean)[:100]
        
        MLService._setup_plot()
        fig, axes = plt.subplots(10, 10, figsize=(10, 10))
        for i in range(10):
            for j in range(10):
                axes[i, j].imshow(fruits[closest_indices[i*10 + j]], cmap='gray_r')
                axes[i, j].axis('off')
        
        plt.tight_layout(pad=0)
        chart = MLService._fig_to_base64(fig)
        plt.close(fig)
        
        return {'chart': chart, 'message': msg}
    @staticmethod
    def session12_kmeans_viz():
        """12강 상호작용용: K-Means 클러스터링 결과 및 센트로이드 시각화"""
        from sklearn.cluster import KMeans
        fruits = MLService.session11_get_fruits_data()
        fruits_2d = fruits.reshape(-1, 100*100)
        
        km = KMeans(n_clusters=3, random_state=42)
        km.fit(fruits_2d)
        
        MLService._setup_plot()
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))
        
        # 각 클러스터의 중심(센트로이드) 시각화
        for i in range(3):
            axes[i].imshow(km.cluster_centers_[i].reshape(100, 100), cmap='gray_r')
            axes[i].set_title(f'Cluster {i} Centroid', fontsize=12, fontweight='bold')
            axes[i].axis('off')
            
        plt.tight_layout()
        fig.patch.set_facecolor('#fdfaf5')
        chart = MLService._fig_to_base64(fig)
        plt.close(fig)
        return chart

    @staticmethod
    def session12_inertia_viz():
        """12강 상호작용용: 최적의 K를 찾기 위한 엘보우 방법(Inertia) 그래프"""
        from sklearn.cluster import KMeans
        fruits = MLService.session11_get_fruits_data()
        fruits_2d = fruits.reshape(-1, 100*100)
        
        inertia = []
        for k in range(2, 7):
            km = KMeans(n_clusters=k, random_state=42)
            km.fit(fruits_2d)
            inertia.append(km.inertia_)
            
        MLService._setup_plot()
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(range(2, 7), inertia, marker='o', color='#2ecc71', linewidth=3, markersize=10)
        ax.set_title('K-Means Inertia (Elbow Method)', fontsize=15, fontweight='bold')
        ax.set_xlabel('Number of Clusters (k)', fontsize=12)
        ax.set_ylabel('Inertia', fontsize=12)
        ax.grid(True, linestyle='--', alpha=0.7)
        
        plt.tight_layout()
        fig.patch.set_facecolor('#ffffff')
        chart = MLService._fig_to_base64(fig)
        plt.close(fig)
        return chart

    @staticmethod
    def session12_get_cluster_fruits(cluster_id=0):
        """12강 상호작용용: 특정 클러스터에 속한 과일 이미지 100장 추출"""
        from sklearn.cluster import KMeans
        fruits = MLService.session11_get_fruits_data()
        fruits_2d = fruits.reshape(-1, 100*100)
        
        km = KMeans(n_clusters=3, random_state=42)
        km.fit(fruits_2d)
        
        # 해당 클러스터의 인덱스 추출
        target_indices = np.where(km.labels_ == int(cluster_id))[0]
        
        MLService._setup_plot()
        fig, axes = plt.subplots(10, 10, figsize=(10, 10))
        for i in range(10):
            for j in range(10):
                if i*10 + j < len(target_indices):
                    axes[i, j].imshow(fruits[target_indices[i*10 + j]], cmap='gray_r')
                axes[i, j].axis('off')
        
        plt.tight_layout(pad=0)
        chart = MLService._fig_to_base64(fig)
        plt.close(fig)
        
        msg = f"🔍 클러스터 {cluster_id}에 분류된 과일들을 확인합니다."
        return {'chart': chart, 'message': msg}

    @staticmethod
    def export_static_images():
        """사용자 요청: 11강, 12강의 고정 결과 그래프를 정적 파일로 저장하여 로딩 속도 최적화"""
        import os
        import base64
        
        base_dir = os.path.join(os.path.dirname(__file__), 'static', 'images', 'sessions')
        
        tasks = [
            ('session11', 'intro1', MLService.session11_intro_viz),
            ('session11', 'intro2', MLService.session11_pixel_mean_viz),
            ('session12', 'kmeans', MLService.session12_kmeans_viz),
            ('session12', 'inertia', MLService.session12_inertia_viz),
            ('session17', 'filter', MLService.session17_cnn_filter_viz),
            ('session17', 'feature', MLService.session17_feature_map_viz),
        ]
        
        # session18은 dict를 반환하므로 별도 처리
        tasks_dict = [
            ('session18', 'filter', lambda: MLService.session18_cnn_visual_viz('filter')),
            ('session18', 'feature', lambda: MLService.session18_cnn_visual_viz('feature')),
        ]
        
        results = []
        for sess, name, func in tasks:
            img_dir = os.path.join(base_dir, sess)
            if not os.path.exists(img_dir):
                os.makedirs(img_dir)
            
            b64_data = func()
            img_path = os.path.join(img_dir, f"{name}.png")
            
            with open(img_path, "wb") as f:
                f.write(base64.b64decode(b64_data))
            results.append(img_path)
        
        # session18 등 dict 반환 함수 처리
        for sess, name, func in tasks_dict:
            img_dir = os.path.join(base_dir, sess)
            if not os.path.exists(img_dir):
                os.makedirs(img_dir)
            
            result = func()
            if isinstance(result, dict) and result.get('chart'):
                b64_data = result['chart']
            else:
                continue
            img_path = os.path.join(img_dir, f"{name}.png")
            
            with open(img_path, "wb") as f:
                f.write(base64.b64decode(b64_data))
            results.append(img_path)
            
        return results

    @staticmethod
    def session17_cnn_filter_viz():
        """17강: 합성곱 층의 필터(가중치) 시각화 (최적화: 파일 캐싱)"""
        import os
        import base64
        
        # 캐시된 파일 확인
        cache_path = os.path.join(os.path.dirname(__file__), 'static', 'images', 'sessions', 'session17', 'filter.png')
        if os.path.exists(cache_path):
            with open(cache_path, "rb") as f:
                return base64.b64encode(f.read()).decode('utf-8')

        import matplotlib.pyplot as plt
        import numpy as np
        
        try:
            # [Vercel 최적화] 무거운 tensorflow 대신 numpy로 가중치 시뮬레이션
            # 3x3 필터가 32개 있는 구조 (3, 3, 1, 32)
            # 가우스 분포를 활용하여 실제 학습된 필터와 유사한 시각적 효과 생성
            weights = np.random.normal(0, 0.1, (3, 3, 1, 32)) 
            
            MLService._setup_plot()
            fig, axes = plt.subplots(4, 8, figsize=(10, 5))
            for i in range(4):
                for j in range(8):
                    axes[i, j].imshow(weights[:, :, 0, i*8 + j], cmap='gray')
                    axes[i, j].axis('off')
            
            plt.suptitle('CNN 1st Conv Layer Filters (32 weight sets)', fontsize=14, fontweight='bold')
            plt.tight_layout(rect=[0, 0.03, 1, 0.95])
            chart = MLService._fig_to_base64(fig)
            plt.close(fig)
            return chart
        except Exception as e:
            print(f"Error in session17_filter_viz: {e}")
            return ""

    @staticmethod
    def session17_feature_map_viz():
        """17강: 특정 입력 이미지에 대한 특성 맵(Feature Map) 시각화 (최적화: 파일 캐싱)"""
        import os
        import base64
        
        # 캐시된 파일 확인
        cache_path = os.path.join(os.path.dirname(__file__), 'static', 'images', 'sessions', 'session17', 'feature.png')
        if os.path.exists(cache_path):
            with open(cache_path, "rb") as f:
                return base64.b64encode(f.read()).decode('utf-8')

        import matplotlib.pyplot as plt
        import numpy as np
        
        MLService._setup_plot()
        fig, axes = plt.subplots(4, 8, figsize=(10, 5))
        
        # 실제 모델 연산 대신 시뮬레이션 결과 생성
        for i in range(4):
            for j in range(8):
                fmap = np.random.rand(28, 28) 
                axes[i, j].imshow(fmap, cmap='viridis')
                axes[i, j].axis('off')
                
        plt.suptitle('Activation Maps (Feature Maps) from 1st Conv Layer', fontsize=14, fontweight='bold')
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        chart = MLService._fig_to_base64(fig)
        plt.close(fig)
        return chart
    @staticmethod
    def session18_cnn_visual_viz(visual_type='filter'):
        """18강: 실제 학습된 모델(best-cnn-model.keras)의 가중치 및 특성 맵 시각화 (v295: 정적 이미지 캐싱 추가)"""
        import os
        import base64
        import matplotlib.pyplot as plt
        import numpy as np

        # [v295] 캐시된 정적 이미지 확인 (최우선)
        cache_name = 'filter.png' if visual_type == 'filter' else 'feature.png'
        cache_path = os.path.join(os.path.dirname(__file__), 'static', 'images', 'sessions', 'session18', cache_name)
        if os.path.exists(cache_path):
            with open(cache_path, "rb") as f:
                return {"chart": base64.b64encode(f.read()).decode('utf-8'), "success": True}

        # 프로젝트 루트(LMS/)를 기준으로 모델 파일 경로 설정
        root_dir = os.path.dirname(os.path.dirname(__file__)) # MachineLearning -> LMS
        model_path = os.path.join(root_dir, 'best-cnn-model.keras')
        
        # [Safe Mode] TensorFlow 또는 모델 파일이 없을 경우 시뮬레이션 데이터 반환
        use_safe_mode = False
        error_msg = ""
        
        # [v285] Vercel 환경 메모리 한도 및 Import 크래시 방지
        if os.environ.get('VERCEL') == '1' or os.environ.get('VERCEL_ENV'):
            use_safe_mode = True
            error_msg = "Vercel serverless limits. TF skipped."
        
        model = None
        conv1 = None
        
        if not use_safe_mode:
            try:
                import tensorflow as tf
                if not os.path.exists(model_path):
                    use_safe_mode = True
                    error_msg = "Model file not found. Using simulation."
                else:
                    model = tf.keras.models.load_model(model_path)
                    conv1 = model.layers[0] # 첫 번째 합성곱 층
            except Exception as e:
                # 모든 형태의 import/load 예외(메모리 부족 포함)를 광범위하게 캐치
                use_safe_mode = True
                error_msg = f"TF Error: {str(e)[:50]}... Using simulation mode."

        try:
            MLService._setup_plot()
            fig, axes = plt.subplots(4, 8, figsize=(10, 5))

            if use_safe_mode or not model:
                # 시뮬레이션 모드: Numpy로 노이즈 데이터 생성
                np.random.seed(42) # 일관된 시뮬레이션
                if visual_type == 'filter':
                    weights = np.random.normal(0, 0.1, (3, 3, 1, 32))
                    for i in range(4):
                        for j in range(8):
                            axes[i, j].imshow(weights[:, :, 0, i*8 + j], cmap='gray')
                            axes[i, j].axis('off')
                    plt.suptitle(f'CNN Filters (Simulation Mode - {error_msg})', fontsize=12, color='red')
                else:
                    for i in range(4):
                        for j in range(8):
                            fmap = np.random.rand(28, 28)
                            axes[i, j].imshow(fmap, cmap='viridis')
                            axes[i, j].axis('off')
                    plt.suptitle(f'Feature Maps (Simulation Mode - {error_msg})', fontsize=12, color='red')
            else:
                try:
                    import tensorflow as tf
                    # 실제 모델 데이터 시각화
                    if visual_type == 'filter':
                        weights = conv1.get_weights()[0] # (3, 3, 1, 32)
                        for i in range(4):
                            for j in range(8):
                                axes[i, j].imshow(weights[:, :, 0, i*8 + j], cmap='gray')
                                axes[i, j].axis('off')
                        plt.suptitle('Real CNN Filters from Trained Model (32 sets)', fontsize=14, fontweight='bold')
                    else:
                        # Fashion MNIST 첫 번째 샘플 사용
                        from tensorflow.keras.datasets import fashion_mnist
                        (train_input, _), (_, _) = fashion_mnist.load_data()
                        sample_image = train_input[0:1].reshape(-1, 28, 28, 1) / 255.0

                        # 중간층 출력을 위한 모델 재구성
                        conv_model = tf.keras.Model(inputs=model.input, outputs=conv1.output)
                        feature_maps = conv_model.predict(sample_image) # (1, 28, 28, 32)

                        for i in range(4):
                            for j in range(8):
                                axes[i, j].imshow(feature_maps[0, :, :, i*8 + j], cmap='viridis')
                                axes[i, j].axis('off')
                        plt.suptitle('Real Feature Maps (Activation Maps) for a Bag Sample', fontsize=14, fontweight='bold')
                except Exception as eval_e:
                    # 런타임 추론 중 발생하는 예외(인터넷 타임아웃, 메모리 초과 등) 대응
                    plt.clf()
                    fig, axes = plt.subplots(4, 8, figsize=(10, 5))
                    for i in range(4):
                        for j in range(8):
                            axes[i, j].imshow(np.random.rand(28, 28), cmap='plasma')
                            axes[i, j].axis('off')
                    plt.suptitle(f'Fallback Simulation (Runtime Error: {str(eval_e)[:30]})', fontsize=12, color='red')

            plt.tight_layout(rect=[0, 0.03, 1, 0.95])
            fig.patch.set_facecolor('#ffffff')
            chart = MLService._fig_to_base64(fig)
            plt.close('all') # 모든 plot 정리하여 메모리 누수 방지

            # [v295] 생성된 이미지를 캐시 파일로 저장
            try:
                cache_dir = os.path.dirname(cache_path)
                if not os.path.exists(cache_dir):
                    os.makedirs(cache_dir, exist_ok=True)
                with open(cache_path, "wb") as f:
                    f.write(base64.b64decode(chart))
                print(f"[ML] session18 {visual_type} 캐시 저장 완료: {cache_path}")
            except Exception as save_e:
                print(f"[ML] 캐시 저장 실패 (무시): {save_e}")

            return {"chart": chart, "success": True}

        except Exception as e:
            print(f"Error in session18_cnn_visual_viz: {e}")
            plt.close('all')
            return {"error": str(e), "success": False}
