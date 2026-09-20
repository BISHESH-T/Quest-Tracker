// --- 1. DOM ELEMENT SELECTORS ---
let x = document.getElementById('yes');
let y = document.getElementById('no');
let formContainer = document.getElementById('formContainer');
let inputForm = document.getElementById('inputForm'); 
let popupYes = document.getElementById('popupYes');
let overlayYes = document.getElementById('overlayYes');
let popupNo = document.getElementById('popupNo');
let overlayNo = document.getElementById('overlayNo');
let content = document.getElementById('content');

const fileName = document.getElementById('label');
const fileInput = document.getElementById('fileInput');

function getCSRFToken() {
    return document.cookie.split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];
}

// --- 2. INTERFACE WORKFLOW CONTROLLERS ---

if (x) {
    x.addEventListener('click', function(){
        if (formContainer) formContainer.style.display = "block";
        if (content) content.style.display = "none";
    });
}

if (y) {
    y.addEventListener('click', function(){
        if (content) content.style.display = "none";
        if (popupNo) popupNo.style.display = "block";
        if (overlayNo) overlayNo.style.display = "block";

        let balanceElem = document.getElementById("balance");
        if (balanceElem) {
            let currentBalance = parseInt(balanceElem.innerText) || 0;
            currentBalance -= 50;
            balanceElem.innerText = currentBalance;

            // Sync penalty to database
            fetch('/update_balance/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                body: JSON.stringify({ balance: currentBalance })
            });
        }
    });
}

// Handling Form Submission
if (inputForm) {
    inputForm.addEventListener('submit', function(event) {
        event.preventDefault(); 

        let formData = new FormData(inputForm);

        fetch('/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCSRFToken()
            },
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === "success") {
                // Update live balance score
                let balanceElem = document.getElementById("balance");
                if (balanceElem && data.new_balance !== undefined) {
                    balanceElem.innerText = data.new_balance;
                }

                // Show confirmation modal
                if (popupYes) popupYes.style.display = "block";
                if (overlayYes) overlayYes.style.display = "block";  
                if (formContainer) formContainer.style.display = "none";
            } else {
                alert(data.message || "Submission failed.");
            }
        })
        .catch(error => {
            console.error("Error submitting quest payloads:", error);
        });
    });
}

function closePopupYes() {
    if (popupYes) popupYes.style.display = "none";
    if (overlayYes) overlayYes.style.display = "none";
    
    if (content) content.style.display = "none";
    if (formContainer) formContainer.style.display = "none";
    
    // Reveal success countdown
    let yesTime = document.getElementById('yesTime');
    if (yesTime) {
        yesTime.style.display = "block"; 
    }
    
    if (inputForm) inputForm.reset();
    if (fileName) fileName.textContent = 'Choose File';
}

function closePopupNo(){
    if (popupNo) popupNo.style.display = "none";
    if (overlayNo) overlayNo.style.display = "none";
    
    if (content) content.style.display = "none";
    
    // Reveal failure countdown
    let noTime = document.getElementById('noTime');
    if (noTime) {
        noTime.style.display = "block";
    }
}

function updateLabel() {
    if (!fileInput || !fileName) return;
    let totalFiles = fileInput.files.length;
    
    if (totalFiles === 1) {
        fileName.textContent = fileInput.files[0].name;
    } 
    else if (totalFiles > 1) {
        fileName.textContent = `${totalFiles} files selected`;
    } 
    else {
        fileName.textContent = 'Choose File';
    }
}
 
// --- 3. DYNAMIC LIVE COUNTDOWN ENGINE ---
function startLiveCountdown() {
    const clocks = document.querySelectorAll('#countdown');
    if (clocks.length === 0) return;

    let secondsLeft = parseInt(clocks[0].getAttribute('data-seconds')) || 0;

    const interval = setInterval(() => {
        if (secondsLeft <= 0) {
            clocks.forEach(clock => clock.innerText = "00:00:00");
            clearInterval(interval);
            return;
        }

        secondsLeft--;

        let h = Math.floor(secondsLeft / 3600);
        let m = Math.floor((secondsLeft % 3600) / 60);
        let s = secondsLeft % 60;

        let standardHms = `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;

        clocks.forEach(clock => {
            clock.innerText = standardHms;
        });

    }, 1000);
}

// Start tracking loop
startLiveCountdown();