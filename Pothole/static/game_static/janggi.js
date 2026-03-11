/**
 * janggi.js - 한국 장기 게임 엔진 + AI (미니맥스 + 알파-베타 가지치기)
 * v2 - 전통 보드 디자인 + 웹오디오 효과음
 */

// ── 기물 이미지 프리로딩 최적화 ─────────────────────
const JANGGI_SVG_ASSETS = [
    'king_b.svg', 'guard_b.svg', 'elephant_b.svg', 'horse_b.svg', 'rook_b.svg', 'cannon_b.svg', 'pawn_b.svg',
    'king_r.svg', 'guard_r.svg', 'elephant_r.svg', 'horse_r.svg', 'rook_r.svg', 'cannon_r.svg', 'pawn_r.svg'
];
const preloadedImages = {};
// 브라우저 초기 로드 시 이미지 메모리 적재 (깜빡임 방지)
JANGGI_SVG_ASSETS.forEach(name => {
    const img = new Image();
    img.src = `/game/static/images/janggi/${name}`;
    preloadedImages[name] = img;
});

// ── 기물 상수 ──────────────────────────────────────────
const EMPTY = 0;
const P_KING = 1;  // 楚 (플레이어, 아래)
const P_GUARD = 2;  // 士
const P_ELEPH = 3;  // 象
const P_HORSE = 4;  // 馬
const P_CART = 5;  // 車
const P_CANNON = 6;  // 包
const P_PAWN = 7;  // 卒

const H_KING = -1; // 漢 (AI, 위)
const H_GUARD = -2;
const H_ELEPH = -3;
const H_HORSE = -4;
const H_CART = -5;
const H_CANNON = -6;
const H_PAWN = -7; // 兵

const PIECE_VALUE = { 1: 10000, 2: 300, 3: 350, 4: 400, 5: 900, 6: 700, 7: 100 };

// 한/초 기물 한자 표기 구분
const PIECE_CHARS_CHO = {
    [P_KING]: '楚', [P_GUARD]: '士', [P_ELEPH]: '象', [P_HORSE]: '馬',
    [P_CART]: '車', [P_CANNON]: '包', [P_PAWN]: '卒'
};
const PIECE_CHARS_HAN = {
    [H_KING]: '漢', [H_GUARD]: '士', [H_ELEPH]: '象', [H_HORSE]: '馬',
    [H_CART]: '車', [H_CANNON]: '包', [H_PAWN]: '兵'
};

function getPieceChar(p) {
    if (p > 0) return PIECE_CHARS_CHO[p];
    if (p < 0) return PIECE_CHARS_HAN[p];
    return '';
}

function inBounds(r, c) { return r >= 0 && r < 10 && c >= 0 && c < 9; }
function isChoSide(p) { return p > 0; }
function isHanSide(p) { return p < 0; }
function inHanPalace(r, c) { return r <= 2 && c >= 3 && c <= 5; }
function inChoPalace(r, c) { return r >= 7 && c >= 3 && c <= 5; }

function createInitialBoard(choForm = 'ma-sang-ma-sang', hanForm = 'ma-sang-ma-sang') {
    const b = Array.from({ length: 10 }, () => Array(9).fill(0));

    // 한 (AI, 위)
    b[0][0] = H_CART; b[0][8] = H_CART;
    b[0][3] = H_GUARD; b[0][5] = H_GUARD;
    b[1][4] = H_KING;
    b[2][1] = H_CANNON; b[2][7] = H_CANNON;
    b[3][0] = H_PAWN; b[3][2] = H_PAWN; b[3][4] = H_PAWN; b[3][6] = H_PAWN; b[3][8] = H_PAWN;

    // 한 포메이션 설정
    if (hanForm === 'ma-sang-ma-sang') { b[0][1] = H_HORSE; b[0][2] = H_ELEPH; b[0][6] = H_HORSE; b[0][7] = H_ELEPH; }
    else if (hanForm === 'sang-ma-sang-ma') { b[0][1] = H_ELEPH; b[0][2] = H_HORSE; b[0][6] = H_ELEPH; b[0][7] = H_HORSE; }
    else if (hanForm === 'ma-sang-sang-ma') { b[0][1] = H_HORSE; b[0][2] = H_ELEPH; b[0][6] = H_ELEPH; b[0][7] = H_HORSE; }
    else if (hanForm === 'sang-ma-ma-sang') { b[0][1] = H_ELEPH; b[0][2] = H_HORSE; b[0][6] = H_HORSE; b[0][7] = H_ELEPH; }

    // 초 (플레이어, 아래)
    b[9][0] = P_CART; b[9][8] = P_CART;
    b[9][3] = P_GUARD; b[9][5] = P_GUARD;
    b[8][4] = P_KING;
    b[7][1] = P_CANNON; b[7][7] = P_CANNON;
    b[6][0] = P_PAWN; b[6][2] = P_PAWN; b[6][4] = P_PAWN; b[6][6] = P_PAWN; b[6][8] = P_PAWN;

    // 초 포메이션 설정
    if (choForm === 'ma-sang-ma-sang') { b[9][1] = P_HORSE; b[9][2] = P_ELEPH; b[9][6] = P_HORSE; b[9][7] = P_ELEPH; }
    else if (choForm === 'sang-ma-sang-ma') { b[9][1] = P_ELEPH; b[9][2] = P_HORSE; b[9][6] = P_ELEPH; b[9][7] = P_HORSE; }
    else if (choForm === 'ma-sang-sang-ma') { b[9][1] = P_HORSE; b[9][2] = P_ELEPH; b[9][6] = P_ELEPH; b[9][7] = P_HORSE; }
    else if (choForm === 'sang-ma-ma-sang') { b[9][1] = P_ELEPH; b[9][2] = P_HORSE; b[9][6] = P_HORSE; b[9][7] = P_ELEPH; }

    return b;
}

