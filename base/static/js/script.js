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
let yesTime = document.getElementById('yesTime');
let noTime = document.getElementById('noTime');
let count = parseInt(document.getElementById("balance").innerText);

const fileName = document.getElementById('label');
const fileInput = document.getElementById('fileInput');

// --- 2. ASYNCHRONOUS DATABASE SYNC ENGINE ---
function balanceUpdate() {
    document.getElementById("balance").innerText = count;

    // Send an AJAX request to update the balance in the database
    fetch('/update_balance/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({ balance: count })
    });
}

// Fixed balance lookup function signature assignment wrapper
function updateLiveUIBalance(amount) {
    count = amount;
    balanceUpdate();
}

function getCSRFToken() {
    return document.cookie.split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];
}

// --- 3. INTERFACE WORKFLOW CONTROLLERS ---

// Clicking "YES" brings up the submission text/file form container
if (x) {
    x.addEventListener('click', function(){
        formContainer.style.display = "block";
        content.style.display = "none";
    });
}

// Clicking "NO" applies an instant penalty stream via background AJAX channel
if (y) {
    y.addEventListener('click', function(){
        content.style.display = "none";
        popupNo.style.display = "block";
        overlayNo.style.display = "block";

        count -= 50;
        balanceUpdate();
    });
}

// Handling the "YES" Path Form Submission via Asynchronous AJAX Fetch
if (inputForm) {
    inputForm.addEventListener('submit', function(event) {
        event.preventDefault(); // Stop the browser from refreshing the page!

        // Gather text input values and media binary assets automatically
        let formData = new FormData(inputForm);

        // Ship the payload data asynchronously straight to your Django home view
        fetch('/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCSRFToken()
            },
            body: formData
        })
        .then(response => {
            if (response.ok) {
                // Award points locally and sync with the database record row
                count += 10;
                balanceUpdate();

                // Open the confirmation dialog popup and hide the workspace inputs
                popupYes.style.display = "block";
                overlayYes.style.display = "block";  
                formContainer.style.display = "none";
            } else {
                alert("Submission failed. Please check your network or server logs.");
            }
        })
        .catch(error => {
            console.error("Error submitting quest payloads:", error);
        });
    });
}

// Transition functions triggered by clicking the "Done" buttons inside your popups
function closePopupYes() {
    popupYes.style.display = "none";
    overlayYes.style.display = "none";
    
    // 1. Smoothly reveal the live ticking midnight countdown element container
    if (yesTime) yesTime.style.display = "block"; 
    
    // 2. Clear out the internal form pointers safely without destroying DOM variables
    if (inputForm) {
        inputForm.reset();
    }
    
    // 3. Reset the visual file selector string safely back to original state
    if (fileName) {
        fileName.textContent = 'Choose File';
    }
}

function closePopupNo(){
    popupNo.style.display = "none";
    overlayNo.style.display = "none";
    if (noTime) noTime.style.display = "block";
}

function newPrompt(){
    if (content) content.style.display = "none";
}

// Handles custom styling labels for single or multiple uploaded attachment counts
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
 
// --- 4. DYNAMIC LIVE COUNTDOWN ENGINE ---
function startLiveCountdown() {
    const clocks = document.querySelectorAll('[id="countdown"]');
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

// Fire up tracking loops
startLiveCountdown();