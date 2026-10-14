// ── Scene parameters ───────────────────────────────────────────────────────────
const N           = 819;
const D           = 81;
const FOV_DEG     = 60.0;
const max_angle   = Math.tan((FOV_DEG / 2) * Math.PI / 180);
const disp_center = (N - 1) / 2.0;

// tan_theta[v] ∈ [-1, 1]: normalised directional sample (full range spans ±max_angle)
const tan_theta = Float64Array.from({ length: D }, (_, v) => 1 - 2 * v / (D - 1));

// Hogel positions along the display plane (z = 0)
const hogels = Float64Array.from({ length: N }, (_, i) => i);

// ── Camera state ───────────────────────────────────────────────────────────────
// tan(cam_fov/2) = ratio * max_angle
// z_cam          = -(N/2) / (ratio * max_angle)
// ratio = 0      → orthographic (camera at −∞, rays become parallel)
let camFovRatio    = parseFloat(document.getElementById('ratioSlider').value);
let z_cam_hogels   = 0;       // computed in recomputeScene()
let isOrthographic = false;
const x_cam        = new Float64Array(D);

// Uniform world-space step between adjacent camera x positions
// x_cam[i+1] - x_cam[i] = z_cam * (tan_theta[i+1] - tan_theta[i]) * max_angle
//                        = z_cam * (-2/(D-1)) * max_angle  → positive (z_cam < 0)
function cameraWorldStep() {
    return z_cam_hogels * (-2 / (D - 1)) * max_angle;
}

let camIdx    = Math.floor(D / 2);
let debugDots = false;

function recomputeScene() {
    isOrthographic = camFovRatio < 1e-9;

    if (isOrthographic) {
        z_cam_hogels = -Infinity;
        document.getElementById('hZ').textContent = '−∞';
    } else {
        z_cam_hogels = -(N / 2) / (camFovRatio * max_angle);
        for (let i = 0; i < D; i++) {
            x_cam[i] = disp_center + z_cam_hogels * tan_theta[i] * max_angle;
        }
        document.getElementById('hZ').textContent = z_cam_hogels.toFixed(1);
    }

    document.getElementById('hRatio').textContent = camFovRatio.toFixed(2);
    refreshHUD();
}

function refreshHUD() {
    document.getElementById('hCI').textContent  = camIdx;
    document.getElementById('hCX').textContent  = isOrthographic ? '−∞' : x_cam[camIdx].toFixed(2);
    document.getElementById('hCT').textContent  =
        (Math.atan(max_angle * tan_theta[camIdx]) * 180 / Math.PI).toFixed(2) + '°';
}

// ── Canvas & viewport ──────────────────────────────────────────────────────────
const canvas = document.getElementById('c');
const ctx    = canvas.getContext('2d');
let W = 0, H = 0;
let viewX = 0, viewZ = 0, scale = 1;

function worldBounds() {
    if (isOrthographic) {
        // Camera at −∞; frame the hogel plane + a fixed depth below for the parallel rays
        return { wxMin: -80, wxMax: N - 1 + 80, wzMin: -1200, wzMax: 80 };
    }
    let xMin = Infinity, xMax = -Infinity;
    for (let i = 0; i < D; i++) {
        if (x_cam[i] < xMin) xMin = x_cam[i];
        if (x_cam[i] > xMax) xMax = x_cam[i];
    }
    return {
        wxMin: xMin - 80,
        wxMax: xMax + 80,
        wzMin: z_cam_hogels - 80,
        wzMax: 80,
    };
}

function fitView() {
    const { wxMin, wxMax, wzMin, wzMax } = worldBounds();
    const PADDING = 60;
    scale = Math.min(
        (W - 2 * PADDING) / (wxMax - wxMin),
        (H - 2 * PADDING) / (wzMax - wzMin)
    );
    viewX = (wxMin + wxMax) / 2;
    viewZ = (wzMin + wzMax) / 2;
}

function toCanvas(wx, wz) {
    return [
        W / 2 + (wx - viewX) * scale,
        H / 2 - (wz - viewZ) * scale,   // z negative → downward on screen
    ];
}

function toWorld(cx, cy) {
    return [
        viewX + (cx - W / 2) / scale,
        viewZ - (cy - H / 2) / scale,
    ];
}