function cloneBoard(b) { return b.map(r => [...r]); }

function canCapture(board, r, c, side) {
    if (!inBounds(r, c)) return false;
    const t = board[r][c];
    if (t === EMPTY) return true;
    return side > 0 ? isHanSide(t) : isChoSide(t);
}

// ── 이동 생성 (이전과 동일한 로직) ─────────────────────
function kingMoves(board, r, c, piece) {
    const moves = [];
    const palFn = isChoSide(piece) ? inChoPalace : inHanPalace;
    const side = isChoSide(piece) ? 1 : -1;
    const diagCells = [[7, 3], [7, 5], [8, 4], [9, 3], [9, 5], [0, 3], [0, 5], [1, 4], [2, 3], [2, 5]];
    const hasDiag = diagCells.some(([dr, dc]) => dr === r && dc === c);
    const dirs = hasDiag ? [[-1, 0], [1, 0], [0, -1], [0, 1], [-1, -1], [-1, 1], [1, -1], [1, 1]] : [[-1, 0], [1, 0], [0, -1], [0, 1]];
    for (const [dr, dc] of dirs) {
        const nr = r + dr, nc = c + dc;
        if (palFn(nr, nc) && canCapture(board, nr, nc, side)) moves.push([r, c, nr, nc]);
    }
    return moves;
}
function guardMoves(board, r, c, piece) { return kingMoves(board, r, c, piece); }

function cartMoves(board, r, c, piece) {
    const moves = []; const side = isChoSide(piece) ? 1 : -1;
    // 기본 직선 이동
    for (const [dr, dc] of [[-1, 0], [1, 0], [0, -1], [0, 1]]) {
        let nr = r + dr, nc = c + dc;
        while (inBounds(nr, nc)) {
            const t = board[nr][nc];
            if (t === EMPTY) { moves.push([r, c, nr, nc]); }
            else { if (canCapture(board, nr, nc, side)) moves.push([r, c, nr, nc]); break; }
            nr += dr; nc += dc;
        }
    }
    // 궁내 대각선 이동
    const diagMap = {
        "0,3": [[1, 4], [2, 5]], "0,5": [[1, 4], [2, 3]],
        "2,3": [[1, 4], [0, 5]], "2,5": [[1, 4], [0, 3]],
        "1,4": [[0, 3], [0, 5], [2, 3], [2, 5]],
        "7,3": [[8, 4], [9, 5]], "7,5": [[8, 4], [9, 3]],
        "9,3": [[8, 4], [7, 5]], "9,5": [[8, 4], [7, 3]],
        "8,4": [[7, 3], [7, 5], [9, 3], [9, 5]]
    };
    const targets = diagMap[`${r},${c}`];
    if (targets) {
        for (const [tr, tc] of targets) {
            // 차는 대각선으로 장애물 전까지 한 번에 이동 가능 (이 엔진은 인접 칸만 체크 후 확장)
            // 여기서는 단순성을 위해 인접 대각선 칸만 체크 (1.4 등 거쳐가는 경우 포함)
            const dr = tr - r, dc = tc - c;
            const nr = r + Math.sign(dr), nc = c + Math.sign(dc);
            if (board[nr][nc] === EMPTY || (nr === tr && nc === tc && canCapture(board, nr, nc, side))) {
                moves.push([r, c, tr, tc]);
            }
        }
    }
    return moves;
}

