from datetime import datetime, timedelta, timezone
import math

# 전역 변수로 필터 캐싱 (성능 최적화)
_banned_words_cache = None

def get_now_kst():
    """현재 한국 표준시(KST)를 naive datetime 객체로 반환합니다. (DB 저장 시 오차 방지)"""
    return datetime.now(timezone(timedelta(hours=9))).replace(tzinfo=None)

def check_profanity(text):
    """텍스트에 비속어/금지어가 포함되어 있는지 확인합니다."""
    global _banned_words_cache
    if not text: return True
    
    if _banned_words_cache is None:
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            profanity_file = os.path.join(base_dir, 'secrets', 'profanity.json')
            with open(profanity_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                banned_hex = data.get('ko', []) + data.get('en', [])
                _banned_words_cache = [bytes.fromhex(w).decode('utf-8') for w in banned_hex]
        except Exception as e:
            print(f"Profanity load error: {e}")
            _banned_words_cache = []

    clean_text = "".join(char for char in text if char.isalnum()).lower()
    text_lower = text.lower()
    for word in _banned_words_cache:
        if word in clean_text or word in text_lower:
            return False
    return True

def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def extract_gps_from_exif(image_path):
    """이미지 파일의 EXIF 메타데이터에서 GPS 위도/경도를 추출합니다."""
    try:
        from PIL import Image
        from PIL.ExifTags import TAGS, GPSTAGS
        import pillow_heif
        
        # HEIF/HEIC 지원 등록
        pillow_heif.register_heif_opener()
        
        img = Image.open(image_path)
        exif_data = img._getexif()
        if not exif_data:
            return None, None
        
        gps_info = {}
        for tag_id, value in exif_data.items():
            tag = TAGS.get(tag_id, tag_id)
            if tag == 'GPSInfo':
                for gps_tag_id in value:
                    gps_tag = GPSTAGS.get(gps_tag_id, gps_tag_id)
                    gps_info[gps_tag] = value[gps_tag_id]
        
        if not gps_info:
            return None, None
        
        def convert_to_degrees(value):
            d = float(value[0])
            m = float(value[1])
            s = float(value[2])
            return d + (m / 60.0) + (s / 3600.0)
        
        lat = convert_to_degrees(gps_info.get('GPSLatitude', (0, 0, 0)))
        lng = convert_to_degrees(gps_info.get('GPSLongitude', (0, 0, 0)))
        
        if gps_info.get('GPSLatitudeRef', 'N') == 'S':
            lat = -lat
        if gps_info.get('GPSLongitudeRef', 'E') == 'W':
            lng = -lng
        
        if lat == 0 and lng == 0:
            return None, None
        
        return lat, lng
    except Exception as e:
        print(f"EXIF GPS extraction error: {e}")
        return None, None

def haversine(lat1, lon1, lat2, lon2):
    """두 위도/경도 좌표 간의 거리를 미터(m) 단위로 계산합니다."""
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return float('inf')
        
    R = 6371000  # 지구 반지름 (미터)
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi/2) * math.sin(delta_phi/2) + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda/2) * math.sin(delta_lambda/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    return R * c

def reverse_geocode(lat, lng):
    """위도/경도를 도로명 주소로 변환합니다 (카카오 API)."""
    kakao_key = os.getenv('KAKAO_REST_API_KEY', '')
    if not kakao_key:
        return None
    try:
        url = f'https://dapi.kakao.com/v2/local/geo/coord2address.json?x={lng}&y={lat}'
        headers = {'Authorization': f'KakaoAK {kakao_key}'}
        resp = http_requests.get(url, headers=headers, timeout=5)
        data = resp.json()
        if data.get('documents'):
            doc = data['documents'][0]
            road = doc.get('road_address')
            if road and road.get('address_name'):
                return road['address_name']
            addr = doc.get('address')
            if addr and addr.get('address_name'):
                return addr['address_name']
    except Exception as e:
        print(f"Reverse geocode error: {e}")
    return None
