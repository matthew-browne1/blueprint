var allDiv = document.getElementById("all-content");

window.addEventListener("beforeunload", function () {
  // Make an Ajax request to fetch the user ID
  getUserId(function (userId) {
    // Get the content of the div
    var contentToSave = document.getElementById("all-content").innerHTML;

    // Save the content to localStorage with a user-specific key
    localStorage.setItem("savedContent_" + userId, contentToSave);
  });
});

// Retrieve user-specific saved content from localStorage
getUserId(function (userId) {
  var savedContent = localStorage.getItem("savedContent_" + userId);

  // Set the content of the div
  $("#all-content").html(savedContent || "");
});

function getUserId(callback) {
  // Make an Ajax request to fetch the user ID
  $.ajax({
    url: "/get_user_id",
    method: "GET",
    dataType: "json",
    success: function (response) {
      // Call the callback function with the user ID
      callback(response.user_id);
    },
    error: function (error) {
      console.error("Error fetching user ID:", error);
    },
  });
}
