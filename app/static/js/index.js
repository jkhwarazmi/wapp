// Show the time remaining until the next party starts if there is one
if ($("#next-start").length) {
  function updateTimeRemaining() {
    const startTime = $("#next-start").data("start")
    const now = new Date()
    const target = new Date(startTime)
    
    // Show the start time if it has already passed
    if (now >= target) {
      const formattedTime = target.toLocaleTimeString("en-US", { 
        hour: "2-digit", 
        minute: "2-digit",
        hour12: false 
      })
      $("#next-start").text("Started at " + formattedTime)
      clearInterval(timerInterval)
      return
    }
    
    $("#next-start").text("Starts in " + getTimeRemaining(startTime))
  }

  // Initial update
  updateTimeRemaining()

  // Update every minute
  const timerInterval = setInterval(updateTimeRemaining, 60000)

  function getTimeRemaining(datetime) {
    const now = new Date()
    const target = new Date(datetime)
    const diff = target - now
      
    const minutes = Math.floor(diff / (1000 * 60))
    const hours = Math.floor(diff / (1000 * 60 * 60))
    const days = Math.floor(diff / (1000 * 60 * 60 * 24))
      
    if (hours < 1) {
      return minutes < 2 ? "1 minute" : `${minutes} minutes`
    } else if (days < 1) {
      return hours < 2 ? "1 hour" : `${hours} hours`
    } else {
      return days < 2 ? "1 day" : `${days} days`
    }
  }
}