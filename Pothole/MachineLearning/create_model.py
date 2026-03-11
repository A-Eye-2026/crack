
import tensorflow as tf
from tensorflow import keras
from sklearn.model_selection import train_test_split

def create_and_save_model():
    # 1. 데이터 준비
    (train_input, train_target), (test_input, test_target) = keras.datasets.fashion_mnist.load_data()
    train_scaled = train_input.reshape(-1, 28, 28, 1) / 255.0
    
    train_scaled, val_scaled, train_target, val_target = train_test_split(
        train_scaled, train_target, test_size=0.2, random_state=42)

    # 2. 모델 구성 (노트북 17강 기준)
    model = keras.Sequential()
    model.add(keras.layers.Conv2D(32, kernel_size=3, activation='relu', padding='same', input_shape=(28,28,1)))
    model.add(keras.layers.MaxPooling2D(2))
    model.add(keras.layers.Conv2D(64, kernel_size=3, activation='relu', padding='same'))
    model.add(keras.layers.MaxPooling2D(2))
    model.add(keras.layers.Flatten())
    model.add(keras.layers.Dense(100, activation='relu'))
    model.add(keras.layers.Dropout(0.4))
    model.add(keras.layers.Dense(10, activation='softmax'))

    # 3. 컴파일 및 훈련
    model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])
    
    # 시간 절약을 위해 에포크를 적게 설정 (시각화 목적이므로)
    model.fit(train_scaled, train_target, epochs=5, validation_data=(val_scaled, val_target))

    # 4. 저장
    model.save('best-cnn-model.keras')
    print("Model saved as best-cnn-model.keras")

if __name__ == "__main__":
    create_and_save_model()
