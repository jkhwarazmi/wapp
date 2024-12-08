// Fade alerts after 5 seconds
function autoFadeAlerts() {
  const alerts = document.querySelectorAll(".alert.fade.show")
  
  alerts.forEach(alert => {
    const fadeOut = () => {
      alert.classList.add("alert-fade-out")
      setTimeout(() => alert.remove(), 500)
    }
  
    // Set timeout to fade out after 5 seconds
    const fadeTimeout = setTimeout(fadeOut, 5000)
    alert.dataset.fadeTimeout = fadeTimeout
  
    // Handle manual close
    const closeButton = alert.querySelector(".btn-close")
    closeButton.addEventListener("click", () => {
      clearTimeout(fadeTimeout)
      fadeOut()
    })
  })
}
  
// Initialise when DOM is loaded
document.addEventListener("DOMContentLoaded", autoFadeAlerts)
  