// Assessment view logic

let assessmentView = localStorage.getItem("assessmentView");

if (!assessmentView) {
  assessmentView = "incomplete"
  localStorage.setItem("assessmentView", assessmentView)
}

function updateAssessmentView() {
  if (assessmentView === "incomplete") {
    document.getElementById("assessment-type").innerText = "Incomplete Assessments"
    document.getElementById("assessment-incomplete-btn").classList.add("active")
    document.getElementById("assessment-complete-btn").classList.remove("active")
    document.getElementById("incomplete").classList.add("show", "active")
    document.getElementById("complete").classList.remove("show", "active")
  } else {
    document.getElementById("assessment-type").innerText = "Complete Assessments"
    document.getElementById("assessment-complete-btn").classList.add("active")
    document.getElementById("assessment-incomplete-btn").classList.remove("active")
    document.getElementById("complete").classList.add("show", "active")
    document.getElementById("incomplete").classList.remove("show", "active")
  }
}

// Initial update
updateAssessmentView();

document.getElementById("assessment-incomplete-btn").onclick = () => {
  assessmentView = "incomplete"
  localStorage.setItem("assessmentView", assessmentView)
  updateAssessmentView()
}

document.getElementById("assessment-complete-btn").onclick = () => {
  assessmentView = "complete"
  localStorage.setItem("assessmentView", assessmentView)
  updateAssessmentView()
}

// Card popup logic

// Format the date string to be more readable
function formatDate(dateString) {
  const datePart = dateString.split(" ")[0];
  const [year, month, day] = datePart.split("-");

  // Format as "dd/mm/yy"
  return `${day}/${month}/${year.slice(2)}`;
}

// Close the card when clicking outside of it
window.addEventListener("click", (e) => {
  const popup = document.getElementById("popup")
  if (popup && !popup.contains(e.target) && !e.target.closest(".card")) {
    closeCard();
  }
})

function expandCard(event, index) {
  // Only expand if we didn't click on a button
  if (event.target.closest(".btn")) {
    return
  }

  // Modify created at and modified at to be more readable
  const assessmentInfo = {
    module: document.getElementById(`assessment-module-${index}`).innerText,
    title: document.getElementById(`assessment-title-${index}`).innerText,
    desc: document.getElementById(`hidden-data-${index}`).getAttribute("data-desc"),
    createdAt: document.getElementById(`hidden-data-${index}`).getAttribute("data-created_at"),
    modifiedAt: document.getElementById(`hidden-data-${index}`).getAttribute("data-modified_at"),
    dueAt: document.getElementById(`assessment-due_at-${index}`).innerText,
    completedAt: null
  }

  // Only get completedAt if the assessment is complete
  const completed = document.getElementById(`assessment-completed_at-${index}`)
  if (completed) {
    assessmentInfo.completedAt = completed.innerText
  }

  // Format the dates
  assessmentInfo.createdAt = "Creation Date: " + formatDate(assessmentInfo.createdAt)
  assessmentInfo.modifiedAt = "Last Modified: " + formatDate(assessmentInfo.modifiedAt)

  // Set the data in the popup
  document.getElementById("popup-module").innerText = assessmentInfo.module
  document.getElementById("popup-title").innerText = assessmentInfo.title
  document.getElementById("popup-created").innerText = assessmentInfo.createdAt
  document.getElementById("popup-modified").innerText = assessmentInfo.modifiedAt
  document.getElementById("popup-desc").innerText = assessmentInfo.desc ? assessmentInfo.desc : "No description provided"
  document.getElementById("popup-form-1").action = `/edit/${index}`
  document.getElementById("popup-input-3").value = index

  if (completed) {
    document.getElementById("popup-due-parent").style.display = "block"
    document.getElementById("popup-due").innerText = assessmentInfo.dueAt

    const status = document.getElementById("popup-status")
    status.innerText = assessmentInfo.completedAt
    status.className = "badge rounded-pill text-bg-success mt-3"

    const form = document.getElementById("popup-form-2")
    form.action = "/restore"
    form.innerHTML = `
      <input type="hidden" name="id" value="${index}">
      <button type="submit" name="restore" class="btn btn-outline-secondary btn-lg d-flex align-items-center gap-2" title="Set this assessment as incomplete">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-arrow-counterclockwise" viewBox="0 0 16 16">
          <path fill-rule="evenodd" d="M8 3a5 5 0 1 0 4.546 2.914.5.5 0 1 1 .908-.418A6 6 0 1 1 8 2v1z"/>
          <path d="M8 1a.5.5 0 0 1 .5.5v3a.5.5 0 0 1-1 0v-3A.5.5 0 0 1 8 1z"/>
          <path d="M5.354 1.646a.5.5 0 0 1 .708 0l2 2a.5.5 0 1 1-.708.708L5.354 2.354a.5.5 0 0 1 0-.708z"/>
        </svg>
        Restore
      </button>
    `
  } else {
    document.getElementById("popup-due-parent").style.display = "none"

    const status = document.getElementById("popup-status")
    status.innerText = assessmentInfo.dueAt
    if (status.innerText.includes("Overdue")) {
      status.className = "badge rounded-pill text-bg-danger mt-3"
    } else {
      status.className = "badge rounded-pill text-bg-warning mt-3"
    }

    const form = document.getElementById("popup-form-2")
    form.action = "/complete"
    form.innerHTML = `
      <input type="hidden" name="id" value="${index}">
      <button type="submit" name="complete" class="btn btn-outline-success btn-lg d-flex align-items-center gap-2" title="Mark this assessment as complete">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-check" viewBox="0 0 16 16">
          <path d="M13.854 3.146a.5.5 0 0 1 0 .708L6.207 11.5 4.854 10.146a.5.5 0 1 1 .708-.708l1.5 1.5a.5.5 0 0 1 .708 0l7.5-7.5a.5.5 0 0 1 .708 0z"/>
        </svg>
        Complete
      </button>
    `
  }

  document.getElementsByClassName("content-wrapper")[0].classList.add('blurred')
  document.getElementById("expanded-view").style.display = "block"
}

function closeCard() {
  document.getElementsByClassName("content-wrapper")[0].classList.remove("blurred")
  document.getElementById("expanded-view").style.display = "none"
}

// Display overdue status
const dueItems = document.getElementsByClassName("incomplete-data")
for (let item of dueItems) {
  const dueDate = item.getAttribute("data-due_date")
  let dueTime = item.getAttribute("data-due_time")

  if (dueTime === "None") {
    dueTime = "00:00:00"
  }

  const date = new Date(dueDate + "T" + dueTime)
  const currentDate = new Date()

  if (date < currentDate) {
    const id = item.getAttribute("data-id")
    const pill = document.getElementById(`pill-${id}`)
    pill.className = "badge rounded-pill text-bg-danger"
    pill.innerText += " (Overdue)"
  }
}