function cannonMoves(board, r, c, piece) {
    const moves = []; const side = isChoSide(piece) ? 1 : -1;
    // 기본 직선 이동
    for (const [dr, dc] of [[-1, 0], [1, 0], [0, -1], [0, 1]]) {
        let nr = r + dr, nc = c + dc; let found = false;
        while (inBounds(nr, nc)) {
            const t = board[nr][nc];
            if (!found) {
                if (t !== EMPTY) {
                    if (Math.abs(t) === P_CANNON) break;
                    found = true;
                }
            }
            else {
                if (t !== EMPTY) {
                    if (Math.abs(t) !== P_CANNON && canCapture(board, nr, nc, side)) moves.push([r, c, nr, nc]);
                    break;
                }
                else moves.push([r, c, nr, nc]);
            }
            nr += dr; nc += dc;
        }
    }
    // 궁내 대각선 이동 (포)
    const palaceCornerMap = {
        "0,3": [2, 5], "0,5": [2, 3], "2,3": [0, 5], "2,5": [0, 3],
        "7,3": [9, 5], "7,5": [9, 3], "9,3": [7, 5], "9,5": [7, 3]
    };
    if (palaceCornerMap[`${r},${c}`]) {
        const [tr, tc] = palaceCornerMap[`${r},${c}`];
        const midR = (r + tr) / 2, midC = (c + tc) / 2;
        const bridge = board[midR][midC];
        if (bridge !== EMPTY && Math.abs(bridge) !== P_CANNON) {
            const target = board[tr][tc];
            if (target === EMPTY || (Math.abs(target) !== P_CANNON && canCapture(board, tr, tc, side))) {
                moves.push([r, c, tr, tc]);
            }
        }
    }
    return moves;
}

function horseMoves(board, r, c, piece) {
    const moves = []; const side = isChoSide(piece) ? 1 : -1;
    // [직선_이동, [최종_이동_1, 최종_이동_2]]
    const steps = [
        [[-1, 0], [[-2, -1], [-2, 1]]], // 위
        [[1, 0], [[2, -1], [2, 1]]],   // 아래
        [[0, -1], [[-1, -2], [1, -2]]], // 왼쪽
        [[0, 1], [[-1, 2], [1, 2]]]    // 오른쪽
    ];
    for (const [orth, diags] of steps) {
        const mr = r + orth[0], mc = c + orth[1];
        // 멱(발목): 첫 번째 직선 경로가 비어있어야 함
        if (!inBounds(mr, mc) || board[mr][mc] !== EMPTY) continue;
        for (const [fr, fc] of diags) {
            const tr = r + fr, tc = c + fc;
            if (inBounds(tr, tc) && canCapture(board, tr, tc, side)) {
                moves.push([r, c, tr, tc]);
            }
        }
    }
    return moves;
}

function elephMoves(board, r, c, piece) {
    const moves = []; const side = isChoSide(piece) ? 1 : -1;
    // 상: 직선 1칸 -> 대각선 2칸. 멱은 1단계(직선), 2단계(첫 대각선)
    const steps = [
        [[-1, 0], [[-2, -1], [-3, -2]], [[-2, 1], [-3, 2]]], // 위
        [[1, 0], [[2, -1], [3, -2]], [[2, 1], [3, 2]]],   // 아래
        [[0, -1], [[-1, -2], [-2, -3]], [[1, -2], [2, -3]]], // 왼쪽
        [[0, 1], [[-1, 2], [-2, 3]], [[1, 2], [2, 3]]]    // 오른쪽
    ];
    for (const [orth, ...paths] of steps) {
        // 1차 멱 (직선 1칸)
        const or = r + orth[0], oc = c + orth[1];
        if (!inBounds(or, oc) || board[or][oc] !== EMPTY) continue;

        for (const path of paths) {
            const [m1, target] = path;
            const m1r = r + m1[0], m1c = c + m1[1];
            // 2차 멱 (대각선 1칸 지점)
            if (!inBounds(m1r, m1c) || board[m1r][m1c] !== EMPTY) continue;

            const tr = r + target[0], tc = c + target[1];
            if (inBounds(tr, tc) && canCapture(board, tr, tc, side)) {
                moves.push([r, c, tr, tc]);
            }
        }
    }
    return moves;
}

/**
 * 졸(卒/兵) 이동: 전진, 좌우 이동 가능.
 * 궁성 내 대각선 규칙 추가: 궁성 대각선 라인에 있을 때 전진 방향 대각선 이동 가능.
 * (주의: 본 엔진은 외부 라이브러리 없이 직접 제작된 엔진으로, 누락되었던 정통 규칙을 보완합니다.)
 */
function pawnMoves(board, r, c, piece) {
    const moves = []; const side = isChoSide(piece) ? 1 : -1;
    const fwd = side > 0 ? -1 : 1;

    // 기본 이동: 전진, 좌, 우
    for (const [dr, dc] of [[fwd, 0], [0, -1], [0, 1]]) {
        const nr = r + dr, nc = c + dc;
        if (inBounds(nr, nc) && canCapture(board, nr, nc, side)) moves.push([r, c, nr, nc]);
    }

    // 궁성 내 대각선 전진 이동
    if (side > 0) { // 초(Cho) - 위로 이동 (한나라 궁성 진입 시)
        if (r === 2 && c === 3) moves.push([r, c, 1, 4]);
        if (r === 2 && c === 5) moves.push([r, c, 1, 4]);
        if (r === 1 && c === 4) { moves.push([r, c, 0, 3]); moves.push([r, c, 0, 5]); }
    } else { // 한(Han) - 아래로 이동 (초나라 궁성 진입 시)
        if (r === 7 && c === 3) moves.push([r, c, 8, 4]);
        if (r === 7 && c === 5) moves.push([r, c, 8, 4]);
        if (r === 8 && c === 4) { moves.push([r, c, 9, 3]); moves.push([r, c, 9, 5]); }
    }

    // 중복 제거 및 유효성 필터링 (canCapture는 위에서 개별 체크됨)
    return moves.filter(m => inBounds(m[2], m[3]) && canCapture(board, m[2], m[3], side));
}

