// Do not allow the user to enter seconds
const timeElement = document.getElementById("due_time")

timeElement.onchange = () => {
  const time = timeElement.value.split(":")

  if (time.length > 2) {
    timeElement.value = time.slice(0, 2).join(":")
  }
}

// Check if date is reasonable
function checkDate(e) {
  const date = new Date()
  const dueDate = new Date(document.getElementById("due_date").value)

  if (timeElement.value) {
    const time = timeElement.value.split(":")
    dueDate.setHours(time[0], time[1], 0, 0)
  }

  // Confirm dates over a year from now
  if (dueDate > date) {
    if (dueDate > date.setFullYear(date.getFullYear() + 1)) {
      if (confirm("Are you sure you want to add an assignment that is due more than a year from now?")) {
        return
      }
      e.preventDefault()
    }
    return
  }

  // Confirm dates in the past
  if (confirm("Are you sure you want to add an assignment that is due in the past?")) {
    return
  }

  e.preventDefault()
}

// Use appropriate form for adding or editing an assessment
let form = document.getElementById("add-assessment")
if (!form) {
  form = document.getElementById("edit-form")
} else {
  // Check if the required fields have been filled and enable the submit button
  const submitBtn = document.getElementById("add-assessment-btn")
  const requiredFields = document.getElementsByClassName("required-field")

  for (let field of requiredFields) {
    field.addEventListener("input", () => {
      const allFilled = Array.from(requiredFields).some(field => field.value.trim() === "")

      submitBtn.disabled = allFilled
      submitBtn.parentElement.title = allFilled ? "Please fill out all required fields" : "Add assessment"
    })
  }
}

// Custom Bootstrap validation form
form.onsubmit = (e) => {
  if (!form.checkValidity()) {
    e.preventDefault()
    e.stopPropagation()
  } else {
    checkDate(e)
  }

  form.classList.add("was-validated")
}

// Show remaining characters
const module = document.getElementById("module")
const title = document.getElementById("title")
const description = document.getElementById("desc")

const moduleCount = document.getElementById("module-count")
const titleCount = document.getElementById("title-count")
const descCount = document.getElementById("desc-count")

module.oninput = () => {
  moduleCount.innerText = `
   ${10 - module.value.length} characters remaining
  `
}

title.oninput = () => {
  titleCount.innerText = `
   ${50 - title.value.length} characters remaining
  `
}

description.oninput = () => {
  descCount.innerText = `
    ${500 - description.value.length} characters remaining
    `
}

// Initial update for editing an assessment
moduleCount.innerText = `
   ${10 - module.value.length} characters remaining
  `
titleCount.innerText = `
  ${50 - title.value.length} characters remaining
 `
descCount.innerText = `
  ${500 - description.value.length} characters remaining
 `
