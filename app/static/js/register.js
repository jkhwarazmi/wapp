const usernameRegex = /^[a-zA-Z][a-zA-Z0-9._-]{0,29}$/
const emailRegex = /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*\.[a-zA-Z]{2,}$/
const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^a-zA-Z\d\s])[A-Za-z\d\W_]{8,24}$/

let validUsername = $("#enter-username").val().length > 0
let validEmail = $("#enter-email").val().length > 5
let validPassword = false
let validConfirm = false

$("#enter-username").on("input", function () {
  const username = $(this).val()
  
  if (username.length == 0) {
    $("#username-warning").css("visibility", "hidden")
    validUsername = false
    return checkValidity()
  }

  if (usernameRegex.test(username)) {
    $("#username-warning").css("visibility", "hidden")
    validUsername = true
  } else {
    $("#username-warning").css("visibility", "visible")
    validUsername = false
  }
  checkValidity()
})

$("#enter-email").on("input", function () {
  const email = $(this).val()
  
  if (email.length == 0) {
    $("#email-warning").css("visibility", "hidden")
    validEmail = false
    return checkValidity()
  }

  if (emailRegex.test(email) && email.length >= 5 && email.length <= 256) {
    $("#email-warning").css("visibility", "hidden")
    validEmail = true
  } else {
    $("#email-warning").css("visibility", "visible")
    validEmail = false
  }
  checkValidity()
})

$("#enter-password").on("input", function () {
  const password = $(this).val()
  const confirm = $("#enter-confirm").val()
  
  if (password.length == 0) {
    $("#password-warning").css("visibility", "hidden")
    validPassword = false
    return checkValidity()
  }

  if (confirm.length > 0) {
    if (password === confirm) {
      $("#confirm-warning").css("visibility", "hidden")
      validConfirm = true
    } else {
      $("#confirm-warning").css("visibility", "visible")
      validConfirm = false
    }
    return checkValidity()
  }

  if (passwordRegex.test(password)) {
    $("#password-warning").css("visibility", "hidden")
    validPassword = true
  } else {
    $("#password-warning").css("visibility", "visible")
    validPassword = false
  }
  checkValidity()
})

$("#enter-confirm").on("input", function () {
  const password = $("#enter-password").val()
  const confirm = $(this).val()
  
  if (confirm.length == 0) {
    $("#confirm-warning").css("visibility", "hidden")
    validConfirm = false
    return checkValidity()
  }

  if (password === confirm) {
    $("#confirm-warning").css("visibility", "hidden")
    validConfirm = true
  } else {
    $("#confirm-warning").css("visibility", "visible")
    validConfirm = false
  }
  checkValidity()
})

function checkValidity() {
  if (validUsername && validEmail && validPassword && validConfirm) {
    console.log("Valid")
    $("#register-btn").prop("disabled", false)
    $("#register-btn").parent().attr("title", "Register")
  } else {
    console.log("Invalid")
    $("#register-btn").prop("disabled", true)
    $("#register-btn").parent().attr("title", "Please fill out all fields correctly")
  }
}