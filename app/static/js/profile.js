const usernameRegex = /^[a-zA-Z][a-zA-Z0-9._-]{0,29}$/
const emailRegex = /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*\.[a-zA-Z]{2,}$/
const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^a-zA-Z\d\s])[A-Za-z\d\W_]{8,24}$/
const colours = ["#3375cb", "#51b1df", "#59c3ad", "#5fcf80", "#7a5ddf", "#959595", "#c67b2b", "#c89332", "#c22946", "#d7348a"]

$("form input").on("input", function() {
  const form = $(this).closest("form")
  const originalValue = form.data("original")
  const newValue = $(this).val().trim()
  const button = form.find("button")
  const inputId = $(this).attr("id")
  
  // Default disabled state if empty or unchanged
  let isValid = newValue !== "" && newValue !== originalValue
  
  // Specific validation based on input type
  switch(inputId) {
    case "username":
      isValid = isValid && usernameRegex.test(newValue)
      break
      
    case "email":
      isValid = isValid && 
                emailRegex.test(newValue) && 
                newValue.length >= 5 && 
                newValue.length <= 256
      break
      
    case "password":
      const confirmPassword = $("#confirm-password").val()
      isValid = isValid && 
                passwordRegex.test(newValue) && 
                (confirmPassword === "" || newValue === confirmPassword)
      // Update confirm password button state
      if (confirmPassword) {
        $("#confirm-password").trigger("input")
      }
      break
      
    case "confirm-password":
      const password = $("#password").val()
      isValid = isValid && 
                password === newValue && 
                passwordRegex.test(password)
      break
  }
  
  button.prop("disabled", !isValid)
})

$("form select").on("change", function() {
  const form = $(this).closest("form")
  const originalValue = form.data("original")
  const newValue = $(this).val()
  const button = form.find("button")
  
  button.prop("disabled", newValue === originalValue)
})

$("form").on("submit", function(e) {
  e.preventDefault()
  let data = {}

  if ($(this).attr("id") === "delete-profile") {
    if (confirm("Are you sure you want to delete your profile?")) {
      data = { "delete-profile": true }
    } else {
      return
    }
  }

  if ($(this).attr("id") === "edit-password") {
    const password = $(this).find("#password").val()
    const confirmPassword = $(this).find("#confirm-password").val()
    
    if (password !== confirmPassword) {
      return alert("Passwords do not match")
    } else if (password.length < 8 || password.length > 24) {
      return alert("Password must be between 8 and 24 characters")
    } else if (!passwordRegex.test(password)) {
      return alert("Password must contain at least one uppercase letter, one lowercase letter, one number, and one special character")
    }

    data = { "edit-password": password, "edit-password-confirm": confirmPassword }
  } else if ($(this).attr("id") === "edit-colour") {

    if (!colours.includes($("input[name='profile_colour']:checked").val())) {
      return alert("Invalid colour")
    }

    data = { "edit-colour": $("input[name='profile_colour']:checked").val() }
  } else if ($(this).attr("id") !== "delete-profile") {
    const key = $(this).attr("id")
    const value = $(this).find("input").val().trim()
    data[key] = value
  } else if ($(this).attr("id") == "edit-username") {
    const username = $(this).find("input").val().trim()

    if (username.length < 8 || username.length > 30) {
      return alert("Username must be between 8 and 30 characters")
    }

    if (!usernameRegex.test(username)) {
      return alert("Invalid username")
    }

    data = { "edit-username": username }
  } else if ($(this).attr("id") == "edit-email") {
    const email = $(this).find("input").val().trim()

    if (!emailRegex.test(email) || email.length < 5 || email.length > 256) {
      return alert("Invalid email")
    }

    data = { "edit-email": email }
  }

  $.ajax({
    url: e.target.action,
    type: "POST",
    data: JSON.stringify(data),
    contentType: "application/json",
    dataType: "json",
    success: (res) => {
      if ($(this).attr("id") === "delete-profile") {
        window.location.href = "/logout"
      } else {
        alert("Changes saved")
        $(this).attr("data-original", res.value)
        if ($(this).attr("id") === "edit-username" || $(this).attr("id") === "edit-email") {
          $(this).find("input").val(res.value)
          if ($(this).attr("id") === "edit-username") {
            $("#profile-initial").text(res.value[0])
          }
        } else if ($(this).attr("id") === "edit-colour") {
          $(`input[name="profile_colour"][value="${res.value}"]`).prop('checked', true)
          $("#profile-circle").css("background-color", res.value)
        } else if ($(this).attr("id") === "edit-password") {
          $(this).find("input").val("")
        }
        $(this).find("button").prop("disabled", true)
      }
    },
    error: (err) => alert("Error: " + err.responseText)      
  }) 
})