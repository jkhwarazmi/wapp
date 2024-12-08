$(document).ready(() => {
  const scrollPosition = localStorage.getItem("scrollPosition")
  if (scrollPosition) {
    $(window).scrollTop(scrollPosition)
    localStorage.removeItem("scrollPosition")
  }

  const startDate = "{{ wp.start_time }}".split(" ")
  $("#start-date").val(startDate[0])

  $("#delete-form").submit(function(e) {
    e.preventDefault()

    if (confirm("Are you sure you want to delete this watch party?")) {
      e.target.submit()
    }
  })
})