function getPieceMoves(board, r, c) {
    const p = board[r][c]; if (p === EMPTY) return [];
    switch (Math.abs(p)) {
        case P_KING: return kingMoves(board, r, c, p);
        case P_GUARD: return guardMoves(board, r, c, p);
        case P_CART: return cartMoves(board, r, c, p);
        case P_CANNON: return cannonMoves(board, r, c, p);
        case P_HORSE: return horseMoves(board, r, c, p);
        case P_ELEPH: return elephMoves(board, r, c, p);
        case P_PAWN: return pawnMoves(board, r, c, p);
        default: return [];
    }
}

function getAllMoves(board, isHan) {
    const moves = [];
    for (let r = 0; r < 10; r++) for (let c = 0; c < 9; c++) {
        const p = board[r][c];
        if (p === EMPTY) continue;
        if (isHan ? isHanSide(p) : isChoSide(p)) moves.push(...getPieceMoves(board, r, c));
    }
    return moves;
}

function applyMove(board, move) {
    const nb = cloneBoard(board);
    const [fr, fc, tr, tc] = move;
    nb[tr][tc] = nb[fr][fc]; nb[fr][fc] = EMPTY;
    return nb;
}

function evaluate(board) {
    let score = 0;
    for (let r = 0; r < 10; r++) for (let c = 0; c < 9; c++) {
        const p = board[r][c]; if (p === EMPTY) continue;
        const v = PIECE_VALUE[Math.abs(p)] || 0;
        score += isHanSide(p) ? -v : v;
    }
    return score;
}

function findKing(board, isHan) {
    const t = isHan ? H_KING : P_KING;
    for (let r = 0; r < 10; r++) for (let c = 0; c < 9; c++) if (board[r][c] === t) return [r, c];
    return null;
}

function minimax(board, depth, alpha, beta, maximizing) {
    if (depth === 0) return evaluate(board);
    const moves = getAllMoves(board, !maximizing);
    if (moves.length === 0) return maximizing ? -50000 : 50000;
    if (maximizing) {
        let best = -Infinity;
        for (const mv of moves) { const ev = minimax(applyMove(board, mv), depth - 1, alpha, beta, false); best = Math.max(best, ev); alpha = Math.max(alpha, ev); if (beta <= alpha) break; }
        return best;
    } else {
        let best = Infinity;
        for (const mv of moves) { const ev = minimax(applyMove(board, mv), depth - 1, alpha, beta, true); best = Math.min(best, ev); beta = Math.min(beta, ev); if (beta <= alpha) break; }
        return best;
    }
}

function getBestMove(board, difficulty) {
    const depth = Math.max(1, Math.min(4, Math.ceil(difficulty / 3)));
    const moves = getAllMoves(board, true);
    if (!moves.length) return null;
    const rndFactor = Math.max(0, (10 - difficulty) * 0.15);
    let bestEval = Infinity, bestMove = null;
    for (const mv of moves) {
        let ev = minimax(applyMove(board, mv), depth - 1, -Infinity, Infinity, true);
        ev += (Math.random() - 0.5) * rndFactor * 500;
        if (ev < bestEval) { bestEval = ev; bestMove = mv; }
    }
    return bestMove;
}

// ── 게임 상태 ──────────────────────────────────────────
let gameBoard = createInitialBoard();
let selectedCell = null;
let validMoves = [];
let isPlayerTurn = true;
let difficulty = 5;
let isGameOver = false;
let moveCount = 0;
let captureWillHappen = false;

// ── 사운드 (Web Audio API) ────────────────────────────
let audioCtx = null;
let isSoundEnabled = true; // 기본값 ON

function getAudio() { if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)(); return audioCtx; }

function playMoveSound() {
    if (!isSoundEnabled) return;
    try {
        const ctx = getAudio();
        const buf = ctx.createBuffer(1, ctx.sampleRate * 0.15, ctx.sampleRate);
        const data = buf.getChannelData(0);
        for (let i = 0; i < data.length; i++) {
            const t = i / ctx.sampleRate;
            const thud = Math.sin(2 * Math.PI * 120 * Math.exp(-t * 15) * t) * Math.exp(-t * 35);
            const noise = (Math.random() * 2 - 1) * Math.exp(-t * 40) * 0.2;
            data[i] = (thud + noise) * 0.7;
        }
        const src = ctx.createBufferSource(); src.buffer = buf;
        src.connect(ctx.destination); src.start();
    } catch (e) { }
}

