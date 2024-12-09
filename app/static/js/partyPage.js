$(document).ready(() => {
  // If we just posted a comment, scroll down to it
  const scrollPosition = localStorage.getItem("scrollPosition")
  if (scrollPosition) {
    $(window).scrollTop(scrollPosition)
    localStorage.removeItem("scrollPosition")
  }

  // Check before deleting a watch party
  $("#delete-form").submit(function(e) {
    e.preventDefault()

    if (confirm("Are you sure you want to delete this watch party?")) {
      e.target.submit()
    }
  })

  // Disable the delete and edit buttons if the watch party has already started
  const startTimeStr = $("#starting-time").text()

  const [datePart, timePart] = startTimeStr.split(" at ")
  const [day, month, year] = datePart.split("/")
  const [hours, minutes] = timePart.split(":")

  const startTime = new Date(year, month - 1, day, hours, minutes)
  const currentTime = new Date()

  if (currentTime > startTime) {
    if ($("#delete-party").length) {
      $("#delete-party").prop("disabled", true)
      $("#delete-container").attr("title", "You cannot delete a watch party that has already started")
    }

    if ($("#edit-party").length) {
      $("#edit-party").prop("disabled", true)
      $("#edit-container").prop("title", "You cannot edit a watch party that has already started")
    }
  }

  // Copy URL to clipboard
  const copyUrlBtn = $("#copy-url-btn")
  const originalHtml = copyUrlBtn.html()
  
  copyUrlBtn.on("click", async function() {
    try {
      await navigator.clipboard.writeText(window.location.href) 
        
      // Change button content to show success
      $(this).html(`
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-check" viewBox="0 0 16 16">
          <path d="M10.97 4.97a.75.75 0 0 1 1.07 1.05l-3.99 4.99a.75.75 0 0 1-1.08.02L4.324 8.384a.75.75 0 1 1 1.06-1.06l2.094 2.093 3.473-4.425a.267.267 0 0 1 .02-.022z"/>
        </svg>
        <span>Copied!</span>
      `)
        
      // Reset button after 2 seconds
      setTimeout(() => {
        $(this).html(originalHtml)
      }, 2000)  
    } catch (err) {
      alert("Failed to copy URL: " + err)
    }
  })
})