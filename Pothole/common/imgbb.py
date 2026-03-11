import requests
import base64
import os

IMGBB_API_KEYS = [
    'e17d73dfd48e881bdf0cb1509d042a8d',
    '62725dbc29482daf6cee98f00c262122'
]

def upload_to_imgbb(file_data):
    """
    이미지 데이터를 ImgBB에 업로드하고 URL을 반환합니다.
    file_data: 바이너리 데이터 또는 파일 객체
    """
    url = "https://api.imgbb.com/1/upload"
    
    # 바이너리 데이터를 base64로 인코딩
    if hasattr(file_data, 'read'):
        data = file_data.read()
    else:
        data = file_data
        
    base64_image = base64.b64encode(data)
    
    for key in IMGBB_API_KEYS:
        try:
            payload = {
                "key": key,
                "image": base64_image,
            }
            response = requests.post(url, payload)
            if response.status_code == 200:
                result = response.json()
                return result['data']['url']
            else:
                print(f"[ImgBB] 키 {key[:5]}... 실패: {response.text}")
        except Exception as e:
            print(f"[ImgBB] 업로드 중 오류: {e}")
            
    return None
