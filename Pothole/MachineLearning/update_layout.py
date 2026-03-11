import os

html_path = r'C:\Users\수빈36\Desktop\플라스크\LMS\MachineLearning\templates\ml_layout.html'

with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Remove const SESSION_CODES = { ... };
start_idx = html.find('const SESSION_CODES = {')
if start_idx != -1:
    end_idx = html.find('};\n', start_idx) + 3
    # Check if switchDataTab is right after
    html = html[:start_idx] + html[end_idx:]

# 2. Inject CSS
if '.code-output' not in html:
    style_end = html.find('</style>')
    if style_end != -1:
        css = """
    .code-output {
        font-family: var(--font-tech), 'Fira Code', monospace;
        color: #d35400;
        background-color: #fff9f5;
        border-left: 4px solid #e67e22;
        padding: 12px 18px;
        margin: 5px 0 15px 15px;
        border-radius: 6px;
        font-size: 0.95rem;
        font-weight: 500;
        white-space: pre-wrap;
        box-shadow: 0 4px 10px rgba(0,0,0,0.03);
        word-break: break-all;
    }
"""
        html = html[:style_end] + css + html[style_end:]

# 3. Replace toggleCodeModal
toggle_start = html.find('function toggleCodeModal() {')
toggle_end = html.find('function updateSigmoidLab() {')
if toggle_start != -1 and toggle_end != -1:
    new_toggle = """function formatCodeHTML(text) {
        const lines = text.split('\\n');
        const container = document.createElement('div');
        let currentCode = [];
        let currentOutput = [];
        
        const flushCode = () => {
            if (currentCode.length > 0) {
                const pre = document.createElement('pre');
                pre.className = "bg-light p-3 rounded-3 border mb-2 mt-2";
                pre.style.fontSize = "0.95rem";
                pre.style.whiteSpace = "pre-wrap";
                pre.style.wordBreak = "break-all";
                
                const code = document.createElement('code');
                code.className = "language-python";
                let escaped = currentCode.join('\\n').replace(/</g, "&lt;").replace(/>/g, "&gt;");
                escaped = escaped.replace(/\\*\\*(.*?)\\*\\*/g, "<strong class='text-danger'>$1</strong>");
                code.innerHTML = escaped;
                
                pre.appendChild(code);
                if (window.hljs) hljs.highlightElement(code);
                container.appendChild(pre);
                currentCode = [];
            }
        };
        
        const flushOutput = () => {
            if (currentOutput.length > 0) {
                const outDiv = document.createElement('div');
                outDiv.className = "code-output";
                outDiv.innerText = currentOutput.join('\\n').trim();
                container.appendChild(outDiv);
                currentOutput = [];
            }
        };
        
        for (let i = 0; i < lines.length; i++) {
            let line = lines[i];
            if (line.trim() === '') {
                if (currentOutput.length > 0) currentOutput.push(line);
                else currentCode.push(line);
                continue;
            }
            
            const trimmed = line.trim();
            let isOutput = false;
            // 배열, 괄호 등 아웃풋의 흔한 형태
            if (trimmed.startsWith('[')) isOutput = true;
            else if (trimmed.startsWith('(')) isOutput = true;
            else if (trimmed.startsWith('array(')) isOutput = true;
            else if (trimmed.startsWith('▾')) isOutput = true;
            else if (/^[-+]?\d*\.?\d+$/.test(trimmed)) isOutput = true; 
            else if (trimmed === '?' || trimmed === 'i') isOutput = true; 
            else if (/^(KNeighbors|LinearRegression|Ridge|Lasso|ExtraTrees|GradientBoosting|HistGradientBoosting|XGBClassifier|LGBMClassifier)/.test(trimmed)) isOutput = true;
            else if (/^(train_score|test_score)/.test(trimmed)) isOutput = true;
            
            let isCode = false;
            if (trimmed.startsWith('print(')) isCode = true;
            else if (trimmed.startsWith('import ')) isCode = true;
            else if (trimmed.startsWith('from ')) isCode = true;
            else if (trimmed.startsWith('!')) isCode = true; 
            else if (/^[a-zA-Z0-9_]+\s*=/.test(trimmed)) isCode = true; 
            else if (/^[a-zA-Z_]\w*\./.test(trimmed)) isCode = true; 
            else if (trimmed.startsWith('plt.')) isCode = true;
            else if (trimmed.startsWith('kn')) isCode = true;
            else if (trimmed.startsWith('lr')) isCode = true;
            else if (trimmed.startsWith('ridge')) isCode = true;
            else if (trimmed.startsWith('lasso')) isCode = true;
            else if (trimmed.startsWith('et')) isCode = true;
            else if (trimmed.startsWith('gb')) isCode = true;
            else if (trimmed.startsWith('hgb')) isCode = true;
            else if (trimmed.startsWith('xgb')) isCode = true;
            else if (trimmed.startsWith('lgb')) isCode = true;
            else if (trimmed.startsWith('result ')) isCode = true;
            else if (trimmed.startsWith('poly ')) isCode = true;
            else if (trimmed.startsWith('distances')) isCode = true;
            else if (trimmed.startsWith('mean')) isCode = true;
            else if (trimmed.startsWith('std')) isCode = true;
            else if (trimmed.startsWith('train_')) isCode = true;
            else if (trimmed.startsWith('test_')) isCode = true;
            else if (trimmed.startsWith('point ')) isCode = true;
            
            if (isCode) {
                flushOutput();
                currentCode.push(line);
            } else if (isOutput) {
                flushCode();
                currentOutput.push(line);
            } else {
                if (currentOutput.length > 0) currentOutput.push(line);
                else currentCode.push(line);
            }
        }
        flushCode();
        flushOutput();
        
        return container;
    }

    function toggleCodeModal() {
        const overlay = document.getElementById('codeModalOverlay');
        if (overlay) {
            if (overlay.style.display === 'flex') {
                gsap.to(overlay, { opacity: 0, duration: 0.2 });
                gsap.to(overlay.querySelector('.raw-data-modal'), { scale: 0.95, opacity: 0, duration: 0.2, onComplete: () => overlay.style.display = 'none' });
            } else {
                overlay.style.display = 'flex';
                gsap.to(overlay, { opacity: 1, duration: 0.3 });
                gsap.fromTo(overlay.querySelector('.raw-data-modal'), { scale: 0.95, opacity: 0 }, { scale: 1, opacity: 1, duration: 0.3, ease: 'back.out(1.5)' });

                const session_id = parseInt(window.location.pathname.split('/').pop());
                const modalBody = document.getElementById('code-modal-body');

                modalBody.innerHTML = '<div class="text-center py-4"><div class="spinner-border text-primary"></div><p class="mt-2 text-muted">분석 코드를 불러오는 중입니다...</p></div>';

                fetch(`/ml_static/codes/session_${session_id}.txt`)
                    .then(res => {
                        if (!res.ok) throw new Error('File not found');
                        return res.text();
                    })
                    .then(text => {
                        modalBody.innerHTML = '';
                        const blockTitle = document.createElement('h6');
                        blockTitle.className = "fw-bold text-primary mt-3 mb-2";
                        blockTitle.innerText = `🔹 ${session_id}강 파이썬 코드 보기 (Python 3.12 환경)`;
                        modalBody.appendChild(blockTitle);
                        
                        modalBody.appendChild(formatCodeHTML(text));
                    })
                    .catch(e => {
                        modalBody.innerHTML = `<p class="text-muted text-center py-4">해당 강의(세션 ${session_id})에 등록된 코드가 없거나 로딩을 실패했습니다.</p>`;
                    });
            }
        }
    }

    """
    html = html[:toggle_start] + new_toggle + html[toggle_end:]

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html)
print("Updated ml_layout.html successfully!")