function playCaptureSound() {
    if (!isSoundEnabled) return;
    try {
        const ctx = getAudio();
        const buf = ctx.createBuffer(1, ctx.sampleRate * 0.25, ctx.sampleRate);
        const data = buf.getChannelData(0);
        for (let i = 0; i < data.length; i++) {
            const t = i / ctx.sampleRate;
            const thud = Math.sin(2 * Math.PI * 80 * Math.exp(-t * 10) * t) * Math.exp(-t * 20);
            const snap = Math.sin(2 * Math.PI * 800 * t) * Math.exp(-t * 60) * 0.4;
            const noise = (Math.random() * 2 - 1) * Math.exp(-t * 30) * 0.3;
            data[i] = (thud + snap + noise) * 0.8;
        }
        const src = ctx.createBufferSource(); src.buffer = buf;
        src.connect(ctx.destination); src.start();
    } catch (e) { }
}

function playSelectSound() {
    if (!isSoundEnabled) return;
    try {
        const ctx = getAudio();
        const osc = ctx.createOscillator(); const g = ctx.createGain();
        osc.frequency.setValueAtTime(400, ctx.currentTime);
        osc.frequency.exponentialRampToValueAtTime(600, ctx.currentTime + 0.05);
        g.gain.setValueAtTime(0.15, ctx.currentTime); g.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.1);
        osc.connect(g); g.connect(ctx.destination); osc.start(); osc.stop(ctx.currentTime + 0.1);
    } catch (e) { }
}

function playCheckSound() {
    if (!isSoundEnabled) return;
    try {
        const ctx = getAudio();
        [0, 0.1, 0.2].forEach((t, i) => {
            const osc = ctx.createOscillator(); const g = ctx.createGain();
            osc.frequency.value = [440, 550, 660][i];
            g.gain.setValueAtTime(0.3, ctx.currentTime + t); g.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + t + 0.15);
            osc.connect(g); g.connect(ctx.destination); osc.start(ctx.currentTime + t); osc.stop(ctx.currentTime + t + 0.15);
        });
    } catch (e) { }
}

function toggleSound(enabled) { isSoundEnabled = enabled; }

// 간단한 동양풍 멜로디 BGM (합성음)
function toggleBGM(play) {
    const ctx = getAudio();
    if (play) {
        if (isBgmPlaying) return;
        isBgmPlaying = true;

        const melody = [261.63, 293.66, 329.63, 392.00, 440.00]; // 도레미솔라 (궁상각치우)
        let noteIdx = 0;

        function playNextNote() {
            if (!isBgmPlaying) return;
            const osc = ctx.createOscillator();
            const g = ctx.createGain();
            const freq = melody[noteIdx % melody.length];

            osc.type = 'triangle';
            osc.frequency.setValueAtTime(freq, ctx.currentTime);
            g.gain.setValueAtTime(0, ctx.currentTime);
            g.gain.linearRampToValueAtTime(0.05, ctx.currentTime + 0.5);
            g.gain.linearRampToValueAtTime(0, ctx.currentTime + 2.0);

            osc.connect(g);
            g.connect(ctx.destination);

            osc.start();
            osc.stop(ctx.currentTime + 2.0);

            noteIdx++;
            setTimeout(playNextNote, 1500 + Math.random() * 1000);
        }
        playNextNote();
    } else {
        isBgmPlaying = false;
    }
}

// ── 보드 렌더링 (교차점 기반, 사진과 동일한 디자인) ────────────────────────
const COLS = 9, ROWS = 10;

function getBoardSize() {
    // ★ 버그 수정: 부모(#jg-board-outer)의 내부 크기를 기준으로 삼아
    //   renderBoard가 container에 고정 px를 설정해도 다음 렌더링 시 줄어들지 않음
    const outer = document.getElementById('jg-board-outer');
    const el = document.getElementById('jg-board-container');

    // outer의 padding과 border를 제외한 내부 영역 = 나무판 영역
    const totalW = outer ? outer.clientWidth - parseFloat(getComputedStyle(outer).paddingLeft) * 2 : window.innerWidth * 0.80;
    const totalH = outer ? outer.clientHeight - parseFloat(getComputedStyle(outer).paddingTop) * 2 : window.innerHeight * 0.80;

    // 상하좌우 동일한 비율의 여백 (8%)
    const marginRatio = 0.08;
    const marginX = totalW * marginRatio;
    const marginY = totalH * marginRatio;

    // 격자 영역: 컨테이너에서 여백을 제외한 영역
    const availW = totalW - (marginX * 2);
    const availH = totalH - (marginY * 2);

    // 장기판 9x10 (8칸×9칸) 비율에 맞춰 cellW, cellH 독립 산출
    const cellW = availW / (COLS - 1);
    const cellH = availH / (ROWS - 1);

    const w = (COLS - 1) * cellW;
    const h = (ROWS - 1) * cellH;

    // 완벽한 중앙 정렬: 보정 없이 순수 수학적 기초값만 사용
    const padX = (totalW - w) / 2;
    const padY = (totalH - h) / 2;

    return { cellW, cellH, w, h, padX, padY, totalW, totalH };
}

