function getCookie(name) {
    let cookieValue = null;

    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");

        for (let i = 0; i < cookies.length; i += 1) {
            const cookie = cookies[i].trim();

            if (cookie.substring(0, name.length + 1) === `${name}=`) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }

    return cookieValue;
}

document.addEventListener("DOMContentLoaded", function () {
    const page = document.getElementById("quest-complete-page");
    if (!page) {
        return;
    }

    const completeApiUrl = page.dataset.completeApiUrl;
    const publishUrl = page.dataset.publishUrl;
    const feedUrl = page.dataset.feedUrl;

    const activeQuest = JSON.parse(localStorage.getItem("activeQuest") || "null");
    const savedProgress = JSON.parse(localStorage.getItem("questProgress") || "null");
    const completedQuestRun = JSON.parse(localStorage.getItem("completedQuestRun") || "null");

    const titleEl = document.getElementById("complete-quest-title");
    const descEl = document.getElementById("complete-quest-description");
    const typeEl = document.getElementById("complete-quest-type");
    const cityEl = document.getElementById("complete-quest-city");
    const limitsEl = document.getElementById("complete-quest-group-limits");
    const durationEl = document.getElementById("complete-quest-duration");

    const timeEl = document.getElementById("time-minutes");
    const distanceEl = document.getElementById("distance-km");
    const stepsEl = document.getElementById("steps");
    const noteEl = document.getElementById("completion-note");
    const proofEl = document.getElementById("proof-file");
    const formEl = document.getElementById("complete-quest-form");
    const messageEl = document.getElementById("complete-message");
    const submitBtn = document.getElementById("submit-completion-btn");

    const postCompleteActions = document.getElementById("post-complete-actions");
    const publishPostBtn = document.getElementById("publish-post-btn");
    const publishMessageEl = document.getElementById("publish-message");

    let currentCompletedRun = completedQuestRun;

    function setMessage(message, type) {
        messageEl.className = `alert alert-${type} border mt-4 mb-0`;
        messageEl.textContent = message;
    }

    function setPublishMessage(message, type) {
        publishMessageEl.className = `alert alert-${type} border mt-3 mb-0`;
        publishMessageEl.textContent = message;
    }

    function showPostCompleteActions() {
        postCompleteActions.classList.remove("d-none");
    }

    function populateQuestSummary(quest) {
        if (!quest) {
            return;
        }

        titleEl.textContent = quest.name || "Current quest";
        descEl.textContent = quest.description || "Quest loaded.";
        typeEl.textContent = quest.type || "N/A";
        cityEl.textContent = quest.selected_city || "—";
        limitsEl.textContent = quest.group_limits || "—";
        durationEl.textContent = quest.duration ? `${quest.duration} minutes` : "—";
    }

    if (activeQuest) {
        populateQuestSummary(activeQuest);
    } else if (currentCompletedRun && currentCompletedRun.quest) {
        populateQuestSummary(currentCompletedRun.quest);
        showPostCompleteActions();
        setMessage("This quest was already completed. You can still publish it to the feed.", "success");
    } else {
        setMessage("No active quest run found. Start a quest first.", "warning");
    }

    if (
        savedProgress &&
        activeQuest &&
        savedProgress.run_id &&
        savedProgress.run_id === activeQuest.run_id
    ) {
        timeEl.value = savedProgress.time_minutes || "";
        distanceEl.value = savedProgress.distance_km || "";
        stepsEl.value = savedProgress.steps || "";
        noteEl.value = savedProgress.note || "";
    }

    if (currentCompletedRun && activeQuest && currentCompletedRun.run_id === activeQuest.run_id) {
        showPostCompleteActions();
    }

    if (formEl) {
        formEl.addEventListener("submit", async function (event) {
            event.preventDefault();

            if (!activeQuest || !activeQuest.run_id) {
                setMessage("No active quest run found. Start a quest first.", "danger");
                return;
            }

            submitBtn.disabled = true;
            submitBtn.textContent = "Submitting...";

            const fd = new FormData();
            fd.append("run_id", activeQuest.run_id);
            fd.append("time_minutes", timeEl.value || "");
            fd.append("distance_km", distanceEl.value || "");
            fd.append("steps", stepsEl.value || "");
            fd.append("note", noteEl.value || "");

            if (proofEl.files.length > 0) {
                fd.append("proof_file", proofEl.files[0]);
            }

            try {
                const response = await fetch(completeApiUrl, {
                    method: "POST",
                    headers: {
                        "X-CSRFToken": getCookie("csrftoken"),
                    },
                    body: fd,
                });

                const data = await response.json();

                if (!response.ok) {
                    setMessage(data.error || "Failed to complete quest.", "danger");
                    submitBtn.disabled = false;
                    submitBtn.textContent = "Submit completion";
                    return;
                }

                currentCompletedRun = {
                    run_id: data.run_id,
                    quest: activeQuest,
                    completion: data,
                };

                localStorage.setItem("completedQuestRun", JSON.stringify(currentCompletedRun));
                localStorage.removeItem("questProgress");
                localStorage.removeItem("activeQuest");

                setMessage("Quest completed successfully.", "success");
                showPostCompleteActions();

                submitBtn.disabled = true;
                submitBtn.textContent = "Quest completed";
            } catch (error) {
                setMessage("Unexpected error while submitting quest completion.", "danger");
                submitBtn.disabled = false;
                submitBtn.textContent = "Submit completion";
            }
        });
    }

    if (publishPostBtn) {
        publishPostBtn.addEventListener("click", async function () {
            if (!currentCompletedRun || !currentCompletedRun.run_id) {
                setPublishMessage("No completed run is available to publish.", "warning");
                return;
            }

            publishPostBtn.disabled = true;
            publishPostBtn.textContent = "Publishing...";

            try {
                const response = await fetch(publishUrl, {
                    method: "POST",
                    headers: {
                        "X-CSRFToken": getCookie("csrftoken"),
                        "Content-Type": "application/x-www-form-urlencoded",
                    },
                    body: new URLSearchParams({
                        run_id: currentCompletedRun.run_id,
                    }),
                });

                const data = await response.json();

                if (response.status === 409) {
                    setPublishMessage("This run has already been published.", "warning");
                    localStorage.removeItem("completedQuestRun");
                    publishPostBtn.disabled = true;
                    publishPostBtn.textContent = "Already published";
                    return;
                }

                if (!response.ok) {
                    setPublishMessage(data.error || "Unable to publish this run.", "danger");
                    publishPostBtn.disabled = false;
                    publishPostBtn.textContent = "Publish to Community Feed";
                    return;
                }

                setPublishMessage("Run published successfully. Opening community feed...", "success");
                localStorage.removeItem("completedQuestRun");

                publishPostBtn.disabled = true;
                publishPostBtn.textContent = "Published";

                setTimeout(function () {
                    window.location.href = feedUrl;
                }, 1000);
            } catch (error) {
                setPublishMessage("Unexpected error while publishing to the feed.", "danger");
                publishPostBtn.disabled = false;
                publishPostBtn.textContent = "Publish to Community Feed";
            }
        });
    }
});