// ── Draw ───────────────────────────────────────────────────────────────────────
function draw() {
    ctx.clearRect(0, 0, W, H);

    const { wxMin, wxMax } = worldBounds();

    // z = 0 axis (hogel display plane) — always drawn
    ctx.strokeStyle = 'rgba(48,54,61,0.5)';
    ctx.lineWidth   = 0.5;
    const [ax0, ay0] = toCanvas(wxMin - 200, 0);
    const [ax1, ay1] = toCanvas(wxMax + 200, 0);
    ctx.beginPath(); ctx.moveTo(ax0, ay0); ctx.lineTo(ax1, ay1); ctx.stroke();

    // z_cam axis — only in perspective mode (in orthographic, camera is at −∞)
    if (!isOrthographic) {
        const [bx0, by0] = toCanvas(wxMin - 200, z_cam_hogels);
        const [bx1, by1] = toCanvas(wxMax + 200, z_cam_hogels);
        ctx.beginPath(); ctx.moveTo(bx0, by0); ctx.lineTo(bx1, by1); ctx.stroke();
    }

    // ── Rays ──────────────────────────────────────────────────────────────────
    ctx.lineWidth   = 0.01;
    ctx.strokeStyle = 'rgb(0,' + Math.floor(255 - 0.1 * (N - 1)) + ',' + Math.floor(0.1 * (N - 1)) + ')';
    ctx.beginPath();

    if (isOrthographic) {
        // Parallel rays at angle arctan(tan_theta[camIdx] * max_angle) to the vertical
        const t      = tan_theta[camIdx] * max_angle;
        const rayLen = - Math.max(W, H) * 3 / scale;   // world units — guaranteed off-screen
        console.log('rayLen', rayLen);
        console.log('scale', scale);
        for (let h = 0; h < N; h++) {
            const [hpx, hpy] = toCanvas(hogels[h], 0);
            const [epx, epy] = toCanvas(hogels[h] + t * rayLen, rayLen);
            ctx.moveTo(hpx, hpy);
            ctx.lineTo(epx, epy);
        }
    } else {
        // Perspective rays converging at the active camera position
        const [cpx, cpy] = toCanvas(x_cam[camIdx], z_cam_hogels);
        for (let h = 0; h < N; h++) {
            const [hpx, hpy] = toCanvas(hogels[h], 0);
            ctx.moveTo(cpx, cpy);
            ctx.lineTo(hpx, hpy);
        }
    }
    ctx.stroke();

    // ── Hogel dots ─────────────────────────────────────────────────────────────
    ctx.fillStyle = '#4fc3f7';
    const hr = Math.max(1.5, Math.min(4, scale * 2));
    ctx.beginPath();
    for (let h = 0; h < N; h++) {
        const [px, py] = toCanvas(hogels[h], 0);
        ctx.moveTo(px + hr, py);
        ctx.arc(px, py, hr, 0, Math.PI * 2);
    }
    ctx.fill();

    // ── Camera shape (perspective only) ────────────────────────────────────────
    if (!isOrthographic) {
        const ws = cameraWorldStep();   // uniform x spacing between adjacent cameras

        const [, py]  = toCanvas(x_cam[camIdx], z_cam_hogels);
        const [xm1]   = toCanvas(x_cam[camIdx] - ws,     z_cam_hogels);
        const [xp1]   = toCanvas(x_cam[camIdx] + ws,     z_cam_hogels);
        const [xm2]   = toCanvas(x_cam[camIdx] - 2 * ws, z_cam_hogels);
        const [xp2]   = toCanvas(x_cam[camIdx] + 2 * ws, z_cam_hogels);

        const innerW = xp1 - xm1;
        const innerH = innerW / 2;
        const outerW = xp2 - xm2;
        const outerH = innerW * 2;

        ctx.beginPath();
        ctx.rect(xm1, py,          innerW, innerH);   // narrow top (viewfinder)
        ctx.rect(xm2, py + innerH, outerW, outerH);   // wide bottom (body)
        ctx.fillStyle   = 'rgb(155,155,155)';
        ctx.fill();
        ctx.lineWidth   = 5;
        ctx.strokeStyle = '#000000';
        ctx.stroke();

        // Debug dots for all other camera positions (toggled with `)
        if (debugDots) {
            for (let i = 0; i < D; i++) {
                if (i === camIdx) continue;
                const [dpx, dpy] = toCanvas(x_cam[i], z_cam_hogels);
                ctx.beginPath();
                ctx.arc(dpx, dpy, 3.5, 0, Math.PI * 2);
                ctx.fillStyle = '#ef5350';
                ctx.fill();
            }
        }
    }

    // ── Axis labels ────────────────────────────────────────────────────────────
    ctx.fillStyle = '#8b949e';
    ctx.font      = '11px monospace';
    const [lhx, lhy] = toCanvas(wxMax + 10, 0);
    ctx.fillText('z = 0  (hogels)', lhx + 4, lhy + 4);
    if (!isOrthographic) {
        const [lcx, lcy] = toCanvas(wxMax + 10, z_cam_hogels);
        ctx.fillText('z_cam  (cameras)', lcx + 4, lcy + 4);
    }

    // ── Tile preview (bottom-right corner) — cropped from full quilt in JS ────────
    if (_quiltImage) {
        const { sx, sy, sw, sh } = tileRect(_quiltImage, camIdx);
        const pad    = 16;
        const dispW  = Math.min(W * 0.4, 400);
        console.log(dispW);
        const dispH  = dispW * (sh / sw);
        const tx     = pad;
        const ty     = H - dispH - pad;

        ctx.fillStyle = 'rgba(13,17,23,0.82)';
        ctx.fillRect(tx - 4, ty - 18, dispW + 8, dispH + 22);

        ctx.drawImage(_quiltImage, sx, sy, sw, sh, tx, ty, dispW, dispH);

        ctx.fillStyle = '#8b949e';
        ctx.font      = '10px monospace';
        ctx.fillText(`cam ${camIdx}`, tx, ty - 5);
    }
}

