const selectAll = document.getElementById("select-all")
const deleteBtn = document.getElementById("delete-btn")
const restoreBtn = document.getElementById("restore-btn")
const checkboxes = Array.from(document.getElementsByName("remove-item"))
const noSelected = document.getElementById("assessments-selected")

// Change form destination based on button clicked
deleteBtn.onclick = () => {
  document.getElementsByName("remove-assessment")[0].action = ""
}
restoreBtn.onclick = () => {
  document.getElementsByName("remove-assessment")[0].action = "/restore"
}

// Enable and disable submission buttons if checkboxes are checked
for (let checkbox of checkboxes) {
  checkbox.addEventListener("change", () => {
    if (checkboxes.some(checkbox => checkbox.checked)) {
      deleteBtn.disabled = false
      deleteBtn.parentElement.title = "Delete selected assessments"

      restoreBtn.disabled = false
      restoreBtn.parentElement.title = "Restore selected assessments"
    } else {
      deleteBtn.disabled = true
      deleteBtn.parentElement.title = "No assessments to delete"

      restoreBtn.disabled = true
      restoreBtn.parentElement.title = "No assessments to restore"
    }

    if (!checkbox.checked && selectAll.checked) {
      selectAll.checked = false
    }

    if (checkboxes.every(checkbox => checkbox.checked)) {
      selectAll.checked = true
    } 
  })
}

// Select all checkboxes
selectAll.onclick = function() {
  for (let checkbox of checkboxes) {
    if (this.checked && !checkbox.checked) {
      checkbox.closest(".card").dispatchEvent(new Event("click"))
    } else if (!this.checked && checkbox.checked) {
      checkbox.closest(".card").dispatchEvent(new Event("click"))
    }
  }
}

// Selecting individual checkboxes and updating the count
function selectAssessment(event) {
  event.currentTarget.classList.toggle("bg-secondary-subtle")
  const checkbox = event.currentTarget.querySelector(".form-check-input")
  event.currentTarget.querySelector(".form-check-label").innerText = checkbox.checked ? "Select" : "Selected"
  
  checkbox.checked = !checkbox.checked
  if (checkbox.checked) {
    noSelected.innerText = parseInt(noSelected.innerText) + 1
  } else {
    noSelected.innerText = parseInt(noSelected.innerText) - 1
  }

  if (noSelected.innerText === "1") {
    document.getElementById("word").innerText = "Assessment"
  } else {
    document.getElementById("word").innerText = "Assessments"
  }

  checkbox.dispatchEvent(new Event("change"))
}
