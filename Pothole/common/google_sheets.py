import gspread
import os
from oauth2client.service_account import ServiceAccountCredentials

class GoogleSheetClient:
    _client = None

    @classmethod
    def get_client(cls):
        """gspread 클라이언트 인스턴스 반환 (싱글톤)"""
        if cls._client is None:
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            key_path = os.environ.get('GOOGLE_SERVICE_ACCOUNT_PATH', '').strip()
            
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            
            print(f"[GoogleSheet] Path/Secret length: {len(key_path)}")
            
            # 1. 환경 변수 값이 JSON 문자열인 경우 (Vercel 배포용)
            if key_path.startswith('{') or key_path.startswith('"'):
                import json
                clean_json = key_path
                
                # 앞뒤에 따옴표가 있는 경우 ("{...}") 제거 및 역슬래시 이스케이프 복원
                if clean_json.startswith('"') and clean_json.endswith('"'):
                    print("[GoogleSheet] Removing outer double quotes from secret.")
                    clean_json = clean_json[1:-1].replace('\\"', '"').replace('\\\\', '\\')
                
                try:
                    key_data = json.loads(clean_json)
                    print(f"[GoogleSheet] JSON successfully parsed. Fields: {list(key_data.keys())}")
                except Exception as e:
                    print(f"[GoogleSheet] JSON Parse Error: {e}")
                    # 파싱 실패 시 마지막 수단으로 따옴표 그대로 시도
                    try:
                        key_data = json.loads(key_path)
                    except:
                        return f"JSON Parse Error: {str(e)} / Raw length: {len(key_path)}"

                # [v97] Base64/Key sanitization & Detailed checking
                if 'private_key' in key_data:
                    pk = key_data['private_key']
                    pk_len = len(pk)
                    # \n 문자열이 실제 줄바꿈이 아닌 리터럴로 들어온 경우 치환
                    pk = pk.replace('\\n', '\n').strip()
                    
                    print(f"[GoogleSheet] Private Key Length: {pk_len} -> {len(pk)}")
                    if len(pk) < 100:
                        print(f"[GoogleSheet] WARNING: Private key is suspiciously short! ({len(pk)} chars)")
                        # return False, f"Key too short ({len(pk)}). Truncated?"

                    # [v97] 보조: 만약 Base64 패딩 문제라면 (65 등 4의 배수가 아님) 강제로 시도할 수 있으나, 
                    # RSA 키는 PEM 형식이므로 보통 base64 라이브러리 내부에서 처리됨.
                    key_data['private_key'] = pk

                try:
                    creds = ServiceAccountCredentials.from_json_keyfile_dict(key_data, scope)
                    print("[GoogleSheet] Credentials created from dict.")
                except Exception as e:
                    import traceback
                    print(f"[GoogleSheet] Creds creation error: {e}")
                    traceback.print_exc()
                    # 에러 메시지에 상세 정보 포함하여 사용자에게 노출 (v97)
                    raise Exception(f"Base64/Key Format Error (Len: {len(key_data.get('private_key', ''))}): {str(e)}")
            else:
                # 2. 파일 경로인 경우
                if key_path and not os.path.isabs(key_path):
                    key_path = os.path.join(base_path, key_path)
                if not key_path or not os.path.exists(key_path):
                    key_path = os.path.join(base_path, 'secrets', 'typing_key.json')
                
                print(f"[GoogleSheet] Using key file: {key_path}")
                creds = ServiceAccountCredentials.from_json_keyfile_name(key_path, scope)
            
            cls._client = gspread.authorize(creds)
            print("[GoogleSheet] Client authorized.")
        return cls._client

    @classmethod
    def get_sheet_all_rows(cls, sheet_name, worksheet_index=0):
        """특정 시트의 모든 행 데이터를 반환"""
        client = cls.get_client()
        sheet = client.open(sheet_name)
        worksheet = sheet.get_worksheet(worksheet_index)
        return worksheet.get_all_values()