function getPieceImage(p) {
    const isCho = isChoSide(p);
    const suffix = isCho ? '_b.svg' : '_r.svg';
    switch (Math.abs(p)) {
        case P_KING: return 'king' + suffix;
        case P_GUARD: return 'guard' + suffix;
        case P_ELEPH: return 'elephant' + suffix;
        case P_HORSE: return 'horse' + suffix;
        case P_CART: return 'rook' + suffix; // 기물은 車(Cart)이나 파일명은 rook임
        case P_CANNON: return 'cannon' + suffix;
        case P_PAWN: return 'pawn' + suffix;
        default: return '';
    }
}

function renderBoard(board) {
    const container = document.getElementById('jg-board-container');
    if (!container) return;
    container.innerHTML = '';

    const size = getBoardSize();
    const { cellW, cellH, w, h, padX, padY, totalW, totalH } = size;

    // SVG 보드 (선)
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('width', totalW); svg.setAttribute('height', totalH);
    svg.style.cssText = 'position:absolute;top:0;left:0;pointer-events:none;z-index:1;';

    const lineStyle = 'stroke:#4a3211; stroke-width:1.5; stroke-linecap:round;';

    // 가로선
    for (let r = 0; r < ROWS; r++) {
        const y = padY + r * cellH; // cell -> cellH
        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.setAttribute('x1', padX); line.setAttribute('y1', y);
        line.setAttribute('x2', padX + w); line.setAttribute('y2', y);
        line.setAttribute('style', lineStyle);
        svg.appendChild(line);
    }
    // 세로선
    for (let c = 0; c < COLS; c++) {
        const x = padX + c * cellW; // cell -> cellW
        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.setAttribute('x1', x); line.setAttribute('y1', padY);
        line.setAttribute('x2', x); line.setAttribute('y2', padY + h);
        line.setAttribute('style', lineStyle);
        svg.appendChild(line);
    }

    // 궁 대각선
    [{ r: 0, c: 3 }, { r: 7, c: 3 }].forEach(({ r, c }) => {
        const x1 = padX + c * cellW, y1 = padY + r * cellH;
        const x2 = padX + (c + 2) * cellW, y2 = padY + (r + 2) * cellH;
        [[x1, y1, x2, y2], [x2, y1, x1, y2]].forEach(([ax, ay, bx, by]) => {
            const d = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            d.setAttribute('x1', ax); d.setAttribute('y1', ay);
            d.setAttribute('x2', bx); d.setAttribute('y2', by);
            d.setAttribute('style', lineStyle + 'stroke-width:1.2;');
            svg.appendChild(d);
        });
    });

    container.style.cssText = `position:relative;width:${totalW}px;height:${totalH}px; cursor:default;`;

    // 클릭 오버레이
    const overlay = document.createElement('div');
    overlay.style.cssText = `position:absolute;inset:0;`;

    const validTargets = new Set(validMoves.map(m => `${m[2]},${m[3]}`));

    for (let r = 0; r < ROWS; r++) {
        for (let c = 0; c < COLS; c++) {
            const { cellW, cellH, padX, padY } = size;
            const cx = padX + c * cellW, cy = padY + r * cellH;
            const p = board[r][c];
            const isSelected = selectedCell && selectedCell[0] === r && selectedCell[1] === c;
            const isHint = validTargets.has(`${r},${c}`);
            const isCapture = isHint && p !== EMPTY;

            const hot = document.createElement('div');
            // 가로(cellW), 세로(cellH) 독립 반영하여 클릭 영역 생성
            hot.style.cssText = `position:absolute;width:${cellW}px;height:${cellH}px;left:${cx - cellW / 2}px;top:${cy - cellH / 2}px;display:flex;align-items:center;justify-content:center;cursor:pointer;z-index:20;`;
            hot.addEventListener('click', () => onCellClick(r, c));

            // 이동 힌트 (심플한 녹색 원)
            if (isHint && !isCapture) {
                const dot = document.createElement('div');
                dot.style.cssText = `width:${cellH * 0.35}px;height:${cellH * 0.35}px;border-radius:50%;background:rgba(46,204,113,0.6);box-shadow:0 0 10px rgba(0,0,0,0.1);`;
                hot.appendChild(dot);
            }

            if (p !== EMPTY) {
                const pc = document.createElement('div');
                const isCho = isChoSide(p);
                const absP = Math.abs(p);

                // 기물 크기 차별화: 졸(卒/兵)과 사(士)는 작게 (0.72), 왕은 크게 (1.05), 나머지는 중간 (0.88)
                let scale = 0.88;
                if (absP === P_PAWN || absP === P_GUARD) scale = 0.72;
                if (absP === P_KING) scale = 1.05;

                // 기물 크기: 세로(cellH) 기준 산출 (기존 1.18 -> 1.30으로 10% 확대)
                const sz = Math.floor(cellH * scale * 1.30);
                const imgName = getPieceImage(p);

                // 왕(King) 기물은 가로가 찌부되어 보이지 않도록 넓이를 25% 확장 (다른 기물은 5%)
                const widthMult = (absP === P_KING) ? 1.25 : 1.05;

                pc.className = 'jg-piece';
                pc.style.cssText = `
                  width:${Math.floor(sz * widthMult)}px;height:${sz}px;
                  display:flex;align-items:center;justify-content:center;
                  transform:${isSelected ? 'scale(1.1) translateY(-3px)' : 'scale(1)'};
                  transition: transform 0.15s cubic-bezier(0.175, 0.885, 0.32, 1.275);
                  position:relative; z-index:15;
                `;

                // [장기 성능 최적화]: 매번 Image를 새로 로드하지 않고 프리캐시 사용
                const img = preloadedImages[imgName] ? preloadedImages[imgName].cloneNode() : document.createElement('img');
                if (!preloadedImages[imgName]) img.src = `/game/static/images/janggi/${imgName}`;

                img.style.cssText = `
                    width: 100%; height: 100%; 
                    filter: drop-shadow(0 3px 5px rgba(0,0,0,0.3)) ${isSelected ? 'drop-shadow(0 0 8px #f1c40f)' : ''};
                `;
                pc.appendChild(img);

                if (isCapture) {
                    pc.style.animation = 'jg-pulse 1s infinite';
                }

                hot.appendChild(pc);
            }
            overlay.appendChild(hot);
        }
    }

    container.appendChild(svg);
    container.appendChild(overlay);
    updateStatus();
}

