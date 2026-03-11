import cloudinary
import cloudinary.uploader
import os
from dotenv import load_dotenv

# 로컬 실행 시를 위해 .env 로드 (api/index.py에서 이미 되어 있을 수 있음)
load_dotenv('secrets/.env')

# Cloudinary 설정
cloudinary.config(
    cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME'),
    api_key=os.environ.get('CLOUDINARY_API_KEY'),
    api_secret=os.environ.get('CLOUDINARY_API_SECRET'),
    secure=True
)

def upload_to_cloudinary(file_data):
    """
    이미지 데이터를 Cloudinary에 업로드하고 secure_url을 반환합니다.
    file_data: 바이너리 데이터
    """
    try:
        if not file_data:
            return None
            
        # Cloudinary 업로드 호출
        upload_result = cloudinary.uploader.upload(
            file_data,
            folder="lms_items",  # 폴더 지정 가능
            resource_type="auto"
        )
        
        return upload_result.get('secure_url')
    except Exception as e:
        print(f"[Cloudinary] Upload Error: {e}")
        return None
