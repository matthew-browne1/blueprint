$(document).ready(function () {
  $("#save-list").click(function () {

    $.ajax({
      url: "/get_saves",
      type: "GET",
      contentType: "application/json",
      success: function (response) {
        if (response && response.saves) {
          displaySaves(response.saves);
          openPopup();
        } else {
            console.error("Invalid response from server");
        }
      },
      error: function (error) {
        console.error("Error fetching saves:", error);
      },
    });
  });
});

function openPopup() {
  $("#savePopup").show();
}

function closePopup() {
  $("#savePopup").hide();
}

function displaySaves(saves) {
  var saveList = $("#saveList");
  saveList.empty();

  saves.forEach(function (save) {
    var listItem = $("<li>");
    listItem.text(`Name: ${save.name}, Table IDs: ${save.table_ids}`);
    saveList.append(listItem);
  });
}