let undoStack = [];
let undoLimit = 5; // 난이도에 따라 가변

function saveState() {
    undoStack.push({
        board: JSON.parse(JSON.stringify(gameBoard)),
        turn: isPlayerTurn,
        moveCount: moveCount
    });
    // 스택 크기는 무르기 가능 횟수보다 넉넉히 유지 (최신 10개)
    if (undoStack.length > 10) undoStack.shift();
    updateUndoUI();
}

function updateUndoUI() {
    const undoBtn = document.getElementById('jg-undo-btn');
    const undoVal = document.getElementById('jg-undo-val');
    if (undoBtn) undoBtn.disabled = undoStack.length === 0 || !isPlayerTurn || undoLimit <= 0;
    if (undoVal) undoVal.textContent = undoLimit;
}

function undoMove() {
    if (isGameOver || !isPlayerTurn || undoStack.length === 0 || undoLimit <= 0) return;
    const lastState = undoStack.pop();
    gameBoard = lastState.board;
    isPlayerTurn = lastState.turn;
    moveCount = lastState.moveCount;
    undoLimit--; // 무르기 횟수 차감
    const mcEl = document.getElementById('jg-move-count');
    if (mcEl) mcEl.textContent = moveCount;
    selectedCell = null; validMoves = [];
    updateUndoUI(); updateStatus(); renderBoard(gameBoard);
    playMoveSound();
}

function onCellClick(r, c) {
    if (isGameOver || !isPlayerTurn) return;
    const p = gameBoard[r][c];

    // 이동 실행
    if (selectedCell && validMoves.some(m => m[2] === r && m[3] === c)) {
        saveState();
        const willCapture = gameBoard[r][c] !== EMPTY;
        const mv = [...selectedCell, r, c];
        executeMove(mv, true, willCapture);
        return;
    }

    // 기물 선택
    if (p !== EMPTY && isChoSide(p)) {
        selectedCell = [r, c];
        validMoves = getPieceMoves(gameBoard, r, c);
        playSelectSound();
        renderBoard(gameBoard);
        return;
    }

    // 선택 해제
    selectedCell = null; validMoves = [];
    renderBoard(gameBoard);
}

function executeMove(mv, isPlayer, willCapture) {
    gameBoard = applyMove(gameBoard, mv);
    selectedCell = null; validMoves = [];
    moveCount++;
    const mcEl = document.getElementById('jg-move-count');
    if (mcEl) mcEl.textContent = moveCount;

    if (willCapture) playCaptureSound();
    else playMoveSound();

    renderBoard(gameBoard);

    if (isPlayer) {
        if (!findKing(gameBoard, true)) { endGame('🎉 초(플레이어) 승리!'); return; }
        isPlayerTurn = false; updateStatus();
        setTimeout(aiMove, 350);
    } else {
        if (!findKing(gameBoard, false)) { endGame('🤖 한(AI) 승리!'); return; }
        isPlayerTurn = true; updateStatus();
    }
}

function aiMove() {
    if (isGameOver) return;
    const mv = getBestMove(gameBoard, difficulty);
    if (!mv) { endGame('🎉 초(플레이어) 승리! (AI 이동 불가)'); return; }
    const willCapture = gameBoard[mv[2]][mv[3]] !== EMPTY;
    executeMove(mv, false, willCapture);
}

function updateStatus() {
    const el = document.getElementById('jg-status');
    if (!el || isGameOver) return;
    el.textContent = isPlayerTurn ? '당신의 턴 (楚 ⬇)' : 'AI 생각 중... (漢 ⬆)';
    el.style.background = isPlayerTurn ? '#483C32' : '#c0392b';
}

