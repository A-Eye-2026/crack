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

try:
    from PIL import Image
    from PIL.ExifTags import TAGS, GPSTAGS
    import pillow_heif
    # HEIF/HEIC 지원 글로벌 등록 (사용자 피드백 수용: 시점 문제 해결)
    pillow_heif.register_heif_opener()
except ImportError:
    pass

def extract_gps_from_exif(image_path):
    """이미지 파일의 EXIF 메타데이터에서 GPS 위도/경도를 추출합니다.
    다양한 EXIF 구조(IFD, Legacy 등)에 대응하며, 서버 재기동 후에도 안정적으로 작동하도록 설계되었습니다.
    """
    try:
        from PIL import Image
        from PIL.ExifTags import TAGS, GPSTAGS
        import os
        
        # [HEIF RE-CHECK] 서버 재시작 후 초기화 누락 방지 (방어적 코드)
        try:
            from pillow_heif import register_heif_opener
            register_heif_opener()
        except ImportError:
            pass

        if not os.path.exists(image_path):
            print(f"[GPS] File not found: {image_path}")
            return None, None

        img = Image.open(image_path)
        
        # 1. Modern API: getexif()
        exif = img.getexif()
        gps_info = {}
        
        if exif:
            # GPS IFD (0x8825)
            gps_ifd = exif.get_ifd(0x8825)
            if gps_ifd:
                print(f"[GPS] Found GPS IFD (0x8825) in {os.path.basename(image_path)}")
                for tag_id, value in gps_ifd.items():
                    tag = GPSTAGS.get(tag_id, tag_id)
                    gps_info[tag] = value

        # 2. Legacy API Fallback: _getexif()
        if not gps_info and hasattr(img, '_getexif'):
            exif_legacy = img._getexif()
            if exif_legacy:
                print(f"[GPS] Searching Legacy EXIF (JPEG) for {os.path.basename(image_path)}")
                for tag_id, value in exif_legacy.items():
                    tag = TAGS.get(tag_id, tag_id)
                    if tag == 'GPSInfo':
                        for gps_tag_id in value:
                            gps_tag = GPSTAGS.get(gps_tag_id, gps_tag_id)
                            gps_info[gps_tag] = value[gps_tag_id]

        if not gps_info:
            # 3. Last Resort: Check all IFDs in getexif() manually if not found in 0x8825
            if exif:
                for tag_id in exif:
                    tag_name = TAGS.get(tag_id, tag_id)
                    if tag_name == 'GPSInfo':
                        val = exif.get(tag_id)
                        if isinstance(val, dict):
                            print(f"[GPS] Found GPSInfo via tag name fallback")
                            for k, v in val.items():
                                gps_tag = GPSTAGS.get(k, k)
                                gps_info[gps_tag] = v

        if not gps_info:
            print(f"[GPS] No GPS info found in any EXIF structure for {os.path.basename(image_path)}")
            return None, None
        
        # [디버그] GPS 원본 데이터 구조 확인 (문제 진단용)
        print(f"[GPS] Raw GPS data keys: {list(gps_info.keys())}")
        raw_lat = gps_info.get('GPSLatitude')
        raw_lng = gps_info.get('GPSLongitude')
        print(f"[GPS] Raw GPSLatitude: {raw_lat} (type: {type(raw_lat).__name__})")
        print(f"[GPS] Raw GPSLongitude: {raw_lng} (type: {type(raw_lng).__name__})")
        if raw_lat and hasattr(raw_lat, '__iter__') and not isinstance(raw_lat, str):
            for i, v in enumerate(raw_lat):
                print(f"[GPS]   lat[{i}] = {v} (type: {type(v).__name__})")
        
        def convert_to_degrees(value):
            if value is None: return 0.0
            
            import math
            
            # Case 1: 이미 단일 부동소수점 (Pillow 12.x에서 IFDRational이 float처럼 동작)
            if isinstance(value, (int, float)):
                return 0.0 if math.isnan(value) or math.isinf(value) else float(value)
            
            def to_f(v):
                # IFDRational: float()로 변환 가능 (Pillow 7+)
                try:
                    f = float(v)
                    if math.isnan(f) or math.isinf(f):
                        return 0.0
                    if f != 0:
                        return f
                except (ValueError, TypeError):
                    pass
                # Rational 형태: numerator/denominator 속성
                if hasattr(v, 'numerator') and hasattr(v, 'denominator'):
                    if v.denominator == 0:
                        return 0.0
                    return float(v.numerator) / float(v.denominator)
                # (numerator, denominator) 튜플 형태
                if isinstance(v, (list, tuple)) and len(v) == 2:
                    if v[1] == 0:
                        return 0.0
                    return float(v[0]) / float(v[1])
                return float(v)

            try:
                if not hasattr(value, '__iter__') or isinstance(value, str):
                    return float(value)
                
                parts = list(value)
                if len(parts) == 3:
                    d = to_f(parts[0])
                    m = to_f(parts[1])
                    s = to_f(parts[2])
                    # NaN이 하나라도 있으면 전체가 무효
                    if any(math.isnan(x) for x in [d, m, s]):
                        print(f"[GPS]   DMS contains NaN: d={d}, m={m}, s={s}")
                        return 0.0
                    result = d + (m / 60.0) + (s / 3600.0)
                    print(f"[GPS]   DMS conversion: {d}° {m}' {s}\" = {result}")
                    return result
                elif len(parts) == 1:
                    return to_f(parts[0])
                else:
                    return 0.0
            except Exception as e:
                print(f"[GPS]   convert_to_degrees error: {e}")
                return 0.0
        
        lat = convert_to_degrees(gps_info.get('GPSLatitude'))
        lng = convert_to_degrees(gps_info.get('GPSLongitude'))
        
        lat_ref = gps_info.get('GPSLatitudeRef', 'N')
        lng_ref = gps_info.get('GPSLongitudeRef', 'E')
        
        if lat_ref == 'S': lat = -lat
        if lng_ref == 'W': lng = -lng
        
        if lat == 0 and lng == 0:
            print(f"[GPS] Extracted coordinates are zero (0,0) - likely invalid.")
            return None, None
            
        print(f"[GPS] SUCCESS: {lat}, {lng} extracted from {os.path.basename(image_path)}")
        return lat, lng
    except Exception as e:
        import traceback
        print(f"[GPS] Extraction Error: {e}")
        traceback.print_exc()
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
