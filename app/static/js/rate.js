// Initialise display-only ratings
$(".rating-display").rating({
  displayOnly: true,
  showCaption: false,
  showClear: false,
  size: "sm",
  theme: "krajee-svg"
})

// Initialise interactive rating
$(".rating-input").rating({
  theme: "krajee-svg",
  showCaption: false,
  showClear: false,
  size: "md"
})

$("#rating-form").submit(function(e) {
  e.preventDefault()
  
  $.ajax({
    url: e.target.action,
    type: "POST",
    data: $(this).serialize(),
    success: (data) => {
      // Update or show the user's rating section
      if ($("#no-rating").length) {
        const ratingHtml = `
          <input type="text" class="kv-fa rating-display" 
            value="${data.rating}" 
            data-size="sm" 
            readonly 
            id="rating-current"
          >`
        $("#no-rating").replaceWith(ratingHtml)
        // Initialise the new rating display
        $("#rating-current").rating({
          displayOnly: true,
          showCaption: false,
          showClear: false,
          size: "sm",
          theme: "krajee-svg"
        })
      } else {
        // Update existing rating display
        $("#rating-current").rating("update", data.rating)
      }

      // Update average rating
      if ($("#no-avg").length) {
        const avgHtml = `
          <div class="d-flex flex-column align-items-center gap-3">
            <input type="text" class="kv-fa rating-display" 
              value="${data.avgRating}" 
              data-size="sm" 
              title="Average rating: ${data.avgRating}" 
              readonly>
            <span class="text-muted fs-5">(${Math.round(parseFloat(data.avgRating) * 10) / 10})</span>
          </div>`
        $("#no-avg").replaceWith(avgHtml)
        // Initialise the new rating display
        $(".rating-display").first().rating({
          displayOnly: true,
          showCaption: false,
          showClear: false,
          size: "sm",
          theme: "krajee-svg"
        })
      } else {
        // Update existing average rating
        $(".rating-display").first().rating("update", data.avgRating)
        $(".text-muted.fs-5").text(`(${Math.round(parseFloat(data.avgRating) * 10) / 10})`)
      }

      // Update button text
      $("#rating-form button").text("Change Rating")
    },
    error: (err) => alert("Error updating rating: " + err.responseText)
  })
})