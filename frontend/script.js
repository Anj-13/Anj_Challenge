const API_URL = "http://localhost:8000";

// The latest records from the API, used to fill in the forms
let medicines = [];

// Sends a request and only resolves if the API confirms it worked
async function apiRequest(path, options) {
    let response;
    try {
        response = await fetch(`${API_URL}${path}`, options);
    } catch (error) {
        throw new Error("Could not reach the server. Make sure the backend is running.");
    }

    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
        const requestError = new Error(data.detail || `Request failed with status ${response.status}.`);
        requestError.status = response.status;
        throw requestError;
    }
    return data;
}

function formatPrice(price) {
    return typeof price === "number" ? `$${price.toFixed(2)}` : "Not Available";
}

function medicineLabel(med) {
    return med.name || "Unknown Med";
}

function validatePrice(value) {
    if (value === "" || !Number.isFinite(Number(value))) {
        return "Please enter a valid price";
    }
    if (Number(value) < 0) {
        return "Price cannot be negative";
    }
    return "";
}

function showNotification(message, isError = false) {
    const notification = document.createElement("div");
    notification.className = isError ? "error-message-global" : "success-message";
    notification.textContent = message;

    document.getElementById("notifications").appendChild(notification);
    setTimeout(() => notification.remove(), isError ? 8000 : 4000);
}

function showError(field, message) {
    const errorElement = document.getElementById(`${field}-error`);
    const inputElement = document.getElementById(field);

    if (errorElement && inputElement) {
        errorElement.textContent = message;
        errorElement.classList.add("show");
        inputElement.classList.add("input-error");
    }
}

function clearErrors() {
    // Clear all error messages
    const errorElements = document.querySelectorAll(".error-message");
    errorElements.forEach(element => {
        element.textContent = "";
        element.classList.remove("show");
    });

    // Remove error styling from inputs
    const inputElements = document.querySelectorAll("input, select");
    inputElements.forEach(input => {
        input.classList.remove("input-error");
    });
}

function setBusy(button, isBusy, busyText) {
    if (isBusy) {
        button.dataset.label = button.textContent;
        button.textContent = busyText;
    } else {
        button.textContent = button.dataset.label;
    }
    button.disabled = isBusy;
}

async function loadAveragePrice() {
    const avgElement = document.getElementById("average-price");
    const basisElement = document.getElementById("average-basis");

    try {
        const data = await apiRequest("/average-price");

        if (data.average_price === null) {
            avgElement.textContent = "Not Available";
            basisElement.textContent = data.message;
        } else {
            avgElement.textContent = formatPrice(data.average_price);
            basisElement.textContent = `Based on ${data.medicines_with_valid_prices} of ${data.total_medicines} medicines`;
        }
    } catch (error) {
        console.error("Error loading AVG price:", error);
        avgElement.textContent = "Error loading report";
        basisElement.textContent = "";
    }
}

// Rebuilds a medicine dropdown, keeping the current choice if it still exists
function fillMedicineSelect(selectId) {
    const select = document.getElementById(selectId);
    const selected = select.value;

    select.innerHTML = "";
    select.add(new Option("Select a medicine", ""));
    for (const med of medicines) {
        select.add(new Option(`${medicineLabel(med)} (${formatPrice(med.price)})`, med.id));
    }

    select.value = medicines.some(med => med.id === selected) ? selected : "";
}

function createMedicineItem(med) {
    const medContainer = document.createElement("li");
    medContainer.className = "medicine-item";

    const medDetails = document.createElement("div");

    const medName = document.createElement("h3");
    medName.innerText = medicineLabel(med);
    medName.classList.toggle("missing-value", !med.name);
    medDetails.appendChild(medName);

    const medPrice = document.createElement("p");
    medPrice.innerText = `Price: ${formatPrice(med.price)}`;
    medPrice.classList.toggle("missing-value", typeof med.price !== "number");
    medDetails.appendChild(medPrice);

    medContainer.appendChild(medDetails);

    // Add quick actions
    const quickActions = document.createElement("div");
    quickActions.className = "quick-actions";

    const updateBtn = document.createElement("button");
    updateBtn.type = "button";
    updateBtn.textContent = "Quick Update";
    updateBtn.className = "quick-update-btn";
    updateBtn.setAttribute("aria-label", `Quick update ${medicineLabel(med)}`);
    updateBtn.onclick = () => {
        clearErrors();
        document.getElementById("update-id").value = med.id;
        document.getElementById("update-price").value = med.price ?? "";
        document.getElementById("update-form").scrollIntoView({ behavior: "smooth", block: "center" });
        document.getElementById("update-price").focus({ preventScroll: true });
    };

    const deleteBtn = document.createElement("button");
    deleteBtn.type = "button";
    deleteBtn.textContent = "Quick Delete";
    deleteBtn.className = "quick-delete-btn";
    deleteBtn.setAttribute("aria-label", `Quick delete ${medicineLabel(med)}`);
    deleteBtn.onclick = () => deleteMedicine(med, deleteBtn);

    quickActions.appendChild(updateBtn);
    quickActions.appendChild(deleteBtn);
    medContainer.appendChild(quickActions);

    return medContainer;
}

