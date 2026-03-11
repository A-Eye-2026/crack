import json
from common.session import Session

class MLQuizService:
    # 퀴즈 데이터 정의 (강의별 3~5문제)
    QUIZ_DATA = {
        1: [
            {
                "id": 1,
                "question": "사과(Apple)와 레몬(Lemon)을 분류하는 KNN 모델을 만들려고 합니다. 사과는 보통 크고 무거우며, 레몬은 작고 가볍습니다. 새로운 과일 데이터(무게: 150g, 지름: 8cm)가 들어왔을 때 K=3이라면 어떻게 분류될까요? (가장 가까운 이웃 3개 중 2개가 사과, 1개가 레몬인 경우)",
                "choices": ["사과", "레몬", "분류 불가", "둘 다 아님"],
                "answer": 0
            },
            {
                "id": 2,
                "question": "KNN 알고리즘에서 'K'의 의미는 무엇인가요?",
                "choices": ["학습 반복 횟수", "특성의 개수", "고려할 가까운 이웃의 개수", "데이터의 총 개수"],
                "answer": 2
            },
            {
                "id": 3,
                "question": "KNN 모델의 .fit() 메서드가 실제로 하는 일은 무엇인가요?",
                "choices": ["복잡한 수학 공식을 계산하여 가중치를 찾는다", "데이터를 메모리에 저장해두고 나중에 거리를 계산할 준비를 한다", "데이터의 평균과 표준편차를 구한다", "불필요한 데이터를 삭제한다"],
                "answer": 1
            }
        ],
        2: [
            {
                "id": 1,
                "question": "KNN 회귀(Regression)와 KNN 분류(Classification)의 가장 큰 차이점은 무엇인가요?",
                "choices": ["사용하는 이웃의 수가 다르다", "분류는 정답 카테고리를 맞추고, 회귀는 수치를 예측한다", "회귀는 거리를 계산하지 않는다", "분류가 훨씬 빠르다"],
                "answer": 1
            },
            {
                "id": 2,
                "question": "결정계수(R²) 값이 0.99가 나왔을 때의 의미로 가장 적절한 것은?",
                "choices": ["모델이 99% 확률로 정답을 맞춘다", "예측값이 평균값과 거의 일치한다", "모델이 타깃의 변동성을 약 99% 설명한다", "데이터가 99개라는 뜻이다"],
                "answer": 2
            },
            {
                "id": 3,
                "question": "KNN 회귀에서 예측값은 어떻게 결정되나요?",
                "choices": ["이웃들 중 가장 많이 나타나는 값", "이웃들의 타깃값의 평균", "가장 먼 이웃의 값", "랜덤하게 결정"],
                "answer": 1
            }
        ],
        3: [
            {
                "id": 1,
                "question": "데이터를 훈련 세트와 테스트 세트로 나누어야 하는 결정적인 이유는 무엇인가요?",
                "choices": ["데이터 양을 줄이기 위해", "모델이 학습하지 않은 데이터에 대해 얼마나 잘 작동하는지 확인하기 위해", "컴퓨터 메모리를 절약하기 위해", "데이터 시각화를 더 잘하기 위해"],
                "answer": 1
            },
            {
                "id": 2,
                "question": "샘플링 편향(Sampling Bias)을 방지하기 위해 사용하는 기법은?",
                "choices": ["데이터 삭제", "순차적 정렬", "계층적 샘플링(Stratified sampling)", "데이터 중복 생성"],
                "answer": 2
            },
            {
                "id": 3,
                "question": "특성들의 단위가 다를 때(예: 몸무게 kg vs 키 cm) 거리를 올바르게 계산하기 위해 수행하는 과정은?",
                "choices": ["데이터 증폭", "표준화(Standardization)", "데이터 요약", "특성 삭제"],
                "answer": 1
            }
        ],
        4: [
            {
                "id": 1,
                "question": "KNN 모델에서 K값을 너무 작게(예: K=1) 설정했을 때 발생하는 현상은?",
                "choices": ["과소적합(Underfitting)", "과적합(Overfitting)", "훈련 속도 저하", "정확도 0%"],
                "answer": 1
            },
            {
                "id": 2,
                "question": "반대로 K값을 너무 크게(예: 데이터 전체 개수) 설정했을 때 발생하는 현상은?",
                "choices": ["과소적합(Underfitting)", "과적합(Overfitting)", "모델이 너무 복잡해짐", "성능 급상승"],
                "answer": 0
            },
            {
                "id": 3,
                "question": "훈련 세트 스코어는 매우 높으나 테스트 세트 스코어가 매우 낮다면 어떤 조치를 취해야 할까요?",
                "choices": ["모델을 더 복잡하게 만든다", "모델을 덜 복잡하게 만들거나 데이터를 더 모은다", "학습을 중단한다", "정답을 무시한다"],
                "answer": 1
            }
        ],
        5: [
            {
                "id": 1,
                "question": "선형 회귀(Linear Regression) 모델이 학습을 통해 찾아내는 것은 무엇인가요?",
                "choices": ["가장 가까운 이웃", "데이터의 카테고리", "최적의 직선을 그리기 위한 기울기(계수)와 절편", "데이터의 평균값"],
                "answer": 2
            },
            {
                "id": 2,
                "question": "단순 선형 회귀로 곡선 형태의 데이터를 잘 표현하지 못할 때, 특성을 제곱하거나 변형하여 사용하는 기법은?",
                "choices": ["다항 회귀(Polynomial Regression)", "단순 회귀", "KNN 분류", "평균 회귀"],
                "answer": 0
            },
            {
                "id": 3,
                "question": "회귀 모델이 훈련 데이터의 범위를 벗어난 데이터를 예측하려 할 때 성능이 떨어지는 한계를 무엇이라 하나요?",
                "choices": ["내삽(Interpolation)", "외삽(Extrapolation)의 한계", "데이터 부족", "계산 오류"],
                "answer": 1
            }
        ],
        6: [
            {
                "id": 1,
                "question": "여러 개의 특성을 사용하여 회귀 모델을 만드는 것을 무엇이라 하나요?",
                "choices": ["단순 회귀", "다중 회귀(Multiple Regression)", "단일 회귀", "이웃 회귀"],
                "answer": 1
            },
            {
                "id": 2,
                "question": "모델의 과적합을 막기 위해 가중치를 작게 만드는 '규제(Regularization)' 기법 중 계수의 제곱을 기준으로 완화하는 방식은?",
                "choices": ["릿지(Ridge)", "라쏘(Lasso)", "선형(Linear)", "다항(Polynomial)"],
                "answer": 0
            },
            {
                "id": 3,
                "question": "라쏘(Lasso) 규제의 가장 큰 특징 중 하나는?",
                "choices": ["계수를 항상 1로 만든다", "일부 특성의 계수를 0으로 만들어 특성을 선택하는 효과가 있다", "학습 속도가 100배 빠르다", "항상 정확도가 100%다"],
                "answer": 1
            }
        ],
        7: [
            {
                "id": 1,
                "question": "로지스틱 회귀(Logistic Regression)는 이름과 달리 어떤 용도로 주로 사용되나요?",
                "choices": ["수치 예측(회귀)", "분류(Classification)", "데이터 정렬", "이미지 생성"],
                "answer": 1
            },
            {
                "id": 2,
                "question": "로지스틱 회귀에서 결과를 0과 1 사이의 확률값으로 변환하기 위해 사용하는 함수는?",
                "choices": ["로그 함수", "시그모이드(Sigmoid) 함수", "제곱 함수", "평균 함수"],
                "answer": 1
            },
            {
                "id": 3,
                "question": "다중 분류에서 각 클래스별 확률의 합이 1이 되도록 변환해주는 함수는?",
                "choices": ["맥스 함수", "소프트맥스(Softmax) 함수", "로그 함수", "코사인 함수"],
                "answer": 1
            }
        ],
        8: [
            {
                "id": 1,
                "question": "데이터가 너무 커서 한 번에 학습하기 어려울 때, 조금씩 나누어 학습하는 방식은?",
                "choices": ["배치 학습", "점진적 학습 (확률적 경사 하강법)", "동시 학습", "수동 학습"],
                "answer": 1
            },
            {
                "id": 2,
                "question": "확률적 경사 하강법(SGD)에서 '경사 하강'의 의미는?",
                "choices": ["산에서 내려오는 것", "손실 함수의 값이 가장 낮은 곳을 향해 조금씩 수정해 나가는 것", "데이터의 값을 줄이는 것", "훈련 횟수를 줄이는 것"],
                "answer": 1
            },
            {
                "id": 3,
                "question": "훈련 데이터 전체를 한 번 모두 사용하는 단위를 무엇이라 하나요?",
                "choices": ["에포크(Epoch)", "스텝(Step)", "라운드(Round)", "사이클(Cycle)"],
                "answer": 0
            }
        ],
        9: [
            {
                "id": 1,
                "question": "결정 트리(Decision Tree) 모델의 가장 큰 장점은?",
                "choices": ["수학적으로 가장 복잡하다", "결과에 대한 이유를 사람이 이해하기 쉽다 (설명 가능성)", "데이터가 적으면 작동하지 않는다", "무조건 선형 회귀보다 좋다"],
                "answer": 1
            },
            {
                "id": 2,
                "question": "결정 트리가 데이터를 나눌 때 기준으로 사용하는 지표(순도 측정)는?",
                "choices": ["평균", "지니 불순도(Gini Impurity) 또는 엔트로피", "분산", "최댓값"],
                "answer": 1
            },
            {
                "id": 3,
                "question": "트리가 너무 깊어져 과적합되는 것을 막기 위해 가지를 치는 과정을 무엇이라 하나요?",
                "choices": ["분할", "가지치기(Pruning) / max_depth 설정", "데이터 삭제", "성장"],
                "answer": 1
            }
        ],
        10: [
            {
                "id": 1,
                "question": "여러 개의 결정 트리를 합쳐서 더 강력한 성능을 내는 기법은?",
                "choices": ["단일 트리", "앙상블 학습(Ensemble Learning)", "단순 분류", "데이터 통합"],
                "answer": 1
            },
            {
                "id": 2,
                "question": "랜덤 포레스트(Random Forest)가 훈련 데이터를 무작위로 샘플링하여 복원 추출하는 방식은?",
                "choices": ["부트스트랩(Bootstrap) 샘플", "랜덤 초이스", "중복 제거 샘플", "전체 샘플"],
                "answer": 0
            },
            {
                "id": 3,
                "question": "이전 트리가 틀린 부분을 다음 트리가 보완해나가며 점진적으로 성능을 높이는 방식의 앙상블 기법은?",
                "choices": ["그레이디언트 부스팅(Gradient Boosting)", "배깅", "단순 평균", "랜덤 트리"],
                "answer": 0
            }
        ],
        11: [
            {
                "id": 1,
                "question": "비지도 학습(Unsupervised Learning)과 지도 학습의 가장 결정적인 차이점은 무엇인가요?",
                "choices": ["사용하는 데이터가 더 많다", "정답(타깃 값)이 없는 데이터에서 스스로 패턴을 찾는다", "컴퓨터가 더 뜨거워진다", "결과가 항상 똑같다"],
                "answer": 1
            },
            {
                "id": 2,
                "question": "이미지 데이터를 분석할 때 '픽셀 평균'을 구하는 이유는 무엇인가요?",
                "choices": ["이미지의 전체적인 밝기나 색상 분포 등 특징을 수치화하기 위해", "이미지 용량을 줄이기 위해", "이미지를 더 선명하게 만들기 위해", "정답을 미리 알기 위해"],
                "answer": 0
            },
            {
                "id": 3,
                "question": "Numpy에서 두 값 사이의 차이를 양수로 변환하기 위해(오차 계산) 사용하는 함수는 무엇인가요?",
                "choices": ["np.sum", "np.mean", "np.abs", "np.sqrt"],
                "answer": 2
            }
        ],
        12: [
            {
                "id": 1,
                "question": "K-평균(K-Means) 알고리즘에서 각 군집의 중심점을 가리키는 용어는 무엇인가요?",
                "choices": ["포인트", "중간점", "센트로이드(Centroid)", "앵커"],
                "answer": 2
            },
            {
                "id": 2,
                "question": "최적의 군집 개수(K)를 찾기 위해, 이너셔가 급격히 줄어드는 지점을 찾는 방법은?",
                "choices": ["니(Knee) 방법", "엘보우(Elbow) 방법", "핑거(Finger) 방법", "숄더(Shoulder) 방법"],
                "answer": 1
            },
            {
                "id": 3,
                "question": "K-평균 알고리즘의 동작 순서로 옳은 것은?",
                "choices": ["중심 정하기 → 거리 계산 → 중심 이동 → 반복", "중심 정하기 → 정답 확인 → 학습 종료", "데이터 정렬 → 평균 계산 → 분류", "랜덤 분류 → 결과 확인 → 끝"],
                "answer": 0
            }
        ],
        13: [
            {
                "id": 1,
                "question": "주성분 분석(PCA)의 주요 목적이 아닌 것은?",
                "choices": ["데이터 차원 축소", "노이즈 제거 및 데이터 압축", "가장 중요한 특징(분산) 추출", "정답(Label) 자동 생성"],
                "answer": 3
            },
            {
                "id": 2,
                "question": "PCA를 사용하여 10,000개의 픽셀 데이터를 50개의 주성분으로 줄였을 때, 50개의 주성분은 무엇을 의미하나요?",
                "choices": ["원본 픽셀 중 가장 밝은 50개", "데이터의 변동성(분산)을 가장 잘 설명하는 새로운 50개의 축", "임의로 선택된 50개의 이미지 샘플", "가장 가운데에 위치한 50개의 픽셀"],
                "answer": 1
            },
            {
                "id": 3,
                "question": "사이킷런의 cross_validate 함수를 사용할 때, 별도의 설정을 하지 않으면 기본적으로 몇 개의 폴드(Fold)로 교차 검증을 수행하나요?",
                "choices": ["2개", "3개", "5개", "10개"],
                "answer": 2
            }
        ],
        15: [
            {
                "id": 1,
                "question": "층(Layer)이 깊어질수록 학습이 느려지는 문제를 해결하기 위해 현대 딥러닝에서 은닉층에 가장 많이 사용하는 활성화 함수는?",
                "choices": ["시그모이드(Sigmoid)", "소프트맥스(Softmax)", "ReLU", "탄젠트"],
                "answer": 2
            },
            {
                "id": 2,
                "question": "입력층과 출력층 사이에 위치하여 데이터의 복잡한 특징을 추출하는 층을 무엇이라 하나요?",
                "choices": ["입력층", "출력층", "은닉층(Hidden layer)", "평활층"],
                "answer": 2
            },
            {
                "id": 3,
                "question": "케라스에서 사용되는 옵티마이저 중, 적응적 학습률을 사용하며 가장 널리 권장되는 것은?",
                "choices": ["SGD", "Adam", "Momentum", "Nesterov"],
                "answer": 1
            }
        ],
        16: [
            {
                "id": 1,
                "question": "훈련 중 인공신경망의 일부 뉴런을 무작위로 끄는 기법으로, 과대적합을 방지하는 방법은 무엇인가요?",
                "choices": ["컴파일", "드롭아웃(Dropout)", "평탄화(Flatten)", "스케일링"],
                "answer": 1
            },
            {
                "id": 2,
                "question": "에포크마다 검증 점수를 확인하여 가장 좋은 성능의 가중치를 자동으로 저장해주는 기능은?",
                "choices": ["ModelCheckpoint", "EarlyStopping", "History", "Summary"],
                "answer": 0
            },
            {
                "id": 3,
                "question": "검증 손실이 더 이상 개선되지 않을 때 훈련을 미리 중단하여 자원을 아끼고 과대적합을 막는 기능은?",
                "choices": ["Dropout", "ModelCheckpoint", "EarlyStopping (조기 종료)", "Dense"],
                "answer": 2
            }
        ],
        17: [
            {
                "id": 1,
                "question": "합성곱 신경망(CNN)에서 입력 데이터의 특징을 추출하기 위해 사용하는 작은 행렬을 무엇이라 하나요?",
                "choices": ["필터(Filter) 또는 커널(Kernel)", "풀링(Pooling)", "패딩(Padding)", "스트라이드(Stride)"],
                "answer": 0
            },
            {
                "id": 2,
                "question": "특성 맵의 크기를 줄으면서 중요한 정보를 강조하고, 이동 불변성을 확보하기 위해 사용하는 층은?",
                "choices": ["합성곱 층", "풀링(Pooling) 층", "밀집층(Dense layer)", "출력층"],
                "answer": 1
            },
            {
                "id": 3,
                "question": "CNN 모델의 마지막 부분에서 다차원 특성 맵을 1차원 벡터로 펼쳐주는 층의 이름은 무엇인가요?",
                "choices": ["Dense", "Conv2D", "Flatten", "Dropout"],
                "answer": 2
            }
        ],
        18: [
            {
                "id": 1,
                "question": "학습된 합성곱 층의 가중치(필터)를 시각화했을 때, 밝은 부분은 무엇을 의미하나요?",
                "choices": ["가중치 값이 0에 가깝다", "해당 필터가 반응하지 않는 영역이다", "가중치 값이 높아서(양수) 해당 패턴을 강하게 포착한다", "이미지의 배경 부분이다"],
                "answer": 2
            },
            {
                "id": 2,
                "question": "입력 이미지가 합성곱 층과 활성화 함수를 통과하여 나온 결과물을 무엇이라 하나요?",
                "choices": ["필터", "가중치", "특성 맵(Feature Map)", "커널"],
                "answer": 2
            },
            {
                "id": 3,
                "question": "첫 번째 합성곱 층보다 뒤쪽(출력에 가까운) 합성곱 층의 특성 맵은 보통 어떤 특징을 가지나요?",
                "choices": ["원본 이미지와 더 비슷해진다", "점, 선 같은 단순한 특징만 보여준다", "더 추상적이고 복잡한 형태의 특징을 포착한다", "해상도가 더 높아진다"],
                "answer": 2
            }
        ]
    }

    @staticmethod
    def get_quiz(session_id):
        """강의별 퀴즈를 가져옴 (정답 제외하고 선택지 셔플 등 없이 원본 반환)"""
        return MLQuizService.QUIZ_DATA.get(session_id, [])

    @staticmethod
    def submit_answers(member_id, session_id, answers):
        """
        답안 제출 및 채점. 
        모두 맞아야만 quiz_progress 업데이트.
        answers: {question_id: selected_index}
        """
        quiz = MLQuizService.QUIZ_DATA.get(session_id, [])
        if not quiz:
            return False, "존재하지 않는 강의입니다."

        correct_count = 0
        for q in quiz:
            q_id = str(q['id'])
            if q_id in answers and int(answers[q_id]) == q['answer']:
                correct_count += 1
        
        is_all_correct = (correct_count == len(quiz))
        
        if is_all_correct:
            # DB 업데이트
            MLQuizService.update_progress(member_id, session_id)
            return True, "축하합니다! 모든 문제를 맞추어 합격하셨습니다."
        else:
            return False, f"아쉽네요. {len(quiz)}문제 중 {correct_count}문제를 맞추셨습니다. 다시 도전해보세요!"

    @staticmethod
    def get_progress(member_id):
        """사용자의 퀴즈 진행도 조회"""
        conn = Session.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT quiz_progress FROM members WHERE id = %s", (member_id,))
                row = cursor.fetchone()
                if row and row['quiz_progress']:
                    return json.loads(row['quiz_progress'])
                return {}
        finally:
            conn.close()

    @staticmethod
    def get_total_progress(member_id):
        """총 합격한 세션 개수 반환 (0~10)"""
        progress = MLQuizService.get_progress(member_id)
        return sum(1 for v in progress.values() if v is True)

    @staticmethod
    def update_progress(member_id, session_id):
        """합격 시 진행도 업데이트"""
        progress = MLQuizService.get_progress(member_id)
        # 이미 합격했어도 True로 갱신 (또는 유지)
        progress[str(session_id)] = True
        
        conn = Session.get_connection()
        try:
            with conn.cursor() as cursor:
                sql = "UPDATE members SET quiz_progress = %s WHERE id = %s"
                cursor.execute(sql, (json.dumps(progress), member_id))
                conn.commit()
                return True
        except Exception as e:
            print(f"Update progress error: {e}")
            return False
        finally:
            conn.close()
