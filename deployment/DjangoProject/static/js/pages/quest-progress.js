document.addEventListener("DOMContentLoaded", function () {
    const page = document.getElementById("quest-progress-page");
    if (!page) {
        return;
    }

    const completeUrl = page.dataset.completeUrl;

    const activeQuest = JSON.parse(localStorage.getItem("activeQuest") || "null");
    const savedProgress = JSON.parse(localStorage.getItem("questProgress") || "null");

    const titleEl = document.getElementById("quest-title");
    const descEl = document.getElementById("quest-description");
    const typeEl = document.getElementById("quest-type");
    const cityEl = document.getElementById("quest-city");
    const limitsEl = document.getElementById("quest-group-limits");
    const durationEl = document.getElementById("quest-duration");

    const elapsedEl = document.getElementById("elapsed-minutes");
    const stepsEl = document.getElementById("progress-steps");
    const distanceEl = document.getElementById("progress-distance");
    const noteEl = document.getElementById("progress-note");
    const checkboxes = document.querySelectorAll(".progress-check");

    const saveBtn = document.getElementById("save-progress-btn");
    const finishBtn = document.getElementById("finish-quest-btn");
    const messageEl = document.getElementById("progress-message");

    function setMessage(message, type) {
        messageEl.className = `alert alert-${type} border mt-4 mb-0`;
        messageEl.textContent = message;
    }

    function getProgressData() {
        return {
            time_minutes: elapsedEl.value || 0,
            steps: stepsEl.value || 0,
            distance_km: distanceEl.value || 0,
            note: noteEl.value || "",
            checklist: Array.from(checkboxes).map(function (checkbox) {
                return checkbox.checked;
            }),
        };
    }

    function saveProgress() {
        const progressData = getProgressData();
        localStorage.setItem("questProgress", JSON.stringify(progressData));
        return progressData;
    }

    if (activeQuest) {
        titleEl.textContent = activeQuest.name || "Current quest";
        descEl.textContent = activeQuest.description || "Quest loaded.";
        typeEl.textContent = activeQuest.type || "N/A";
        cityEl.textContent = activeQuest.selected_city || "—";
        limitsEl.textContent = activeQuest.group_limits || "—";
        durationEl.textContent = activeQuest.duration ? `${activeQuest.duration} minutes` : "—";
    } else {
        setMessage("No active quest found. Please start one from the shuffle page.", "warning");
    }

    if (savedProgress) {
        elapsedEl.value = savedProgress.time_minutes || 0;
        stepsEl.value = savedProgress.steps || 0;
        distanceEl.value = savedProgress.distance_km || 0;
        noteEl.value = savedProgress.note || "";

        if (Array.isArray(savedProgress.checklist)) {
            checkboxes.forEach(function (checkbox, index) {
                checkbox.checked = !!savedProgress.checklist[index];
            });
        }
    }

    if (saveBtn) {
        saveBtn.addEventListener("click", function () {
            saveProgress();
            setMessage("Progress saved locally.", "success");
        });
    }

    if (finishBtn) {
        finishBtn.addEventListener("click", function () {
            if (!activeQuest || !activeQuest.run_id) {
                setMessage("You need an active quest before you can finish it.", "warning");
                return;
            }

            saveProgress();
            window.location.href = completeUrl;
        });
    }
});