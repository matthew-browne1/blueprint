// modal login
function openLoginForm(){
    document.body.classList.add("showLoginForm");
    }
function closeLoginForm(){
    document.body.classList.remove("showLoginForm");
    }

// Base Page - Settings popup and light/dark features
var settingsmenu = document.querySelector(".settings-menu");
var darkBtn = document.getElementById("dark-btn");

function settingsMenuToggle(){
    settingsmenu.classList.toggle("settings-menu-height");
}
 darkBtn.onclick = function(){
    darkBtn.classList.toggle("dark-btn-on");
    document.body.classList.toggle("dark-theme");
    if(localStorage.getItem("theme") == "light"){
        localStorage.setItem("theme", "dark");
    }
    else{
        localStorage.setItem("theme", "light");
    }
}

if(localStorage.getItem("theme") == "light"){
    darkBtn.classList.remove("dark-btn-on");
    document.body.classList.remove("dark-theme");
}
else if(localStorage.getItem("theme") == "dark"){
    darkBtn.classList.add("dark-btn-on");
    document.body.classList.add("dark-theme");
}

else {
    localStorage.setItem("theme", "light");
}

// Drop down menu
window.onclick = function(event) {
  if (!event.target.matches('.dropbtn')) {
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

// Slider
const mySlider = document.getElementById("nav-modal-slider");
const sliderValue = document.getElementById("slider-value");
function slider(){
    valPercent = (mySlider.value / mySlider.max)*100;
    mySlider.style.background = `linear-gradient(to right, #3264fe ${valPercent}%, #d5d5d5 ${valPercent}%)`;
    sliderValue.textContent = mySlider.value;
}
slider();

//Sidebar

$(function() {
    $('nav-sidebar').each(function() {
        var $active, $content, $links = $(this).find('a');

        $active = $($links.filter('[href="' + location.hash + '"]')[0] || $links[0]);
        $active.addClass('active');

        $content = $($active[0].hash);

        $links.not($active).each(function() {
            $(this.hash).hide();
        });

        $(this).on('click', 'a', function(e) {
            $active.removeClass('active');
            $content.hide();

            $active = $(this);
            $content = $(this.hash);

            $active.addClass('active');
            $content.show();

            e.preventDefault();
        });
    });
});

// Toggle sidebar
const sidebarContent = document.querySelector('.sidebar-content');
const sidebarContentLinks = document.querySelectorAll('.sidebar-content-link');
const sidebarContentToggle = document.querySelector('.sidebar-content-toggle');

sidebarContentLinks.forEach(function(link) {
  link.addEventListener('click', function(e) {
    e.preventDefault();
    sidebarContent.classList.remove('collapsed');
  });
});

sidebarContentToggle.addEventListener('click', function() {
  sidebarContent.classList.add('collapsed');
});

//Variable settings dropdown
const table = document.getElementById('table1');
const dropdown1 = document.getElementById('model-dropdown');
const dropdown2 = document.getElementById('cross-section-dropdown');
const dropdown3 = document.getElementById('time-series-dropdown');

// Loop through the rows in the table
for (let i = 1; i < table.rows.length; i++) {
const variable = table.rows[i].cells[0].innerText;

// Create an option element for each variable in the table
const option1 = document.createElement('option');
const option2 = document.createElement('option');
const option3 = document.createElement('option');

// Set the value and text of the option elements to the variable
option1.value = variable;
option1.text = variable;
option2.value = variable;
option2.text = variable;
option3.value = variable;
option3.text = variable;

// Add the option elements to the corresponding dropdowns
dropdown1.appendChild(option1);
dropdown2.appendChild(option2);
dropdown3.appendChild(option3);
}

  const applyToleranceCheckbox = document.getElementById('apply-tolerance');
  const toleranceContainer = document.querySelector('.tolerance-box');

  applyToleranceCheckbox.addEventListener('change', () => {
    toleranceContainer.style.display = applyToleranceCheckbox.checked ? 'block' : 'none';
  });

// Send settings selection to backend
  $(document).ready(function() {
    $("#saveButton").on("click", function() {
      // Get selected values from the dropdowns and other input elements
      var modelClass = $("#model-class-dropdown").val();
      var modelField = $("#model-dropdown").val();
      var targetVariable = $("#target-dropdown").val();
      var crossSectionField = $("#cross-section-dropdown").val();
      var useAsCrossSectional = $("#cross-checkbox").prop("checked");
      var timeSeriesField = $("#time-series-dropdown").val();
      var minTValue = $("#t-value").val();
      var tolerance = $("#tolerance-input").val();
      var applyTolerance = $("#apply-tolerance").prop("checked");

      // Create an object with the data to be sent
      var data = {
        modelClass: modelClass,
        modelField: modelField,
        targetVariable: targetVariable,
        crossSectionField: crossSectionField,
        useAsCrossSectional: useAsCrossSectional,
        timeSeriesField: timeSeriesField,
        minTValue: minTValue,
        tolerance: tolerance,
        applyTolerance: applyTolerance
      };

      // Send the data to the backend using AJAX
      $.ajax({
        type: "POST",
        url: "/save_settings",
        data: JSON.stringify(data),
        contentType: "application/json",
        success: function(response) {
          // Handle the response from the backend if needed
          console.log("Saved!");
        },
        error: function(error) {
          // Handle the error if the request fails
          console.error("Error Saving Preference:", error);
        }
      });
    });
    $.ajax({
      url: '/load_settings',
      method: 'GET',
      success: function(data) {
        $('#model-class-dropdown').val(data.modelClass);
        $('#model-dropdown').val(data.modelField);
        $('#target-dropdown').val(data.targetVariable);
        $('#cross-section-dropdown').val(data.crossSectionField);
        $('#cross-checkbox').val(data.useAsCrossSectional);
        $('#time-series-dropdown').val(data.timeSeriesField);
        $('#t-value').val(data.minTValue);
        $('#tolerance-input').val(data.tolerance);
        $('#apply-tolerance').val(data.applyTolerance);
          
      }
  });



});
 

