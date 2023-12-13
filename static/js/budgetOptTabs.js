function dropdownButtons(dropdownId) {
  $("#dd-obj" + dropdownId).click(function () {
    $(this).attr("tabindex", 1).focus();
    $(this).toggleClass("active");
    $(this).find(".dropdown-menu").slideToggle(300);
  });
  $("#dd-obj" + dropdownId).focusout(function () {
    $(this).removeClass("active");
    $(this).find(".dropdown-menu").slideUp(300);
  });
  $("#dd-obj" + dropdownId + " .dropdown-menu li").click(function () {
    $(this)
      .parents("#dd-obj" + dropdownId)
      .find("span")
      .text($(this).text());
    $(this)
      .parents("#dd-obj" + dropdownId)
      .find("input")
      .attr("value", $(this).attr("id"));
  });

  $("#dd-exh" + dropdownId).click(function () {
    $(this).attr("tabindex", 1).focus();
    $(this).toggleClass("active");
    $(this).find(".dropdown-menu").slideToggle(300);
  });
  $("#dd-exh" + dropdownId).focusout(function () {
    $(this).removeClass("active");
    $(this).find(".dropdown-menu").slideUp(300);
  });
  $("#dd-exh" + dropdownId + " .dropdown-menu li").click(function () {
    $(this)
      .parents("#dd-exh" + dropdownId)
      .find("span")
      .text($(this).text());
    $(this)
      .parents("#dd-exh" + dropdownId)
      .find("input")
      .attr("value", $(this).attr("id"));
  });

  $("#dd-blend" + dropdownId).click(function () {
    $(this).attr("tabindex", 1).focus();
    $(this).toggleClass("active");
    $(this).find(".dropdown-menu").slideToggle(300);
  });
  $("#dd-blend" + dropdownId).focusout(function () {
    $(this).removeClass("active");
    $(this).find(".dropdown-menu").slideUp(300);
  });
  $("#dd-blend" + dropdownId + " .dropdown-menu li").click(function () {
    $(this)
      .parents("#dd-blend" + dropdownId)
      .find("span")
      .text($(this).text());
    $(this)
      .parents("#dd-blend" + dropdownId)
      .find("input")
      .attr("value", $(this).attr("id"));
  });
}


function initializeDataTable(tableID) {

   $.ajax({
     type: "POST",
     url: "/create_copy",
     data: { tableID: tableID },
     success: function (response) {



      console.log("pinged create_copy")
      console.log("/channel/"+tableID)

       $("#channel" + tableID).DataTable({
         destroy: true,
         dom: "Blfrtip",
         ajax: {
           url: "/channel_main",
           contentType: "application/json",
           dataSrc: tableID.toString(),
         },
         columns: [
           { data: "Channel" },
           { data: "Carryover" },
           { data: "Alpha" },
           {
             data: "Beta",
             render: $.fn.DataTable.render.number(",", ".", 0, ""),
           },
           {
             data: "Current_Budget",
             render: $.fn.DataTable.render.number(",", ".", 0, "£"),
           },
           {
             data: "Min_Spend_Cap",
             render: $.fn.DataTable.render.number(",", ".", 0, "£"),
           },
           {
             data: "Max_Spend_Cap",
             render: $.fn.DataTable.render.number(",", ".", 0, "£"),
           },
           {
             data: null,
             defaultContent:
               '<div class="toggle-button-cover"><div class="button-cover"><div class="button r" id="lock-button"><input type="checkbox" class="checkbox" /><div class="knobs"></div><div class="layer"></div></div></div></div>',
           },
           {
             data: "Laydown",
             render: function (data, type, row, meta) {
               var sparklineID = "sparkline" + tableID;
               return type === "display"
                 ? '<span class="' +
                     sparklineID +
                     '" id="' +
                     sparklineID +
                     '">' +
                     data.toString() +
                     "</span>"
                 : data;
             },
           },
         ],
         select: {
           style: "os",
         },
         autoWidth: false,
         columnDefs: [
           { width: "80px", targets: 0 }, // Set width for the first column (Channel)
           { width: "80px", targets: 1 }, // Set width for the second column (Carryover)
           { width: "80px", targets: 2 }, // Set width for the third column (Alpha)
           { width: "80px", targets: 3 }, // Set width for the fourth column (Beta)
           { width: "80px", targets: 4 }, // Set width for the fourth column (Beta)
           { width: "80px", targets: 5 }, // Set width for the fifth column (Max Spend Cap)
           { width: "80px", targets: 6 }, // Set width for the fifth column (Max Spend Cap)
           { width: "40px", targets: 7 }, // Set width for the fifth column (Max Spend Cap)
           { width: "250px", targets: 8 }, // Set width for the fifth column (Max Spend Cap)
         ],
         drawCallback: function () {
           $(".sparkline" + tableID).sparkline("html", {
             type: "line",
             width: "250px",
           });
         },
       });
     },
     error: function (error) {
       console.error("Error creating copy of data:", error);
     },
   });
  
  $("#channel" + tableID).DataTable().on("page.dt", function () {
    $("#channel" + tableID).DataTable().ajax.reload(null, false);
  });

  attachButtonListenersToDataTable(tableID);
  redrawAllSparklines(tableID);
  // initializeToggleAllButton(tableID);
    $(document).on("change", ".checkbox.main"+tableID, function () {
      if ($(this).is(":checked")) {
        // If the static checkbox is checked, set all dynamically added checkboxes to checked
        $("#channel" + tableID + " tbody .checkbox").prop("checked", true);
      } else {
        $("#channel" + tableID + " tbody .checkbox").prop("checked", false);
      }
    });
}

