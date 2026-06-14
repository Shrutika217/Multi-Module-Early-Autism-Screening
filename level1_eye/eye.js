const video = document.getElementById("video");
const canvas = document.getElementById("gameCanvas");
const ctx = canvas.getContext("2d");

canvas.width = window.innerWidth;
canvas.height = window.innerHeight;

let gazeData = [];
let running = false;

let currentTry = 1;
let totalTries = 3;

let predictions = [];
let confidences = [];

// 🔥 store latest gaze point
let currentGaze = null;

// 🔥 pattern type
let patternType = 1;

let animal = {
    x: 0,
    y: canvas.height / 2,
    speed: 5
};

// ======================
// MEDIAPIPE SETUP
// ======================

const faceMesh = new FaceMesh({
    locateFile: (file) => {
        return `https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh/${file}`;
    }
});

faceMesh.setOptions({
    maxNumFaces: 1,
    refineLandmarks: true,
    minDetectionConfidence: 0.7,
    minTrackingConfidence: 0.7
});

faceMesh.onResults(onResults);

// ======================
// CAMERA
// ======================

const camera = new Camera(video, {
    onFrame: async () => {
        await faceMesh.send({ image: video });
    },
    width: 640,
    height: 480
});

camera.start();

// ======================
// LANDMARK PROCESSING
// ======================

function onResults(results) {
    if (!results.multiFaceLandmarks) return;

    const landmarks = results.multiFaceLandmarks[0];

    const leftEye = landmarks[33];
    const rightEye = landmarks[263];

    const x = ((leftEye.x + rightEye.x) / 2) * canvas.width;
    const y = ((leftEye.y + rightEye.y) / 2) * canvas.height;

    if (!isFinite(x) || !isFinite(y)) return;

    currentGaze = { x, y };

    if (running) {
        gazeData.push({ x, y });
    }
}

// ======================
// START GAME
// ======================

function startGame() {
    currentTry = 1;
    predictions = [];
    confidences = [];

    runSingleTry();
}

// ======================
// RUN ONE TRY
// ======================

function runSingleTry() {
    gazeData = [];
    running = true;

    // 🔥 change pattern per try
    patternType = currentTry;

    // 🔥 reset animal
    animal.x = 0;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    document.getElementById("result").innerText =
        `Running Try ${currentTry}...`;

    gameLoop();

    setTimeout(endGame, 8000);
}

// ======================
// GAME LOOP
// ======================

function gameLoop() {
    if (!running) return;

    ctx.fillStyle = "rgba(0,0,0,0.15)";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    moveAnimal();
    drawAnimal();

    // 🔥 draw gaze dot here (NOT in onResults)
    if (currentGaze) {
        ctx.beginPath();
        ctx.arc(currentGaze.x, currentGaze.y, 6, 0, Math.PI * 2);
        ctx.fillStyle = "red";
        ctx.fill();
    }

    requestAnimationFrame(gameLoop);
}

// ======================
// ANIMAL MOVEMENT (3 PATTERNS)
// ======================

function moveAnimal() {

    // Pattern 1: Wave
    if (patternType === 1) {
        animal.x += animal.speed;
        animal.y = canvas.height / 2 + 150 * Math.sin(animal.x * 0.02);
    }

    // Pattern 2: Zig-Zag
    else if (patternType === 2) {
        animal.x += animal.speed;
        let step = Math.floor(animal.x / 100) % 2;
        animal.y = step === 0 ? canvas.height * 0.3 : canvas.height * 0.7;
    }

    // Pattern 3: Circular
    else if (patternType === 3) {

        // speed changes dynamically
        let dynamicSpeed = 3 + 4 * Math.abs(Math.sin(animal.x * 0.01));

        animal.x += dynamicSpeed;

        animal.y = canvas.height / 2;
    }

    // reset when reaching edge
    if (animal.x > canvas.width) {
        animal.x = 0;
    }

    if (animal.x > canvas.width) animal.x = 0;
}

