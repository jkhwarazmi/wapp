// Track form state
let formMode = "create"
let validTitle = false
let validStart = false

$(document).ready(function() {
  $("#create").on("click", function() {
    formMode = "create"
    $("#party-form").removeClass("form-mode-edit").addClass("form-mode-create")
    resetForm()
    openPopup()
    showSearch()
  })

  $("#edit-party").on("click", function() {
    formMode = "edit"
    $("#party-form").removeClass("form-mode-create").addClass("form-mode-edit")
    populateEditForm()
    openPopup()
    showForm() 
  })

  $(window).on("click", function(e) {
    if (!$(e.target).closest("#popup").length && 
        !$(e.target).closest("#create").length && 
        !$(e.target).closest("#edit-party").length && 
        $("#expanded-view").is(":visible")) {
      closePopup()
    }
  })

  // Form submission handling
  $("#party-form").on("submit", function(e) {
    e.preventDefault()
    
    const url = formMode === "create" ? "/create" : `/party/edit/${$("#wp-url").val()}`
    
    $(this).attr("action", url)
    this.submit()
  })
})

function openPopup() {
  $(".content-wrapper").addClass("blurred")
  $("#expanded-view").show()
  $("#create-form").hide()
}

function closePopup() {
  $(".content-wrapper").removeClass("blurred")
  $("#expanded-view").hide()
}

function resetForm() {
  $("#search-bar").val("")
  $("#movie-results").empty()
  $("#title-input, #location-input, #date-input, #time-input, #description-input").val("")
  $("#private-input").prop("checked", false)
  $("#movie-input").val("")
  
  // Reset character counters
  $("#title-count").text("100 characters remaining")
  $("#location-count").text("100 characters remaining")
  $("#description-count").text("500 characters remaining")
  
  // Reset validation
  validTitle = false
  validStart = false
  checkValid()
}

function populateEditForm() {
  // Get current values from the page or data attributes
  const title = $("#current-title").text()
  const movieId = $("#current-movie-id").val()
  const location = $("#current-location").text()
  const description = $("#current-description").text()
  const isPrivate = $("#current-is-private").val()
  const startDate = $("#current-start-date").val()
  const startTime = $("#current-start-time").val()

  // Populate the form
  $("#title-input").val(title)
  $("#movie-input").val(movieId)
  $("#location-input").val(location)
  $("#description-input").val(description)
  $("#private-input").prop("checked", isPrivate)
  $("#date-input").val(startDate)
  $("#time-input").val(startTime)

  // Update character counters
  updateCharacterCount("#title-input", "#title-count", 100)
  updateCharacterCount("#location-input", "#location-count", 100)
  updateCharacterCount("#description-input", "#description-count", 500)

  // Validate form
  validTitle = title.length > 0 && title.length <= 100
  checkValid()
}

function updateCharacterCount(inputId, counterId, maxLength) {
  const remaining = maxLength - $(inputId).val().length
  $(counterId).text(`${remaining} characters remaining`)
}

$("#search-form").on("submit", function(e) {
  e.preventDefault()

  const inputValue = $("#search-bar").val().trim()
  if (inputValue === "") {
    return
  }

  $.ajax({
    url: "/query",
    type: "POST",
    data: JSON.stringify({ search: inputValue }),
    contentType: "application/json",
    dataType: "json",
    success: (data) => {
      $("#movie-results").empty()
      for (let movie of data.results) {
        let movieCard = $(`
          <div class="col m-4" title="Select ${movie.title}">
            <div class="card p-3 shadow-sm content-box" onclick="pickMovie(${movie.id})">
              <div class="row g-0 flex-column flex-md-row">
                <div class="col-md-8 text-center text-md-start">
                  <div class="card-body">
                    <h5 class="card-title">${movie.title}</h5>
                    <h6 class="card-subtitle mb-2 text-muted">${movie.release_date.split("-").reverse().join("/")}</h6>
                    <p class="card-text text-muted movie-description">${movie.overview}</p>
                  </div>
                </div>
                <div class="col-md-4 d-flex justify-content-center justify-content-md-end mt-4">
                  <img src="https://image.tmdb.org/t/p/w500${movie.poster_path}" alt="${movie.title} Poster" class="poster img-fluid create-poster">
                </div>
              </div>
            </div>
          </div>
        `)
        $("#movie-results").append(movieCard)
      }
      if (data.results.length === 0) {
        $("#movie-results").append(`
          <div class="col-12 text-center">
            <p class="text-muted">No movies found</p>
          </div>
        `)
      }
    },
    error: (err) => console.error("Error fetching data:", err)      
  })
})

function pickMovie(id) {
  $("#movie-input").val(id)
  $("#create-form").show()
  showForm()
}

$("#show-search").on("click", function(e) {
  e.preventDefault()
  showSearch()
})

function showSearch() {
  // Hide form elements
  $("#party-form").hide()
  $("#show-search").hide()
  
  // Show search elements
  $("#search-form").show()
  $("#results-heading").show()
  $("#movie-results").show()
  $("#search-bar").focus()
}

function showForm() {
  // Hide search elements
  $("#search-form").hide()
  $("#results-heading").hide()
  $("#movie-results").hide()
  
  // Show form
  $("#party-form").show()
  
  // Show back button
  $("#show-search").show()
  checkValid()
}

// Input validation handlers
$("#title-input").on("input", function() {
  const remaining = 100 - $(this).val().length
  $("#title-count").text(`${remaining} characters remaining`)

  validTitle = remaining >= 0 && remaining < 100
  checkValid()
})

$("#location-input").on("input", function() {
  const remaining = 100 - $(this).val().length
  $("#location-count").text(`${remaining} characters remaining`)
  checkValid()
})

$("#description-input").on("input", function() {
  const remaining = 500 - $(this).val().length
  $("#description-count").text(`${remaining} characters remaining`)
  checkValid()
})

$("#date-input, #time-input").on("input", function() {
  checkValid()
})

$("#private-input").on("change", function() {
  checkValid()
})

function checkValid() {
  if ($("#date-input").val() && $("#time-input").val()) {
    const now = new Date()
    const date = new Date($("#date-input").val())
    const time = $("#time-input").val().split(":")
    date.setHours(time[0])
    date.setMinutes(time[1])

    // Within the next year
    if (date > now && date < new Date(now.getFullYear() + 1, now.getMonth(), now.getDate())) {
      validStart = true
      $("#date-warning").css("visibility", "hidden")
    } else {
      validStart = false
      $("#date-warning").css("visibility", "visible")
    }
  } else {
    validStart = false
    $("#date-warning").css("visibility", "hidden")
  }

  if (validTitle && validStart) {
    $("#create-party").prop("disabled", false)
    $("#create-party").parent().attr("title", formMode === "create" ? "Create a new watch party" : "Save changes")
  } else {
    $("#create-party").prop("disabled", true)
    $("#create-party").parent().attr("title", "Fill out all required fields")
  }

  if (formMode === "edit") {
    if ($("#title-input").val() === $("#current-title").text() && $("#description-input").val() === $("#current-description").text() && $("#location-input").val() === $("#current-location").text() && $("#date-input").val() === $("#current-start-date").val() && $("#time-input").val() === $("#current-start-time").val() && $("#private-input").prop("checked") == Boolean($("#current-is-private").val()) && $("#movie-input").val() === $("#current-movie-id").val()) {
      $("#create-party").prop("disabled", true)
      $("#create-party").parent().attr("title", "No changes to save")
    }
  }
}