var allDiv = document.getElementById("all-content");

var saveButton = document.getElementById("saveButtonPopup");
var loadButton = document.getElementById("content-load-button");

function sendTableIDsOnRefresh() {
  var tableIDs = [];

  // Loop through divs with ids "channel"+tableID, up to 15
for (var i = 1; i <= 15; i++) {
  var divId = "channel" + i;
  var divElement = document.getElementById(divId);

  // If divElement is found, collect the tableID and add it to the array
  if (divElement) {
    var tableID = i;
    tableIDs.push(tableID);
  }
}

  console.log("table ids collected:", tableIDs);

  // Perform an AJAX post request to send back the array of tableIDs
  $.ajax({
    type: "POST",
    url: "/table_ids_sync",
    contentType: "application/json",
    data: JSON.stringify({ tableIDs: tableIDs }), 
    success: function (response) {
      console.log("TableIDs sent successfully:", tableIDs);
      // Assuming you want to do something with the response
      console.log("Server response:", response);
    },
    error: function (error) {
      console.error("Error sending TableIDs:", error);
    },
  });

}