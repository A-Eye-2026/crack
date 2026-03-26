import os
import zipfile
import time

def create_deploy_package():
    source_dir = "."
    output_filename = "CRACK_FULL_DEPLOY_v1.0.zip"

    # 제외할 폴더 및 파일 명시 (최소화)
    # .venv는 너무 커서 제외하는 것이 일반적이나, 
    # 사용자가 "전체"를 원했으므로 고민되지만 .venv는 서버마다 환경이 다르므로 제외하고 
    # 대신 원클릭 스크립트에서 자동 생성하도록 함.
    # .git은 포함 요청이 있었으므로 제외 목록에서 제거.
    exclude_dirs = {'.venv', '__pycache__', '.vscode', 'node_modules', 'deploy', 'tmp'}
    exclude_exts = {'.zip', '.log', '.bak'}

    print(f"[*] Starting packaging: {output_filename}")
    
    # requirements.txt 업데이트
    core_reqs = [
        "Flask",
        "Flask-SQLAlchemy",
        "ultralytics",
        "Pillow",
        "piexif",
        "exifread",
        "pillow_heif",
        "python-dotenv",
        "PyMySQL",
        "certifi",
        "opencv-python",
        "numpy"
    ]
    with open("requirements.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(core_reqs))
    
    print("[*] requirements.txt regenerated.")

    with zipfile.ZipFile(output_filename, "w", zipfile.ZIP_DEFLATED) as ziph:
        for root, dirs, files in os.walk(source_dir):
            # .venv 등 제외 폴더 건너뛰기
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in exclude_exts:
                    continue
                # 자기 자신 제외
                if file == output_filename:
                    continue
                    
                filepath = os.path.join(root, file)
                arcname = os.path.relpath(filepath, source_dir)
                ziph.write(filepath, arcname)

    print(f"[*] Successfully created: {output_filename} ({os.path.getsize(output_filename) // (1024*1024)} MB)")
    print("[*] Includes: .git, .gitignore, secrets, uploads (media)")

if __name__ == "__main__":
    create_deploy_package()
