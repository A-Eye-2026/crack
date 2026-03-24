import os
import zipfile
import time

def create_deploy_package():
    source_dir = "."
    output_filename = f"CRACK_PORTABLE_v1.3.5.zip"

    # 제외할 폴더 및 파일 명시
    exclude_dirs = {'.git', '.venv', '__pycache__', '.vscode', 'node_modules', 'deploy'}
    exclude_exts = {'.zip', '.log', '.bak'}

    print(f"[*] Starting packaging: {output_filename}")
    
    # requirements.txt 명시적 업데이트 (원클릭 환경을 위한 의존성 정리)
    # pip freeze의 지저분한 종속성 대신 핵심 모듈만 명시 (나머지는 pip가 자동 해결)
    core_reqs = [
        "Flask",
        "ultralytics",
        "Pillow",
        "piexif",
        "exifread",
        "pillow_heif",
        "python-dotenv",
        "PyMySQL",
        "certifi"
    ]
    with open("requirements.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(core_reqs))
    
    print("[*] requirements.txt explicitly regenerated for clean deployment.")

    with zipfile.ZipFile(output_filename, "w", zipfile.ZIP_DEFLATED) as ziph:
        for root, dirs, files in os.walk(source_dir):
            if root == source_dir:
                dirs[:] = [d for d in dirs if d not in exclude_dirs]
            else:
                # 하위 폴더 탐색 시에도 제외 폴더 거름
                dirs[:] = [d for d in dirs if not any(ex in root for ex in exclude_dirs)]
            
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in exclude_exts:
                    continue
                # 자기 자신 제외
                if file == output_filename:
                    continue
                if file == "create_package.py":
                    continue
                    
                filepath = os.path.join(root, file)
                arcname = os.path.relpath(filepath, source_dir)
                ziph.write(filepath, arcname)

    print(f"[*] Successfully created: {output_filename} ({os.path.getsize(output_filename) // (1024*1024)} MB)")
    print("[*] Ready for deployment.")

if __name__ == "__main__":
    create_deploy_package()
