// Store whether we want to show upcoming or previous watch parties
let partyview = localStorage.getItem("partyview")

if (!partyview) {
  partyview = "upcoming"
  localStorage.setItem("partyview", partyview)
}

function updatepartyview() {
  if (partyview === "upcoming") {
    $("#party-type").text("Upcoming Watch Parties")
    $("#party-upcoming-btn").addClass("active")
    $("#party-previous-btn").removeClass("active")
    $("#upcoming").addClass("show active")
    $("#previous").removeClass("show active")
  } else {
    $("#party-type").text("Previous Watch Parties")
    $("#party-previous-btn").addClass("active")
    $("#party-upcoming-btn").removeClass("active")
    $("#previous").addClass("show active")
    $("#upcoming").removeClass("show active")
  }
}

// Initial update
updatepartyview()

$("#party-upcoming-btn").on("click", () => {
  partyview = "upcoming"
  localStorage.setItem("partyview", partyview)
  updatepartyview()
})

$("#party-previous-btn").on("click", () => {
  partyview = "previous"
  localStorage.setItem("partyview", partyview)
  updatepartyview()
})