async function loadMedicines() {
    const medList = document.getElementById("medicine-list");
    const status = document.getElementById("list-status");

    try {
        const data = await apiRequest("/medicines");
        medicines = data.medicines.reverse();

        medList.innerHTML = ""; // clear the list
        status.hidden = medicines.length > 0;
        status.textContent = "No medicines found. Add some medicines to get started.";

        for (const med of medicines) {
            medList.appendChild(createMedicineItem(med));
        }
    } catch (error) {
        console.error("Error loading medicines:", error);
        medicines = [];
        medList.innerHTML = "";
        status.hidden = false;
        status.textContent = error.message;

        const retryBtn = document.createElement("button");
        retryBtn.type = "button";
        retryBtn.className = "secondary-btn";
        retryBtn.textContent = "Try again";
        retryBtn.onclick = refreshData;
        status.appendChild(retryBtn);
    }

    fillMedicineSelect("update-id");
    fillMedicineSelect("delete-id");
}

async function refreshData() {
    await Promise.all([loadMedicines(), loadAveragePrice()]);
}

// Delete medicine function, shared by the delete form and Quick Delete
async function deleteMedicine(med, button) {
    if (!confirm(`Are you sure you want to delete "${medicineLabel(med)}"? This action cannot be undone.`)) {
        return false;
    }

    const formData = new FormData();
    formData.append("id", med.id);

    setBusy(button, true, "Deleting...");
    try {
        const data = await apiRequest("/delete", { method: "DELETE", body: formData });
        showNotification(data.message);
        await refreshData();
        return true;
    } catch (error) {
        console.error("Error:", error);
        showNotification(error.message, true);
        if (error.status === 404) {
            await refreshData();
        }
        return false;
    } finally {
        setBusy(button, false);
    }
}

document.addEventListener("DOMContentLoaded", async () => {
    // Add Medicine Form
    const medForm = document.querySelector("#add-form");
    medForm.addEventListener("submit", async (event) => {
        event.preventDefault();

        const name = event.target.name.value.trim();
        const price = event.target.price.value;

        clearErrors();
        let hasError = false;

        if (name.length < 3) {
            showError("name", "Please enter a medicine name (min 3 characters)");
            hasError = true;
        }
        const priceError = validatePrice(price);
        if (priceError) {
            showError("price", priceError);
            hasError = true;
        }

        if (hasError) return;

        const formData = new FormData();
        formData.append("name", name);
        formData.append("price", price);

        const button = medForm.querySelector("button");
        setBusy(button, true, "Adding...");
        try {
            const data = await apiRequest("/create", { method: "POST", body: formData });
            medForm.reset();
            showNotification(data.message);
            await refreshData();
        } catch (error) {
            console.error("Error:", error);
            showNotification(error.message, true);
            if (error.status === 409) {
                showError("name", error.message);
            }
        } finally {
            setBusy(button, false);
        }
    });

    // Update Medicine Form
    const updateForm = document.querySelector("#update-form");
    const updateSelect = document.getElementById("update-id");
    updateSelect.addEventListener("change", () => {
        const med = medicines.find(item => item.id === updateSelect.value);
        document.getElementById("update-price").value = med?.price ?? "";
    });

    updateForm.addEventListener("submit", async (event) => {
        event.preventDefault();

        const id = updateSelect.value;
        const price = event.target["update-price"].value;

        clearErrors();
        let hasError = false;

        if (!id) {
            showError("update-id", "Please select a medicine");
            hasError = true;
        }
        const priceError = validatePrice(price);
        if (priceError) {
            showError("update-price", priceError);
            hasError = true;
        }

        if (hasError) return;

        const formData = new FormData();
        formData.append("id", id);
        formData.append("price", price);

        const button = updateForm.querySelector("button");
        setBusy(button, true, "Updating...");
        try {
            const data = await apiRequest("/update", { method: "POST", body: formData });
            updateForm.reset();
            showNotification(data.message);
            await refreshData();
        } catch (error) {
            console.error("Error:", error);
            showNotification(error.message, true);
            if (error.status === 404) {
                await refreshData();
            }
        } finally {
            setBusy(button, false);
        }
    });

    // Delete Medicine Form
    const deleteForm = document.querySelector("#delete-form");
    deleteForm.addEventListener("submit", async (event) => {
        event.preventDefault();

        const med = medicines.find(item => item.id === event.target["delete-id"].value);

        clearErrors();
        if (!med) {
            showError("delete-id", "Please select a medicine");
            return;
        }

        const deleted = await deleteMedicine(med, deleteForm.querySelector("button"));
        if (deleted) {
            deleteForm.reset();
        }
    });

    const refreshBtn = document.getElementById("refresh-report");
    refreshBtn.addEventListener("click", async () => {
        setBusy(refreshBtn, true, "Refreshing...");
        await loadAveragePrice();
        setBusy(refreshBtn, false);
    });

    // Initial load
    await refreshData();
});
