$(document).ready(function () {
    // Use jQuery to select elements and bind event listeners
    $("#continue-btn").on("click", function () {
      redirectToBp();
    });
    $("#login-btn").on("click", function () {
      openLoginForm();
    });
    $("#close-login").on("click", function () {
      closeLoginForm();
    });
  
  });
  
  // modal login
  function openLoginForm() {
    document.body.classList.add("showLoginForm");
  }
  function closeLoginForm() {
    document.body.classList.remove("showLoginForm");
  }
  
  // Drop down menu
  window.onclick = function (event) {
    if (!event.target.matches(".dropbtn")) {
      var dropdowns = document.getElementsByClassName("dropdown-content");
      var i;
      for (i = 0; i < dropdowns.length; i++) {
        var openDropdown = dropdowns[i];
        if (openDropdown.style.display === "block") {
          openDropdown.style.display = "none";
        }
      }
    }
  };
  
  function redirectToBp() {
    window.location.href = "blueprint";
  }
  
  