function initializeButtons(setID) {
  var obj = document.getElementById("obj-input" + setID);
  var exh = document.getElementById("exh-input" + setID);
  var max = document.getElementById("max-input" + setID);
  var optButton = document.getElementById("opt-button" + setID);
  var blend = document.getElementById("blend-input" + setID);

  optButton.addEventListener("click", function () {
    showLoadingOverlay(setID)
    var objValue = obj.value;
    var exhValue = exh.value;
    var maxValue = max.value;
    var blendValue = blend.value;

    var dataToSend = {
      objectiveValue: objValue,
      exhaustValue: exhValue,
      maxValue: maxValue,
      blendValue: blendValue,
      tableID: setID
    };

    // Use jQuery AJAX to send the data to the Flask endpoint
    $.ajax({
      type: "POST", // Use POST method
      url: "/optimise", // Replace with your actual Flask endpoint URL
      contentType: "application/json",
      data: JSON.stringify(dataToSend), // Convert data to JSON format
      success: function (response) {
        // Handle the response from the Flask endpoint here
        console.log(response);
        optResults = response;
        // alert(JSON.stringify(response))
        hideLoadingOverlay(setID)
      },
      error: function (error) {
        // Handle any errors that occur during the AJAX request
        console.error("AJAX request error:", error);
      },
    });
  });
}

function redrawAllSparklines(tableID) {
  for (var i = 1; i < tableID; i++) {
    var currentTableID = i;
    $("#sparkline" + currentTableID).each(function () {
      var $sparkline = $(this);
      var sparklineData = $sparkline.text();
      $sparkline.empty().sparkline(sparklineData, {
        type: "line",
        width: "250px",
      });
    });
  }
}

function redrawAllTables(tableID) {
  $("#channel1").DataTable().ajax.reload(null, false);
  for (var i = 2; i < tableID; i++) {
    var currentTableId = i;
    $("#channel" + currentTableId)
      .DataTable()
      .ajax.reload(null, false);
  }
}


const toggleStates = {};
function attachButtonListenersToDataTable(tableID) {
  // Assuming your DataTable has an ID, replace 'channel' with the actual ID
  const dataTable = document.getElementById("channel"+tableID);

  if (dataTable) {
    dataTable.addEventListener("click", function (e) {
      const target = e.target.closest(".checkbox");

      if (target) {
        const closestRow = target.closest("tr");

        if (closestRow) {
          const rowText = closestRow
            .querySelector("td:first-child")
            .textContent.trim();
          console.log(`Button clicked in row: ${rowText}`);
          toggleStates[rowText] = target.checked;
          // Add your logic for handling button click in a row here
        } else {
          console.log("Button clicked, but not in a row.");
        }
      }
    });
  } 
}

function sendToggleStatesToBackend() {


  // Make an AJAX request to send toggleStates to the backend using jQuery
  $.ajax({
    url: '/toggle_states',
    type: "POST", // You might need to adjust the method based on your backend API
    contentType: "application/json",
    data: JSON.stringify(toggleStates),
    success: function (data) {
      console.log("Response from backend:", data);
      // Add any further handling based on the backend response
    },
    error: function (error) {
      console.error("Error sending toggle states to backend:", error);
    },
  });
}

function showLoadingOverlay(tableID) {
  document.getElementById("loading-overlay"+tableID).style.display = "block";
}

function hideLoadingOverlay(tableID) {
  document.getElementById("loading-overlay"+tableID).style.display = "none";
}