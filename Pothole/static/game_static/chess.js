var board = null;
var game = new Chess();
var engine = null;
var gameOver = false;
var difficulty = 5;
var undoTotal = 5;
var moveHistory = [];
var selectedSquare = null;
var promotionPending = false;
var selectedPromotion = null;

// DOM 요소
var difficultyInput, diffValDisplay, diffDescDisplay, undoValDisplay, undoBtn, startGameBtn, resignBtn, moveHistoryEl, capturedWhiteEl, capturedBlackEl;

var descTexts = [
    "",
    "⭐ 완전 초심자용 | 거의 무작위 수를 둡니다. 누구나 이길 수 있습니다.",
    "⭐⭐ 입문자용 | 기초적인 수만 둡니다. 기물 보호를 거의 안 합니다.",
    "⭐⭐⭐ 초급자용 | 간단한 전술을 씁니다. 허점이 많습니다.",
    "⭐⭐⭐⭐ 초·중급 | 기본 전략을 사용합니다. 실수가 종종 있습니다.",
    "⭐⭐⭐⭐⭐ 중급 | 전술적으로 둡니다. 적당히 도전적인 난이도입니다.",
    "⭐⭐⭐⭐⭐⭐ 중·고급 | 강력한 공격과 수비를 합니다.",
    "⭐x7 고급 | 집중하지 않으면 질 수 있습니다.",
    "⭐x8 마스터급 | 정교한 수 읽기. 아마추어가 이기기 어렵습니다.",
    "⭐x9 전문가급 | 평범한 플레이어는 이기기 거의 불가능합니다.",
    "⭐x10 인류 최강 | Stockfish 최고 레벨. 세계 챔피언도 이기기 힘든 수준입니다."
];

const PIECE_ICONS = {
    'p': 'https://chessboardjs.com/img/chesspieces/wikipedia/bP.png',
    'n': 'https://chessboardjs.com/img/chesspieces/wikipedia/bN.png',
    'b': 'https://chessboardjs.com/img/chesspieces/wikipedia/bB.png',
    'r': 'https://chessboardjs.com/img/chesspieces/wikipedia/bR.png',
    'q': 'https://chessboardjs.com/img/chesspieces/wikipedia/bQ.png',
    'k': 'https://chessboardjs.com/img/chesspieces/wikipedia/bK.png',
    'P': 'https://chessboardjs.com/img/chesspieces/wikipedia/wP.png',
    'N': 'https://chessboardjs.com/img/chesspieces/wikipedia/wN.png',
    'B': 'https://chessboardjs.com/img/chesspieces/wikipedia/wB.png',
    'R': 'https://chessboardjs.com/img/chesspieces/wikipedia/wR.png',
    'Q': 'https://chessboardjs.com/img/chesspieces/wikipedia/wQ.png',
    'K': 'https://chessboardjs.com/img/chesspieces/wikipedia/wK.png'
};

const PROMO_PIECES = [
    { code: 'q', name: '퀸', white: 'Q', black: 'q' },
    { code: 'r', name: '룩', white: 'R', black: 'r' },
    { code: 'b', name: '비숍', white: 'B', black: 'b' },
    { code: 'n', name: '나이트', white: 'N', black: 'n' }
];

// 엔진 초기화 (Web Worker 방식 - Stockfish.js WASM 필수)
function initEngine() {
    console.log("Stockfish 엔진 초기화 (Web Worker)...");
    try {
        engine = new Worker('/game/static/stockfish.js');

        engine.onmessage = function (event) {
            const line = event.data;
            console.log("Engine:", line);

            if (typeof line === 'string' && line.startsWith('bestmove')) {
                const parts = line.split(' ');
                const moveUCI = parts[1];
                if (moveUCI && moveUCI !== '(none)') {
                    makeAIMove(moveUCI);
                }
            }
        };

        engine.onerror = function (err) {
            console.error("Stockfish Worker 오류:", err);
        };

        engine.postMessage('uci');
        engine.postMessage('isready');
        engine.postMessage('ucinewgame');
        console.log("Stockfish Worker 초기화 완료");
    } catch (e) {
        console.error("Stockfish Worker 생성 실패:", e);
    }
}

function updateEngineDifficulty() {
    if (!engine) return;
    let skillLevel;
    if (difficulty == 1) skillLevel = 0;
    else if (difficulty == 2) skillLevel = 1;
    else if (difficulty == 3) skillLevel = 3;
    else skillLevel = Math.round((difficulty - 1) * (20 / 9));

    engine.postMessage(`setoption name Skill Level value ${skillLevel}`);
}

