const questions = [
    "1. Does your child look at you when you call their name?",
    "2. Is it easy to make eye contact with your child?",
    "3. Does your child point to ask for something?",
    "4. Does your child point to share interest with you?",
    "5. Does your child engage in pretend play?",
    "6. Does your child follow where you are looking?",
    "7. Does your child try to comfort someone who is upset?",
    "8. How often does your child use meaningful words to communicate?",
    "9. Does your child use simple gestures (like waving or nodding)?",
    "10. Does your child stare at nothing with no clear reason?"
  ];
  
  let current = 0;
  let answers = [];
  window.submitted = false;
  // =======================
  // RENDER QUESTION
  // =======================
  function renderQuestion(direction = "right") {
  
    const card = document.getElementById("card");
  
    card.classList.remove("slide-in-left", "slide-in-right");
    void card.offsetWidth;
  
    card.classList.add(direction === "right" ? "slide-in-right" : "slide-in-left");
  
    document.getElementById("question").innerText = questions[current];
  
    document.querySelectorAll(".likert button").forEach(btn => {
      btn.classList.remove("active");
    });
  
    if (answers[current]) {
      document.querySelectorAll(".likert button").forEach(btn => {
        if (btn.innerText === answers[current]) {
          btn.classList.add("active");
        }
      });
    }
  }
  
  // =======================
  // SELECT OPTION
  // =======================
  function selectOption(val, event) {
    answers[current] = val;
  
    document.querySelectorAll(".likert button").forEach(btn => {
      btn.classList.remove("active");
    });
  
    event.target.classList.add("active");
  }
  
  // =======================
  // NEXT
  // =======================
  function nextQuestion() {
  
    if (!answers[current]) {
      alert("Please select an option");
      return;
    }
  
    if (current < questions.length - 1) {
      current++;
      renderQuestion("right");
    } else {
      submitForm();
    }
  }
  
  // =======================
  // PREVIOUS
  // =======================
  function prevQuestion() {
    if (current > 0) {
      current--;
      renderQuestion("left");
    }
  }
  
  // =======================
  // START
  // =======================
  function startQuestions() {
  
    const age = document.getElementById("age").value;
    const gender = document.getElementById("gender").value;
    const jaundice = document.getElementById("jaundice").value;
    const family = document.getElementById("family_asd").value;
    const ethnicity = document.getElementById("ethnicity").value;
    const who = document.getElementById("who_completed").value;

  
    if (!age || !gender || !jaundice || !family || !ethnicity || !who) {
        alert("Please fill all details");
        return;
    }
  
    document.getElementById("demographics").style.display = "none";
    document.getElementById("questions-section").style.display = "flex";
  
    current = 0;
    renderQuestion();
  }
  
  // =======================
  // SUBMIT (FIXED)
  // =======================
  async function submitForm() {

    // 🔥 prevent multiple submissions
    if (window.submitted) return;
    window.submitted = true;
  
    // =======================
    // CUSTOM BINARY LOGIC
    // =======================
    function convertToBinary(responses) {
      return responses.map((r, i) => {
  
        // A1–A9
        if (i < 9) {
          return ["Sometimes", "Rarely", "Never"].includes(r) ? 1 : 0;
        }
  
        // A10 (reverse logic)
        if (i === 9) {
          return ["Always", "Usually", "Sometimes"].includes(r) ? 1 : 0;
        }
  
      });
    }
  
    // =======================
    // BUILD PAYLOAD
    // =======================
    const payload = {
      responses: convertToBinary(answers),   // 🔥 FIXED
      age: parseFloat(document.getElementById("age").value),
      gender: document.getElementById("gender").value,
      jaundice: document.getElementById("jaundice").value,
      family_asd: document.getElementById("family_asd").value,
      ethnicity: document.getElementById("ethnicity").value,          // 🔥 NEW
      who_completed: document.getElementById("who_completed").value   // 🔥 NEW
    };
  
    console.log("🚀 Sending payload:", payload);
  
    try {
      const res = await fetch("http://127.0.0.1:8000/predict-ques", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
      });
  
      // 🔥 error handling
      if (!res.ok) {
        throw new Error("Server error");
      }
  
      const data = await res.json();
  
      console.log("✅ Response:", data);
  
      // 🔥 store result
      localStorage.setItem("ques_prediction", data.prediction);
      localStorage.setItem("ques_confidence", data.confidence);
  
      const resultDiv = document.getElementById("result");
  
      resultDiv.innerHTML = `
        <div style="margin-top:30px; text-align:center;">
          <h2>Screening Result</h2>
          <p><b>Prediction:</b> ${data.prediction}</p>
          <p><b>Confidence:</b> ${data.confidence.toFixed(2)}%</p>
  
          <button onclick="goToConsent()" style="
            margin-top:20px;
            width: 250px;
            height: 50px;
            border-radius: 10px;
            border: none;
            font-size: 16px;
            font-weight: bold;
            background: #00c6ff;
            color: white;
            cursor: pointer;
          ">
            Continue to Final Step
          </button>
        </div>
      `;
  
      // 🔥 fade card after submit
      document.getElementById("card").style.opacity = "0.5";
  
      // 🔥 disable buttons
      document.querySelectorAll(".likert button").forEach(btn => {
        btn.disabled = true;
      });
  
      document.querySelectorAll(".nav-buttons button").forEach(btn => {
        btn.disabled = true;
      });
  
      // 🔥 scroll to result
      resultDiv.scrollIntoView({ behavior: "smooth" });
  
    } catch (err) {
      console.error("❌ Error:", err);
      alert("Something went wrong. Please try again.");
      window.submitted = false; // allow retry
    }
  }
  
  // =======================
  // CONSENT REDIRECT
  // =======================
  function goToConsent() {
    window.location.href = "consent.html";
  }
  
  // =======================
  // RESET
  // =======================
  function restartForm() {
  
    current = 0;
    answers = [];
    window.submitted = false; // reset submit flag
  
    document.getElementById("demographics").style.display = "flex";
    document.getElementById("questions-section").style.display = "none";
  
    document.getElementById("result").innerHTML = "";
  
    document.getElementById("age").value = "";
    document.getElementById("gender").selectedIndex = 0;
    document.getElementById("jaundice").selectedIndex = 0;
    document.getElementById("family_asd").selectedIndex = 0;
  }
  
  // =======================
  // DOWNLOAD
  // =======================
  function downloadReport() {
    window.open("http://127.0.0.1:8000/download-report", "_blank");
  }