// ── Quilt fetch & tile crop ────────────────────────────────────────────────────
// Fetch the full quilt once per z_cam change; A/D crops in JS — no extra fetch.

// Tile grid layout — mirrors integral_to_quilt logic (D=81 → cols=9, rows=9)
let _quiltCols = Math.floor(Math.sqrt(D));
while (D % _quiltCols !== 0) _quiltCols++;
const _quiltRows = D / _quiltCols;

// Source rect in the quilt image for a given view index v
function tileRect(quiltImg, v) {
    const tileW   = quiltImg.naturalWidth  / _quiltCols;
    const tileH   = quiltImg.naturalHeight / _quiltRows;
    const tileCol = v % _quiltCols;
    const tileRow = Math.floor(v / _quiltCols);
    return {
        sx: tileCol * tileW,
        sy: (_quiltRows - 1 - tileRow) * tileH,   // row 0 stored at bottom
        sw: tileW,
        sh: tileH,
    };
}

let _fetchCtrl   = null;
let _sliderTimer = null;
let _quiltImage  = null;   // full quilt PNG decoded as Image
let _quiltBlobUrl = null;

async function fetchQuilt() {
    if (_fetchCtrl) _fetchCtrl.abort();
    _fetchCtrl = new AbortController();

    setTileStatus('loading…');

    const zCam = isOrthographic ? -1e9 : z_cam_hogels;

    try {
        const res = await fetch(`/quilt?z_cam=${zCam}`, { signal: _fetchCtrl.signal });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const blob    = await res.blob();
        const blobUrl = URL.createObjectURL(blob);

        const img  = new Image();
        img.onload = () => {
            if (_quiltBlobUrl) URL.revokeObjectURL(_quiltBlobUrl);
            _quiltBlobUrl = blobUrl;
            _quiltImage   = img;
            setTileStatus('');
            draw();
        };
        img.src = blobUrl;
    } catch (e) {
        if (e.name !== 'AbortError') {
            setTileStatus('server not running');
            _quiltImage = null;
            draw();
        }
    }
}

function setTileStatus(msg) {
    const el = document.getElementById('tileStatus');
    el.textContent   = msg;
    el.style.display = msg ? '' : 'none';
}

// ── Input handlers ─────────────────────────────────────────────────────────────
let dragging = false, dragStart = null, viewStart = null;

canvas.addEventListener('mousedown', e => {
    dragging  = true;
    dragStart = [e.clientX, e.clientY];
    viewStart = [viewX, viewZ];
});
canvas.addEventListener('mousemove', e => {
    if (!dragging) return;
    viewX = viewStart[0] - (e.clientX - dragStart[0]) / scale;
    viewZ = viewStart[1] + (e.clientY - dragStart[1]) / scale;
    draw();
});
canvas.addEventListener('mouseup',    () => { dragging = false; });
canvas.addEventListener('mouseleave', () => { dragging = false; });

canvas.addEventListener('wheel', e => {
    e.preventDefault();
    const factor   = e.deltaY < 0 ? 1.12 : 1 / 1.12;
    const [wx, wz] = toWorld(e.clientX, e.clientY);
    scale  *= factor;
    viewX   = wx - (wx - viewX) / factor;
    viewZ   = wz - (wz - viewZ) / factor;
    draw();
}, { passive: false });

window.addEventListener('keydown', e => {
    if (e.key === 'a' || e.key === 'A') {
        if (camIdx > 0) { camIdx--; refreshHUD(); draw(); }
    } else if (e.key === 'd' || e.key === 'D') {
        if (camIdx < D - 1) { camIdx++; refreshHUD(); draw(); }
    } else if (e.key === '`') {
        debugDots = !debugDots;
        draw();
    }
});

// Slider: update visualization immediately, debounce the expensive fetch
document.getElementById('ratioSlider').addEventListener('input', e => {
    camFovRatio = parseFloat(e.target.value);
    recomputeScene();
    fitView();
    draw();
    clearTimeout(_sliderTimer);
    _sliderTimer = setTimeout(fetchQuilt, 400);
});

// ── Init ───────────────────────────────────────────────────────────────────────
recomputeScene();
W = canvas.width  = window.innerWidth;
H = canvas.height = window.innerHeight;
fitView();
draw();
fetchQuilt();   // load quilt for initial z_cam on page load

window.addEventListener('resize', () => {
    W = canvas.width  = window.innerWidth;
    H = canvas.height = window.innerHeight;
    draw();   // preserve user's zoom/pan on resize
});
