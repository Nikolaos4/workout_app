document.getElementById("add-exercise")?.addEventListener("click", function () {
    const total = document.getElementById("id_items-TOTAL_FORMS");
    const max = Number(document.getElementById("id_items-MAX_NUM_FORMS").value);
    const index = Number(total.value);
    if (index >= max) { this.disabled = true; return; }
    const html = document.getElementById("empty-exercise").innerHTML.replaceAll("__prefix__", index);
    document.getElementById("exercise-rows").insertAdjacentHTML("beforeend", html);
    total.value = index + 1;
});
