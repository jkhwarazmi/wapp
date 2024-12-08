$("#login-button").prop("disabled", $("#enter-username").val().length == 0 || $("#enter-password").val().length < 8)

if ($("#login-btn").attr("disabled")) {
  $("#login-btn").parent().attr("title", "Fill out all fields")
} else {
  $("#login-btn").parent().attr("title", "Login")
}

$("#enter-username").on("input", function () {
  const username = $(this).val()

  if (username.length == 0) {
    $("#login-btn").prop("disabled", true)
  } else {
    $("#login-btn").prop("disabled", $("#enter-password").val().length < 8)
  }

  if ($("#login-btn").attr("disabled")) {
    $("#login-btn").parent().attr("title", "Fill out all fields")
  } else {
    $("#login-btn").parent().attr("title", "Login")
  }
})

$("#enter-password").on("input", function () {
  const password = $(this).val()

  if (password.length < 8) {
    $("#login-btn").prop("disabled", true)
  } else {
    $("#login-btn").prop("disabled", $("#enter-username").val().length == 0)
  }

  if ($("#login-btn").attr("disabled")) {
    $("#login-btn").parent().attr("title", "Fill out all fields")
  } else {
    $("#login-btn").parent().attr("title", "Login")
  }
})