function removeHighlights() {
    $('#myBoard .square-55d63').removeClass('highlight-square');
}

function highlightLegalMoves(square) {
    const moves = game.moves({
        square: square,
        verbose: true
    });
    moves.forEach(m => {
        $('#myBoard .square-' + m.to).addClass('highlight-square');
    });
}

function getCapturedWhitePieces() {
    const initial = { 'P': 8, 'N': 2, 'B': 2, 'R': 2, 'Q': 1 };
    const current = { 'P': 0, 'N': 0, 'B': 0, 'R': 0, 'Q': 0 };
    const fen = game.fen().split(' ')[0];
    for (let ch of fen) {
        if (current[ch] !== undefined) current[ch]++;
    }
    const captured = {};
    for (let p in initial) {
        const cnt = initial[p] - current[p];
        if (cnt > 0) captured[p] = cnt;
    }
    return captured;
}

function showPromotionModal() {
    promotionPending = true;
    selectedPromotion = null;
    $('#promo-confirm-btn').prop('disabled', true);

    const capturedMap = getCapturedWhitePieces();
    let html = '';
    PROMO_PIECES.forEach(p => {
        const count = capturedMap[p.white] || 0;
        const disabled = count === 0 ? 'disabled-piece' : '';
        const countBadge = count > 0 ? `<span style="font-size:0.65rem;color:#888;">(${count}개)</span>` : `<span style="font-size:0.65rem;color:#ccc;">없음</span>`;
        html += `
            <button class="promo-piece-btn ${disabled}" data-piece="${p.code}" data-name="${p.name}">
                <img src="${PIECE_ICONS[p.white]}" alt="${p.name}">
                <span>${p.name}</span>
                ${countBadge}
            </button>`;
    });

    $('#promo-captured-list').html(html);
    $('#promo-selected-display').html('<span id="promo-selected-name">없음</span>');

    const totalCaptured = Object.values(capturedMap).reduce((a, b) => a + b, 0);
    if (totalCaptured === 0) {
        $('#promo-subtitle').text('잡힌 기물이 없어 퀸으로 자동 승격됩니다');
        selectedPromotion = 'q';
        $('#promo-confirm-btn').prop('disabled', false);
    } else {
        $('#promo-subtitle').text('잡힌 아군 기물 중 하나를 선택하세요');
    }
    $('#promotion-modal').removeClass('hidden');
}

$(document).on('click', '.promo-piece-btn:not(.disabled-piece)', function () {
    $('.promo-piece-btn').removeClass('selected');
    $(this).addClass('selected');
    const piece = $(this).data('piece');
    const name = $(this).data('name');
    selectedPromotion = piece;
    $('#promo-selected-display').html(`<img src="${PIECE_ICONS[piece.toUpperCase()]}" alt="${name}"><strong>${name}</strong>`);
    $('#promo-confirm-btn').prop('disabled', false);
});

$(document).on('click', '#promo-confirm-btn', function () {
    if (!selectedPromotion || !promotionPending) return;

    // 수동 프로모션 이동 실행
    const moveData = {
        from: pendingPromotionMove.from,
        to: pendingPromotionMove.to,
        promotion: selectedPromotion
    };

    const move = game.move(moveData);
    if (move) {
        promotionPending = false;
        $('#promotion-modal').addClass('hidden');
        board.position(game.fen());
        addMoveToHistory(getMoveInfo(move), 'white');
        updateStatus();

        if (!game.game_over()) {
            requestAIMove();
        }
    }
});

var pendingPromotionMove = null;

function handleMove(source, target) {
    if (gameOver || promotionPending) return;

    // 프로모션 체크
    const piece = game.get(source);
    if (piece && piece.type === 'p' && piece.color === 'w' && target[1] === '8') {
        const moveAttempt = game.move({ from: source, to: target, promotion: 'q' });
        if (moveAttempt) {
            game.undo(); // 시도 취소
            pendingPromotionMove = { from: source, to: target };
            showPromotionModal();
            return;
        }
    }

    const move = game.move({
        from: source,
        to: target,
        promotion: 'q'
    });

    if (move === null) return 'snapback';

    board.position(game.fen());
    addMoveToHistory(getMoveInfo(move), 'white');
    updateStatus();

    if (!game.game_over()) {
        requestAIMove();
    }
}

