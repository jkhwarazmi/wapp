const csrf = $("meta[name='csrf-token']").attr("content")

$.ajaxSetup({
  beforeSend: (xhr, settings) => {
    if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !settings.crossDomain) {
      xhr.setRequestHeader("X-CSRFToken", csrf)
    }
  }
})