function endGame(msg) {
    isGameOver = true;
    const resArea = document.getElementById('jg-result-area');
    const resTitle = document.getElementById('jg-result-title');
    const settingsModal = document.getElementById('jg-settings-modal');
    if (resArea && resTitle) {
        resArea.classList.remove('hidden');
        resTitle.textContent = msg.includes('승리') ? 'VICTORY' : 'DEFEAT';
        // Detailed message can go in jg-result-desc if needed
    }
    if (settingsModal) {
        settingsModal.classList.remove('hidden');
        document.body.classList.add('modal-open');
    }
}

function startGame() {
    const formationBtn = document.querySelector('.formation-btn.selected');
    const choFormation = formationBtn ? formationBtn.dataset.type : 'ma-sang-ma-sang';
    const difficultyInput = document.getElementById('jg-difficulty');
    difficulty = difficultyInput ? parseInt(difficultyInput.value) : 5;

    // 난이도에 따른 무르기 횟수 자동 부여: 쉬움(1-3)=10회, 보통(4-6)=5회, 어려움(7-10)=3회
    undoLimit = 5;
    if (difficulty <= 3) undoLimit = 10;
    else if (difficulty >= 7) undoLimit = 3;

    // [v258] AI(한나라) 진영의 배치를 매 게임 무작위로 설정
    const hanFormations = ['ma-sang-ma-sang', 'sang-ma-sang-ma', 'ma-sang-sang-ma', 'sang-ma-ma-sang'];
    const randomHanFormation = hanFormations[Math.floor(Math.random() * hanFormations.length)];

    gameBoard = createInitialBoard(choFormation, randomHanFormation);
    selectedCell = null; validMoves = [];
    isPlayerTurn = true; isGameOver = false; moveCount = 0; undoStack = [];

    const mcEl = document.getElementById('jg-move-count');
    if (mcEl) mcEl.textContent = 0;

    const resArea = document.getElementById('jg-result-area');
    const settingsModal = document.getElementById('jg-settings-modal');
    if (resArea) resArea.classList.add('hidden');
    if (settingsModal) {
        settingsModal.classList.add('hidden');
        document.body.classList.remove('modal-open');
    }

    updateUndoUI();
    updateStatus();
    renderBoard(gameBoard);
}

window.addEventListener('DOMContentLoaded', () => {
    // 난이도 UI 동기화 (HTML 내 인라인 스크립트와 중복될 수 있으나 안정성을 위해 유지)
    const slider = document.getElementById('jg-difficulty');
    const dv = document.getElementById('jg-diff-val');
    const dd = document.getElementById('jg-diff-desc');
    const descs = ["매우 쉬움", "쉬움", "적절함", "도전적임", "약간 어려워짐", "어려움", "매우 어려움", "장기 기사", "그랜드마스터", "장기 신"];

    if (slider) {
        slider.addEventListener('input', () => {
            difficulty = parseInt(slider.value);
            if (dv) dv.textContent = difficulty;
            if (dd) dd.textContent = descs[difficulty - 1] || '보통';
        });
    }

    // 포메이션 버튼 이벤트 (이미 HTML에 있을 수 있음)
    const formationBtns = document.querySelectorAll('.formation-btn');
    formationBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            formationBtns.forEach(b => b.classList.remove('selected'));
            btn.classList.add('selected');
        });
    });

    // 시작 버튼
    document.getElementById('jg-new-game-btn')?.addEventListener('click', startGame);

    // 모달 제어
    const modal = document.getElementById('jg-settings-modal');
    document.getElementById('jg-settings-btn')?.addEventListener('click', () => {
        modal.classList.toggle('hidden');
        document.body.classList.toggle('modal-open');
    });
    document.getElementById('jg-close-modal-top')?.addEventListener('click', () => {
        modal.classList.add('hidden');
        document.body.classList.remove('modal-open');
    });

    // 무르기 버튼
    document.getElementById('jg-undo-btn')?.addEventListener('click', undoMove);

    // 기권 버튼
    document.getElementById('jg-resign-btn')?.addEventListener('click', () => {
        if (confirm('정말로 기권하시겠습니까?')) endGame('📉 기권패 하셨습니다.');
    });

    // SND(효과음) 버튼
    document.getElementById('jg-snd-btn')?.addEventListener('click', function () {
        this.classList.toggle('snd-active');
        const active = this.classList.contains('snd-active');
        toggleSound(active);
    });

    window.addEventListener('resize', () => renderBoard(gameBoard));

    updateStatus();
    // 초기 보드 렌더링 (그리드 라인 표시용)
    gameBoard = Array.from({ length: 10 }, () => Array(9).fill(0));
    renderBoard(gameBoard);

    // 초기 모달 표시
    setTimeout(() => {
        if (modal) {
            modal.classList.remove('hidden');
            document.body.classList.add('modal-open');
        }
    }, 500);
});