function requestAIMove() {
    if (!engine || gameOver) return;
    $('#status').text('AI가 생각하는 중...');
    updateEngineDifficulty();

    // 난이도 1단계 특별 처리: 랜덤 수 확률 도입 (누구나 이길 수 있게)
    if (difficulty == 1) {
        const moves = game.moves();
        if (Math.random() < 0.7 && moves.length > 0) { // 70% 확률로 완전 랜덤
            console.log("AI Level 1: 랜덤 수 선택");
            const randomMove = moves[Math.floor(Math.random() * moves.length)];
            setTimeout(() => {
                const moveResult = game.move(randomMove);
                if (moveResult) {
                    board.position(game.fen());
                    addMoveToHistory(getMoveInfo(moveResult), 'black');
                    updateStatus();
                }
            }, 500);
            return;
        }
    }

    engine.postMessage('isready');
    engine.postMessage('position fen ' + game.fen());

    // 난이도별 최적화 (v207)
    let timeLimit, depthLimit;
    if (difficulty == 1) {
        timeLimit = 50; depthLimit = 1; // 극도로 낮음
    } else if (difficulty == 2) {
        timeLimit = 100; depthLimit = 2; // 매우 낮음
    } else if (difficulty == 3) {
        timeLimit = 200; depthLimit = 3; // 낮음
    } else {
        timeLimit = Math.round((0.1 + (difficulty * 0.15)) * 1000);
        depthLimit = 5 + parseInt(difficulty);
    }

    console.log(`AI 요청 (Level ${difficulty}): depth ${depthLimit}, time ${timeLimit}ms`);
    engine.postMessage(`go depth ${depthLimit} movetime ${timeLimit}`);
}

function makeAIMove(moveUCI) {
    const move = game.move({
        from: moveUCI.substring(0, 2),
        to: moveUCI.substring(2, 4),
        promotion: moveUCI.length === 5 ? moveUCI[4] : 'q'
    });

    if (move) {
        board.position(game.fen());
        addMoveToHistory(getMoveInfo(move), 'black');
        updateStatus();
    }
}

function getMoveInfo(move) {
    const pieceMap = { 'p': '졸', 'n': '나이트', 'b': '비숍', 'r': '룩', 'q': '퀸', 'k': '킹' };
    return {
        move: move.from + move.to,
        piece_name: pieceMap[move.piece],
        piece_color: move.color === 'w' ? 'white' : 'black',
        is_capture: move.captured ? true : false,
        captured_piece: move.captured ? pieceMap[move.captured] : null
    };
}

function addMoveToHistory(info, player) {
    if (!info) return;
    const colorLabel = info.piece_color === 'white' ? '백색' : '흑색';
    let msg = `<b>${colorLabel} ${info.piece_name}</b> ${info.move.substring(0, 2)} → ${info.move.substring(2, 4)}`;
    if (info.is_capture) msg += ` <small>(${info.captured_piece} 획득)</small>`;
    $('#move-history').prepend(`<div class="move-item ${player}">${msg}</div>`);
}

function updateCapturedPieces() {
    const counts = { 'p': 8, 'n': 2, 'b': 2, 'r': 2, 'q': 1, 'k': 1, 'P': 8, 'N': 2, 'B': 2, 'R': 2, 'Q': 1, 'K': 1 };
    game.board().forEach(row => {
        row.forEach(p => {
            if (p) {
                const char = p.color === 'w' ? p.type.toUpperCase() : p.type;
                counts[char]--;
            }
        });
    });

    let whiteHtml = '', blackHtml = '';
    ['P', 'N', 'B', 'R', 'Q'].forEach(p => {
        for (let i = 0; i < counts[p]; i++) whiteHtml += `<img src="${PIECE_ICONS[p]}" class="captured-piece">`;
    });
    ['p', 'n', 'b', 'r', 'q'].forEach(p => {
        for (let i = 0; i < counts[p]; i++) blackHtml += `<img src="${PIECE_ICONS[p]}" class="captured-piece">`;
    });

    $('#captured-white').html(whiteHtml);
    $('#captured-black').html(blackHtml);
}

