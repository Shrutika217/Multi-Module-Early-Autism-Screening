const video = document.getElementById("video");
const canvas = document.getElementById("canvas");
const ctx = canvas.getContext("2d");

let stream = null;
let captured = false;

// Buttons
const captureBtn = document.querySelector(".capture");
const predictBtn = document.querySelector(".predict");

// ======================
// START CAMERA
// ======================
async function startCamera() {
    stream = await navigator.mediaDevices.getUserMedia({ video: true });
    video.srcObject = stream;
}
startCamera();

// Disable predict initially
predictBtn.disabled = true;

// ======================
// 📸 CAPTURE (REAL FREEZE)
// ======================
function capture() {

    if (captured) return;

    if (!video.videoWidth) {
        alert("Camera not ready");
        return;
    }

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    ctx.drawImage(video, 0, 0);

    // 🔥 HARD FREEZE
    stream.getTracks().forEach(track => track.stop());

    video.style.display = "none";
    canvas.style.display = "block";

    captured = true;

    // 🔥 BUTTON CONTROL
    captureBtn.disabled = true;
    predictBtn.disabled = false;

    console.log("✅ Frame captured and frozen");

    document.getElementById("instructions").innerHTML =
    "Image captured <br>Now click <b style='color:#00c6ff;'>Predict</b>";
}

// ======================
// 🤖 PREDICT (ONLY AFTER CAPTURE)
// ======================
async function predict() {

    if (!captured) {
        alert("Capture image first!");
        return;
    }

    console.log("🚀 Sending to backend...");

    canvas.toBlob(async (blob) => {

        let formData = new FormData();
        formData.append("file", blob, "face.jpg");

        try {
            let response = await fetch("http://127.0.0.1:8000/predict-face", {
                method: "POST",
                body: formData
            });

            let data = await response.json();

            console.log("✅ Backend response:", data);

            document.getElementById("result").innerHTML =
                `<b>${data.prediction}</b><br>
                 Confidence: ${data.confidence.toFixed(2)}%`;

            document.getElementById("nextLevel").style.display = "inline-block";

        } catch (err) {
            console.error("❌ Backend error:", err);
        }
    });
}

// ======================
// 🔁 RETRY
// ======================
function retry() {
    window.location.reload();
}

function goToLevel3() {
    window.location.href = "../level3_ques/ques.html";
}