// Fade alerts after 5 seconds
function autoFadeAlerts() {
  $(".alert.fade.show").each(function() {
    const $alert = $(this)
    
    const fadeOut = () => {
      $alert.addClass("alert-fade-out")
      setTimeout(() => $alert.remove(), 500)
    }
    
    // Set timeout to fade out after 5 seconds
    const fadeTimeout = setTimeout(fadeOut, 5000)
    $alert.data("fadeTimeout", fadeTimeout)
    
    // Handle manual close
    $alert.find(".btn-close").on("click", function() {
      clearTimeout($alert.data("fadeTimeout"))
      fadeOut()
    })
  })
}

// Initialise when DOM is loaded
$(document).ready(autoFadeAlerts)