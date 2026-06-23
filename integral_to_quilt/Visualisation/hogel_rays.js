// ── Scene parameters ───────────────────────────────────────────────────────────
const N           = 819;
const D           = 81;
const FOV_DEG     = 60.0;
const max_angle   = Math.tan((FOV_DEG / 2) * Math.PI / 180);
const disp_center = (N - 1) / 2.0;

// tan_theta[v] for each directional sample — fixed, independent of z_cam
const tan_theta = Float64Array.from({ length: D }, (_, v) => 1 - 2 * v / (D - 1));

// Hogel positions along the display plane (z = 0)
const hogels = Float64Array.from({ length: N }, (_, i) => i);

// ── Camera state ───────────────────────────────────────────────────────────────
// Derivation:
//   tan(cam_fov/2) = (N/2) / |z_cam|
//   let ratio = tan(cam_fov/2) / max_angle
//   => z_cam = -(N/2) / (ratio * max_angle)
let camFovRatio  = 0.5;
let z_cam_hogels = 0;       // computed in recomputeScene()
const x_cam      = new Float64Array(D);

let camIdx    = Math.floor(D / 2);   // current camera, start at centre
let debugDots = false;

function recomputeScene() {
    z_cam_hogels = -(N / 2) / (camFovRatio * max_angle);
    for (let i = 0; i < D; i++) {
        x_cam[i] = disp_center + z_cam_hogels * tan_theta[i] * max_angle;
    }
    document.getElementById('hZ').textContent    = z_cam_hogels.toFixed(1);
    document.getElementById('hRatio').textContent = camFovRatio.toFixed(2);
    refreshHUD();
}

function refreshHUD() {
    document.getElementById('hCI').textContent = camIdx;
    document.getElementById('hCX').textContent = x_cam[camIdx].toFixed(2);
    document.getElementById('hCT').textContent =
        (Math.atan(max_angle * tan_theta[camIdx]) * 180 / Math.PI).toFixed(2) + '°';
}

// ── Canvas & viewport ──────────────────────────────────────────────────────────
const canvas = document.getElementById('c');
const ctx    = canvas.getContext('2d');
let W = 0, H = 0;

let viewX = 0, viewZ = 0, scale = 1;

function worldBounds() {
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

    // Reference axis lines
    ctx.strokeStyle = 'rgba(48,54,61,0.5)';
    ctx.lineWidth   = 0.5;

    const [ax0, ay0] = toCanvas(wxMin - 200, 0);
    const [ax1, ay1] = toCanvas(wxMax + 200, 0);
    ctx.beginPath(); ctx.moveTo(ax0, ay0); ctx.lineTo(ax1, ay1); ctx.stroke();

    const [bx0, by0] = toCanvas(wxMin - 200, z_cam_hogels);
    const [bx1, by1] = toCanvas(wxMax + 200, z_cam_hogels);
    ctx.beginPath(); ctx.moveTo(bx0, by0); ctx.lineTo(bx1, by1); ctx.stroke();

    // Rays from active camera to every hogel — single path, single stroke call for clean rendering
    const [cpx, cpy] = toCanvas(x_cam[camIdx], z_cam_hogels);
    ctx.lineWidth   = 0.01;
    ctx.strokeStyle = 'rgb(0,' + Math.floor(255 - 0.1 * (N - 1)) + ',' + Math.floor(0.1 * (N - 1)) + ')';
    ctx.beginPath();
    for (let h = 0; h < N; h++) {
        const [hpx, hpy] = toCanvas(hogels[h], 0);
        ctx.moveTo(cpx, cpy);
        ctx.lineTo(hpx, hpy);
    }
    ctx.stroke();

    // Hogel dots
    ctx.fillStyle = '#4fc3f7';
    const hr = Math.max(1.5, Math.min(4, scale * 2));
    ctx.beginPath();
    for (let h = 0; h < N; h++) {
        const [px, py] = toCanvas(hogels[h], 0);
        ctx.moveTo(px + hr, py);
        ctx.arc(px, py, hr, 0, Math.PI * 2);
    }
    ctx.fill();

    // Camera shape — world-unit step between adjacent camera positions (uniform, safe at edges)
    const worldStep = z_cam_hogels * (-2 / (D - 1));   // x_cam[i+1] - x_cam[i], always positive

    for (let i = 0; i < D; i++) {
        const [px, py] = toCanvas(x_cam[i], z_cam_hogels);
        const isCurrent = i === camIdx;

        if (isCurrent) {
            // Extrapolate neighbours from uniform step — no out-of-bounds access at edges
            const [xm1] = toCanvas(x_cam[i] - worldStep, z_cam_hogels);
            const [xp1] = toCanvas(x_cam[i] + worldStep, z_cam_hogels);
            const [xm2] = toCanvas(x_cam[i] - 2 * worldStep, z_cam_hogels);
            const [xp2] = toCanvas(x_cam[i] + 2 * worldStep, z_cam_hogels);

            const innerW = xp1 - xm1;
            const innerH = innerW / 2;
            const outerW = xp2 - xm2;
            const outerH = innerW * 2;

            ctx.beginPath();
            ctx.rect(xm1, py,          innerW, innerH);   // top narrow part
            ctx.rect(xm2, py + innerH, outerW, outerH);   // bottom wide body
            ctx.fillStyle   = 'rgb(155,155,155)';
            ctx.fill();
            ctx.lineWidth   = 5;
            ctx.strokeStyle = '#000000';
            ctx.stroke();
        } else if (debugDots) {
            ctx.beginPath();
            ctx.arc(px, py, 3.5, 0, Math.PI * 2);
            ctx.fillStyle = '#ef5350';
            ctx.fill();
        }
    }

    // Axis labels
    ctx.fillStyle = '#8b949e';
    ctx.font = '11px monospace';
    const [lhx, lhy] = toCanvas(wxMax + 10, 0);
    ctx.fillText('z = 0  (hogels)', lhx + 4, lhy + 4);
    const [lcx, lcy] = toCanvas(wxMax + 10, z_cam_hogels);
    ctx.fillText('z_cam  (cameras)', lcx + 4, lcy + 4);
}

// ── Input handlers ─────────────────────────────────────────────────────────────

// Pan
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

// Zoom toward cursor
canvas.addEventListener('wheel', e => {
    e.preventDefault();
    const factor     = e.deltaY < 0 ? 1.12 : 1 / 1.12;
    const [wx, wz]   = toWorld(e.clientX, e.clientY);
    scale           *= factor;
    viewX            = wx - (wx - viewX) / factor;
    viewZ            = wz - (wz - viewZ) / factor;
    draw();
}, { passive: false });

// Keyboard: A/D step camera, ` toggle debug
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

// Ratio slider — refit view since world extents change
document.getElementById('ratioSlider').addEventListener('input', e => {
    camFovRatio = parseFloat(e.target.value);
    recomputeScene();
    fitView();
    draw();
});

// ── Init ───────────────────────────────────────────────────────────────────────
recomputeScene();
W = canvas.width  = window.innerWidth;
H = canvas.height = window.innerHeight;
fitView();
draw();

window.addEventListener('resize', () => {
    W = canvas.width  = window.innerWidth;
    H = canvas.height = window.innerHeight;
    draw();   // preserve user's zoom/pan on resize
});
