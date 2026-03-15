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
    const questBoard = document.getElementById("quest-board");
    if (!questBoard) {
        return;
    }

    const recommendBtn = document.getElementById("recommend-btn");
    const shuffleBtn = document.getElementById("shuffle-btn");
    const startBtn = document.getElementById("start-btn");

    const statusMessage = document.getElementById("status-message");
    const titleEl = document.getElementById("quest-title");
    const descEl = document.getElementById("quest-description");
    const typeEl = document.getElementById("quest-type");
    const cityEl = document.getElementById("quest-city");
    const groupLimitsEl = document.getElementById("quest-group-limits");
    const durationEl = document.getElementById("quest-duration");
    const currentGroupSizeEl = document.getElementById("current-group-size");

    const recommendUrl = questBoard.dataset.recommendUrl;
    const shuffleUrl = questBoard.dataset.shuffleUrl;
    const startUrl = questBoard.dataset.startUrl;
    const progressUrl = questBoard.dataset.progressUrl;

    let currentQuest = null;
    let currentGroupSize = parseInt(questBoard.dataset.selectedGroupSize || "1", 10);

    if (isNaN(currentGroupSize) || currentGroupSize < 1) {
        currentGroupSize = 1;
    }

    function setStatus(message, type) {
        statusMessage.className = `alert alert-${type} border mb-4`;
        statusMessage.textContent = message;
    }

    function updateGroupSizeLabel() {
        if (currentGroupSizeEl) {
            currentGroupSizeEl.textContent = currentGroupSize;
        }
    }

    function renderQuest(quest) {
        currentQuest = quest;

        titleEl.textContent = quest.name || "Unnamed quest";
        descEl.textContent = quest.description || "No description available.";
        typeEl.textContent = quest.type || "N/A";
        cityEl.textContent = quest.selected_city || "—";
        groupLimitsEl.textContent = quest.group_limits || "—";
        durationEl.textContent = quest.duration ? `${quest.duration} minutes` : "—";
    }

    async function loadQuest(url, successMessage) {
        try {
            const response = await fetch(url);
            const data = await response.json();

            if (!response.ok) {
                setStatus(data.error || "Unable to load quest.", "danger");
                return;
            }

            renderQuest(data);
            setStatus(successMessage, "success");
        } catch (error) {
            setStatus("Unexpected error while loading quest.", "danger");
        }
    }

    if (recommendBtn) {
        recommendBtn.addEventListener("click", function () {
            loadQuest(`${recommendUrl}?group_size=${currentGroupSize}`, "Quest recommended successfully.");
        });
    }

    if (shuffleBtn) {
        shuffleBtn.addEventListener("click", function () {
            loadQuest(`${shuffleUrl}?group_size=${currentGroupSize}`, "Quest shuffled successfully.");
        });
    }

    if (startBtn) {
        startBtn.addEventListener("click", async function () {
            if (!currentQuest || !currentQuest.id) {
                setStatus("Please load a quest first before starting.", "warning");
                return;
            }

            try {
                const response = await fetch(startUrl, {
                    method: "POST",
                    headers: {
                        "X-CSRFToken": getCookie("csrftoken"),
                        "Content-Type": "application/x-www-form-urlencoded",
                    },
                    body: new URLSearchParams({
                        quest_id: currentQuest.id,
                        group_size: currentGroupSize,
                    }),
                });

                const data = await response.json();

                if (!response.ok) {
                    setStatus(data.error || "Unable to start quest.", "danger");
                    return;
                }

                const activeQuest = {
                    run_id: data.run_id,
                    id: data.quest.id,
                    name: data.quest.name,
                    type: data.quest.type,
                    duration: data.quest.duration,
                    selected_city: data.city.name,
                    group_limits: currentQuest.group_limits,
                    description: currentQuest.description,
                    started_at: data.started_at,
                    status: data.status,
                    group_size: currentGroupSize,
                };

                localStorage.removeItem("questProgress");
                localStorage.setItem("activeQuest", JSON.stringify(activeQuest));

                setStatus(`Quest started successfully. Run ID: ${data.run_id}`, "success");
                window.location.href = progressUrl;
            } catch (error) {
                setStatus("Unexpected error while starting quest.", "danger");
            }
        });
    }

    updateGroupSizeLabel();
});