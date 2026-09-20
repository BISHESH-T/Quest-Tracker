(function syncTimezone() {
    const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
    if (!tz) return;

    const current = document.cookie.split('; ')
        .find(r => r.startsWith('user_tz='))?.split('=')[1];

    if (current !== tz) {
        document.cookie = `user_tz=${tz}; path=/; max-age=31536000; SameSite=Lax`;

        // reload once per timezone value, so blocked cookies can't cause a loop
        if (sessionStorage.getItem('tzReloadedFor') !== tz) {
            sessionStorage.setItem('tzReloadedFor', tz);
            location.reload();
        }
    }
})();

// --- 1. DOM ELEMENT SELECTORS ---
const x = document.getElementById('yes');
const y = document.getElementById('no');
const formContainer = document.getElementById('formContainer');
const inputForm = document.getElementById('inputForm');
const popupYes = document.getElementById('popupYes');
const overlayYes = document.getElementById('overlayYes');
const popupNo = document.getElementById('popupNo');
const overlayNo = document.getElementById('overlayNo');
const content = document.getElementById('content');
const fileName = document.getElementById('label');
const fileInput = document.getElementById('fileInput');

const MAX_SIZE = 2 * 1024 * 1024; // 2 MB

function getCSRFToken() {
    return document.cookie.split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];
}

// --- 2. INTERFACE WORKFLOW CONTROLLERS ---

if (x) {
    x.addEventListener('click', function () {
        if (formContainer) formContainer.style.display = "block";
        if (content) content.style.display = "none";
    });
}

if (y) {
    y.addEventListener('click', async function () {
        y.disabled = true;
        if (x) x.disabled = true;

        try {
            const res = await fetch('/update_balance/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                body: JSON.stringify({ quest_status: "No" })
            });

            if (!res.ok) throw new Error(`Server returned ${res.status}`);
            const data = await res.json();

            const balanceElem = document.getElementById("balance");
            if (balanceElem) balanceElem.innerText = data.balance;

            if (content) content.style.display = "none";
            if (popupNo) popupNo.style.display = "block";
            if (overlayNo) overlayNo.style.display = "block";
        } catch (err) {
            console.error(err);
            alert("Couldn't save your answer. Please try again.");
            y.disabled = false;
            if (x) x.disabled = false;
        }
    });
}

// Handling form submission
if (inputForm) {
    const submitBtn = document.getElementById('submit');
    let submitting = false;

    function unlock() {
        submitting = false;
        submitBtn.disabled = false;
        submitBtn.value = "Submit";
    }

    inputForm.addEventListener('submit', function (event) {
        event.preventDefault();
        if (submitting) return; // ignore repeat clicks

        const tooBig = Array.from(fileInput.files).find(f => f.size > MAX_SIZE);
        if (tooBig) {
            alert(`"${tooBig.name}" is larger than 2 MB.`);
            return;
        }

        submitting = true;
        submitBtn.disabled = true;
        submitBtn.value = "Submitting...";

        const formData = new FormData(inputForm);

        fetch('/', {
            method: 'POST',
            headers: { 'X-CSRFToken': getCSRFToken() },
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === "success") {
                const balanceElem = document.getElementById("balance");
                if (balanceElem && data.new_balance !== undefined) {
                    balanceElem.innerText = data.new_balance;
                }
                if (popupYes) popupYes.style.display = "block";
                if (overlayYes) overlayYes.style.display = "block";
                if (formContainer) formContainer.style.display = "none";
                // button stays locked: the day is done
            } else {
                alert(data.message || "Submission failed.");
                unlock();
            }
        })
        .catch(error => {
            console.error("Error submitting quest payloads:", error);
            alert("Something went wrong. Please try again.");
            unlock();
        });
    });
}

function closePopupYes() {
    if (popupYes) popupYes.style.display = "none";
    if (overlayYes) overlayYes.style.display = "none";

    if (content) content.style.display = "none";
    if (formContainer) formContainer.style.display = "none";

    const yesTime = document.getElementById('yesTime');
    if (yesTime) yesTime.style.display = "block";

    if (inputForm) inputForm.reset();
    if (fileName) fileName.textContent = 'Choose file';
}

function closePopupNo() {
    if (popupNo) popupNo.style.display = "none";
    if (overlayNo) overlayNo.style.display = "none";

    if (content) content.style.display = "none";

    const noTime = document.getElementById('noTime');
    if (noTime) noTime.style.display = "block";
}

function updateLabel() {
    if (!fileInput || !fileName) return;

    const tooBig = Array.from(fileInput.files).find(f => f.size > MAX_SIZE);
    if (tooBig) {
        alert(`"${tooBig.name}" is larger than 2 MB.`);
        fileInput.value = "";
        fileName.textContent = 'Choose file';
        return;
    }

    const totalFiles = fileInput.files.length;
    if (totalFiles === 1) {
        fileName.textContent = fileInput.files[0].name;
    } else if (totalFiles > 1) {
        fileName.textContent = `${totalFiles} files selected`;
    } else {
        fileName.textContent = 'Choose file';
    }
}

// --- 3. DYNAMIC LIVE COUNTDOWN ENGINE ---
function startLiveCountdown() {
    const clocks = document.querySelectorAll('.countdown');
    if (clocks.length === 0) return;

    let secondsLeft = parseInt(clocks[0].getAttribute('data-seconds')) || 0;

    const interval = setInterval(() => {
        if (secondsLeft <= 0) {
            clocks.forEach(clock => clock.innerText = "00:00:00");
            clearInterval(interval);
            return;
        }

        secondsLeft--;

        const h = Math.floor(secondsLeft / 3600);
        const m = Math.floor((secondsLeft % 3600) / 60);
        const s = secondsLeft % 60;

        const hms = `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
        clocks.forEach(clock => { clock.innerText = hms; });
    }, 1000);
}

startLiveCountdown();