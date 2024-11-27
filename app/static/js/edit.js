const submitBtn = document.getElementById("submit-btn")

const originalValues = {
  module: form.getAttribute("data-original-module"),
  title: form.getAttribute("data-original-title"),
  dueDate: form.getAttribute("data-original-due-date"),
  dueTime: form.getAttribute("data-original-due-time"),
  desc: form.getAttribute("data-original-desc")
}

const formInputs = {
  module: document.getElementById("module"),
  title: document.getElementById("title"),
  dueDate: document.getElementById("due_date"),
  dueTime: document.getElementById("due_time"),
  desc: document.getElementById("desc")
}

// Only enable the submit button if values have changed and required fields are filled
function checkForChanges() {
  const hasChanged = 
    (formInputs.module.value !== originalValues.module ||
    formInputs.title.value !== originalValues.title ||
    formInputs.dueDate.value !== originalValues.dueDate ||
    formInputs.dueTime.value !== originalValues.dueTime ||
    formInputs.desc.value !== originalValues.desc) &&
    (formInputs.module.value.trim() !== "" && 
    formInputs.title.value.trim() !== "" &&
    formInputs.dueDate.value.trim() !== "")
  
  submitBtn.disabled = !hasChanged
  submitBtn.parentElement.title = hasChanged ? "Save changes" : "No changes to save"
}

for (let input in formInputs) {
  formInputs[input].addEventListener("input", checkForChanges)
}