function drawAnimal() {
    ctx.beginPath();
    ctx.arc(animal.x, animal.y, 20, 0, Math.PI * 2);
    ctx.fillStyle = "orange";
    ctx.fill();
}

// ======================
// SMOOTHING
// ======================

function smoothGaze(data, windowSize = 5) {
    let smoothed = [];

    for (let i = 0; i < data.length; i++) {
        let start = Math.max(0, i - windowSize);
        let subset = data.slice(start, i + 1);

        let avgX = subset.reduce((s, p) => s + p.x, 0) / subset.length;
        let avgY = subset.reduce((s, p) => s + p.y, 0) / subset.length;

        smoothed.push({ x: avgX, y: avgY });
    }

    return smoothed;
}

// ======================
// FEATURE EXTRACTION
// ======================

function extractFeatures(data) {

    if (data.length < 20) return [0,0,0,0,0,0];

    let total_path = 0;
    let segments = [];

    for (let i = 1; i < data.length; i++) {
        let dx = data[i].x - data[i-1].x;
        let dy = data[i].y - data[i-1].y;

        let dist = Math.sqrt(dx*dx + dy*dy);
        if (!isFinite(dist)) continue;

        total_path += dist;
        segments.push(dist);
    }

    let avg_length = segments.length
        ? segments.reduce((a,b)=>a+b,0)/segments.length
        : 0;

    let num_segments = segments.length;

    let xs = data.map(p => p.x);
    let ys = data.map(p => p.y);

    let spread_x = std(xs);
    let spread_y = std(ys);

    let density = data.length / (canvas.width * canvas.height);

    return [
        total_path,
        avg_length,
        num_segments,
        density,
        spread_x,
        spread_y
    ];
}

function std(arr) {
    let mean = arr.reduce((a,b)=>a+b,0)/arr.length;
    return Math.sqrt(arr.map(x => (x-mean)**2).reduce((a,b)=>a+b)/arr.length);
}

// ======================
// END TRY
// ======================

async function endGame() {

    running = false;

    // 🔥 remove dot after game
    currentGaze = null;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    let smoothed = smoothGaze(gazeData);
    let features = extractFeatures(smoothed);

    console.log(`Try ${currentTry} Features:`, features);

    let response = await fetch("http://127.0.0.1:8000/predict-eye", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({features: features})
    });

    let result = await response.json();

    console.log(`Try ${currentTry} Prediction:`, result.prediction);
    console.log(`Try ${currentTry} Confidence:`, result.confidence);

    predictions.push(result.prediction);
    confidences.push(result.confidence);

    document.getElementById("result").innerText =
    `Try ${currentTry}: ${result.prediction} (${(result.confidence * 100).toFixed(1)}%)`;

    currentTry++;

    if (currentTry <= totalTries) {
        setTimeout(runSingleTry, 2000);
    } else {
        showFinalResult();
    }
}

// ======================
// FINAL RESULT
// ======================

function showFinalResult() {

    let autisticCount = predictions.filter(p => p === "Autistic").length;

    let finalPrediction = autisticCount >= 2 ? "Autistic" : "Non-Autistic";

    let avgConfidence =
        confidences.reduce((a,b)=>a+b,0) / confidences.length;

    document.getElementById("result").innerText =
        `FINAL RESULT: ${finalPrediction} (${avgConfidence.toFixed(2)}% avg confidence)`;

    console.log("Final Prediction:", finalPrediction);
    console.log("Average Confidence:", avgConfidence);

    document.getElementById("result").innerText =
        `FINAL RESULT: ${finalPrediction} (${avgConfidence.toFixed(2)}% avg confidence)`;

    // 🔥 OPTIONAL: store result for later use (important!)
    localStorage.setItem("level1_result", finalPrediction);
    localStorage.setItem("level1_confidence", avgConfidence);

    // 🔥 ALWAYS move to Level 2
    setTimeout(() => {
        window.location.href = "../level2_face/face.html";
    }, 2000);
    }

function restartLevel1() {
    window.location.reload();
}