function updateStatus() {
    let status = '';
    if (game.in_checkmate()) {
        gameOver = true;
        status = '체크메이트! 게임 종료.';
        triggerEndingSequence();
    } else if (game.in_draw()) {
        gameOver = true;
        status = '스테일메이트/무승부! 게임 종료.';
        $('#result-title').text('DRAW');
        $('#result-desc').text(status);
        $('#game-result-area, #settings-modal').removeClass('hidden');
    } else {
        status = game.turn() === 'w' ? '당신의 턴' : 'AI의 턴';
        if (game.in_check()) $('#check-alert').removeClass('hidden');
        else $('#check-alert').addClass('hidden');
    }

    $('#status').text(status);
    $('#undo-val').text(undoTotal);
    $('#undoBtn').prop('disabled', undoTotal <= 0 || gameOver);
    updateCapturedPieces();
}

function triggerEndingSequence() {
    const isWin = game.turn() === 'b'; // 승리 직후는 상대 턴
    const title = isWin ? 'VICTORY' : 'DEFEAT';
    const desc = isWin ? '체크메이트로 AI를 굴복시켰습니다.' : 'AI에게 체크메이트를 당했습니다.';

    setTimeout(() => {
        const kingColor = isWin ? 'b' : 'w';
        const $king = $(`img[data-piece="${kingColor}K"]`);
        if ($king.length > 0) {
            $king.addClass('king-death-vibrate');
            setTimeout(() => {
                $('#result-title').text(title);
                $('#result-desc').text(desc);
                $('#game-result-area, #settings-modal').removeClass('hidden');
                $king.css('opacity', '0');
            }, 1200);
        } else {
            $('#result-title').text(title);
            $('#result-desc').text(desc);
            $('#game-result-area, #settings-modal').removeClass('hidden');
        }
    }, 500);
}

$(document).on('click', '.square-55d63', function () {
    if (gameOver || promotionPending || game.turn() === 'b') return;
    const square = $(this).data('square');
    if (!square) return;

    if (selectedSquare) {
        if (selectedSquare === square) {
            selectedSquare = null;
            removeHighlights();
        } else {
            const move = handleMove(selectedSquare, square);
            if (move !== 'snapback') {
                selectedSquare = null;
                removeHighlights();
            } else {
                // 다른 기물 선택 시도
                const piece = game.get(square);
                if (piece && piece.color === 'w') {
                    selectedSquare = square;
                    removeHighlights();
                    $(this).addClass('highlight-square');
                    highlightLegalMoves(square);
                }
            }
        }
    } else {
        const piece = game.get(square);
        if (piece && piece.color === 'w') {
            selectedSquare = square;
            removeHighlights();
            $(this).addClass('highlight-square');
            highlightLegalMoves(square);
        }
    }
});

$(document).ready(function () {
    difficultyInput = document.getElementById('difficulty');
    diffValDisplay = document.getElementById('diff-val');
    diffDescDisplay = document.getElementById('diff-desc');
    initEngine();

    setTimeout(() => {
        board = Chessboard('myBoard', {
            draggable: false,
            position: 'start',
            pieceTheme: 'https://chessboardjs.com/img/chesspieces/wikipedia/{piece}.png'
        });
        $(window).resize(board.resize);
        $('#status').text('설정에서 게임을 시작하세요');
    }, 300);

    difficultyInput.oninput = function () {
        difficulty = this.value;
        diffValDisplay.innerText = this.value;
        diffDescDisplay.innerText = descTexts[this.value];
    };

    $('#startGameBtn').click(() => {
        game.reset();
        board.start();
        gameOver = false;
        promotionPending = false;
        undoTotal = 5;
        $('#move-history').empty();
        $('#game-result-area, #check-alert, #settings-modal, #promotion-modal').addClass('hidden');
        updateStatus();
    });

    $('#undoBtn').click(() => {
        if (undoTotal <= 0 || gameOver || game.turn() === 'b') return;
        game.undo(); // AI move
        game.undo(); // Player move
        board.position(game.fen());
        undoTotal--;
        $('#move-history div:first-child').remove();
        $('#move-history div:first-child').remove();
        updateStatus();
    });

    $('#resignBtn').click(() => {
        gameOver = true;
        $('#status').text('기권패');
        $('#result-title').text('RESIGNED');
        $('#result-desc').text('게임을 기권하셨습니다.');
        $('#game-result-area, #settings-modal').removeClass('hidden');
    });

    $('#settingsBtn').click(() => $('#settings-modal').removeClass('hidden'));
    $('#closeSettingsBtn').click(() => $('#settings-modal').addClass('hidden'));
});
