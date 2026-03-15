document.addEventListener("DOMContentLoaded", function () {
    const cards = document.querySelectorAll(".city-card");
    const cityForm = document.getElementById("city-form");
    const selectedCityInput = document.getElementById("selected-city-id");
    const searchInput = document.getElementById("city-search");

    const minusBtn = document.getElementById("group-minus");
    const plusBtn = document.getElementById("group-plus");
    const groupValue = document.getElementById("group-size-value");
    const groupInput = document.getElementById("group-size-input");

    if (!selectedCityInput || !groupInput || !groupValue) {
        return;
    }

    let groupSize = parseInt(groupInput.value || "1", 10);
    if (isNaN(groupSize) || groupSize < 1) {
        groupSize = 1;
    }
    if (groupSize > 10) {
        groupSize = 10;
    }

    function updateGroupDisplay() {
        groupValue.textContent = groupSize === 1 ? "1 person" : `${groupSize} people`;
        groupInput.value = groupSize;
    }

    if (minusBtn) {
        minusBtn.addEventListener("click", function () {
            if (groupSize > 1) {
                groupSize -= 1;
                updateGroupDisplay();
            }
        });
    }

    if (plusBtn) {
        plusBtn.addEventListener("click", function () {
            if (groupSize < 10) {
                groupSize += 1;
                updateGroupDisplay();
            }
        });
    }

    cards.forEach(function (card) {
        card.addEventListener("click", function () {
            cards.forEach(function (c) {
                c.classList.remove("selected");
            });

            card.classList.add("selected");
            selectedCityInput.value = card.dataset.cityId || "";
        });
    });

    if (searchInput) {
        searchInput.addEventListener("input", function () {
            const keyword = searchInput.value.trim().toLowerCase();

            cards.forEach(function (card) {
                const cityName = (card.dataset.cityName || "").toLowerCase();
                card.style.display = cityName.includes(keyword) ? "" : "none";
            });
        });
    }

    if (cityForm) {
        cityForm.addEventListener("submit", function (event) {
            if (!selectedCityInput.value) {
                event.preventDefault();
                alert("Please select a city before continuing.");
            }
        });
    }

    updateGroupDisplay();
});