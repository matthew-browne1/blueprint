

$(document).ready(function() {
  sendTableIDsOnRefresh();
  newTabButtonInit();
  syncTabCounter();
  var optAllBtn = document.getElementById("optimise-all");
  optAllBtn.addEventListener("click", optAll);
});

var optResults = {};

// ANY EDITS MADE TO THIS FUNCTION, REMEMBER TO ALSO CHANGE THEM IN THE IDENTICAL FUNCTION IN SAVEUI.JS

function initializeInitialTable() {
  
  var channelTable = $("#channel1").DataTable({
    dom: "Blfrtip",
    ajax: {
      url: "/channel_main",
      contentType: "application/json",
      dataSrc: "1",
    },
    drawCallback: function () {
      $(".sparkline1").sparkline("html", {
        type: "line",
        width: "250px",
      });
    },
    columns: [
      { data: null },
      { data: "Region" },
      { data: "Brand" },
      { data: "Channel" },
      // { data: "Beta", render: $.fn.DataTable.render.number(",", ".", 0, "") },
      {
        data: "Current Budget",
        render: $.fn.DataTable.render.number(",", ".", 0, "£"),
      },
      {
        data: "Min Spend Cap",
        render: $.fn.DataTable.render.number(",", ".", 0, "£"),
      },
      {
        data: "Max Spend Cap",
        render: $.fn.DataTable.render.number(",", ".", 0, "£"),
      },

      {
        data: "Laydown",
        render: function (data, type, row, meta) {
          return type === "display"
            ? '<span class="sparkline1">' + data.toString() + "</span>"
            : data;
        },
      },
    ],
    autoWidth: false,
    columnDefs: [
      { width: "50px", targets: 0 },
      { width: "80px", targets: 1 },
      { width: "80px", targets: 2 },
      { width: "80px", targets: 3 },
      { width: "80px", targets: 4 },
      { width: "80px", targets: 5 },
      { width: "80px", targets: 6 },
      { width: "250px", targets: 7 },
      {
        targets: 0,
        searchable: false,
        orderable: false,
        className: "dt-body-center",
        render: function (data, type, full, meta) {
          return (
            '<input type="checkbox" name="id[]" checked value="' +
            $("<div/>").text(data).html() +
            '">'
          );
        },
      },
      { className: "dt-head-center", targets: [0,1,2,3,4,5,6,7]}
    ],
    rowId: "row_id",
  });
  attachButtonListenersToDataTable();
  var channelEditor = new $.fn.dataTable.Editor({
    ajax: {
      type: 'POST',
      url: '/table_data_editor',
      contentType: 'application/json', // Set the content type to JSON
      data: function (d) {
        d.tableId = "1";
        return JSON.stringify(d); // Convert the data to JSON string
      }
    },
    table: "#channel1",
    fields: [
      {
        label: "Min Spend Cap:",
        name: "Min Spend Cap",
      },
      {
        label: "Max Spend Cap:",
        name: "Max Spend Cap",
      },
    ],
    idSrc: "row_id",
  });

channelTable.on(
  "mouseenter",
  "tbody td:nth-child(0), tbody td:nth-child(7), tbody td:nth-child(6)",
  function (e) {
    $(this).css({
      cursor: "text",
      userSelect: "none",
    });
  }
);

channelTable.on(
  "mouseleave",
  "tbody td:nth-child(0), tbody td:nth-child(7), tbody td:nth-child(6)",
  function (e) {
    $(this).css({
      cursor: "default",
      userSelect: "auto",
    });
  }
);

channelTable.on(
  "click",
  "tbody td:nth-child(7), tbody td:nth-child(6)",
  function (e) {
    channelEditor.inline(this);
  }
);
  // channelTable.on("page.dt", function () {
  //   channelTable.ajax.reload(null, false);
  // });
   $("#example-select-all").on("click", function () {
     // Get all rows with search applied
     var rows = channelTable.rows({ search: "applied" }).nodes();
     // Check/uncheck checkboxes for all rows in the table
     $('input[type="checkbox"]', rows).prop("checked", this.checked);
      if (!this.checked) {
        $(rows).addClass("disabled");
      } else {
        $(rows).removeClass("disabled");
      }
   });

   // Handle click on checkbox to set state of "Select all" control
   $("#channel1 tbody").on("change", 'input[type="checkbox"]', function () {
     // If checkbox is not checked
     if (!this.checked) {
       var el = $("#example-select-all").get(0);
       // If "Select all" control is checked and has 'indeterminate' property
       if (el && el.checked && "indeterminate" in el) {
         // Set visual state of "Select all" control
         // as 'indeterminate'
         el.indeterminate = true;
       }
     }
   });

   // Handle form submission event
   $("#frm-example").on("submit", function (e) {
     var form = this;

     // Iterate over all checkboxes in the table
     channelTable.$('input[type="checkbox"]').each(function () {
       // If checkbox doesn't exist in DOM
       if (!$.contains(document, this)) {
         // If checkbox is checked
         if (this.checked) {
           // Create a hidden element
           $(form).append(
             $("<input>")
               .attr("type", "hidden")
               .attr("name", this.name)
               .val(this.value)
           );
         }
       }
     });
   });

   $("#channel1 tbody").on("change", 'input[type="checkbox"]', function () {
     var row = $(this).closest("tr");
     var rowId = channelTable.row(row).id();
     var isChecked = $(this).prop("checked")
     if (isChecked) {
       channelTable.row(row).nodes().to$().removeClass("disabled");
       console.log("removing class");
     } else {
       channelTable.row(row).nodes().to$().addClass("disabled");
       console.log("adding class");
     }
   });

  function getDisabledRowIds() {
    var disabledRowIds = [];

    channelTable
      .rows(".disabled")
      .data()
      .each(function (row) {
        var rowId = row.row_id;
        disabledRowIds.push(rowId);
      });

    return disabledRowIds;
  }
  
document.addEventListener("DOMContentLoaded", function () {
  var obj = document.getElementById("obj-input1");
  var exh = document.getElementById("exh-input1");
  var max = document.getElementById("max-input1");
  var optButton = document.getElementById("opt-button1");
  var blend = document.getElementById("blend-input1");

  optButton.addEventListener("click", function () {
    sendToggleStatesToBackend();
    showLoadingOverlay();
    var objValue = obj.value;
    var exhValue = exh.value;
    var maxValue = max.value;
    var blendValue = blend.value;
    var disabledRowIds = getDisabledRowIds();

    var dataToSend = {
      objectiveValue: objValue,
      exhaustValue: exhValue,
      maxValue: maxValue,
      blendValue: blendValue,
      tableID: 1,
      disabledRows: disabledRowIds
    };
    var dateButtonIsChecked = $("#date-filter-button1").prop("checked");
    var startDate = $("#start-date1").datepicker("getDate");
    var endDate = $("#end-date1").datepicker("getDate");
    var dateTuple = [startDate, endDate];
    if (!dateButtonIsChecked) {
      dataToSend[dates] = dateTuple;
    }
    console.log(dataToSend);

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
        showResultsButton();
        hideLoadingOverlay();
      },
      error: function (error) {
        // Handle any errors that occur during the AJAX request
        console.error("AJAX request error:", error);
        hideLoadingOverlay();
      },
    });
  });
});
}

initializeInitialTable();

function showResultsButton() {
  var div = document.getElementById("results-div");
  var existingButton = document.getElementById("results-button");

  if (existingButton) {
    // If the button already exists, update its innerHTML to "Update Results"
    existingButton.innerHTML = "Update Results";
  } else {
    // If the button doesn't exist, create a new button and add it to the div
    var buttonHtml =
      '<button class="button-5" role="button" id="results-button">Show Results</button>';

    // Create a new div element and set its innerHTML to the buttonHtml
    var tempDiv = document.createElement("div");
    tempDiv.innerHTML = buttonHtml;

    // Append the first child of tempDiv (which is the newly created button element) to the actual div
    div.appendChild(tempDiv.firstChild);

    // Trigger a resize event (you may remove this line if it's not necessary)
    var event = new Event("resize");
    window.dispatchEvent(event);
  }
}

function showLoadingOverlay() {
  document.getElementById("loading-overlay1").style.display = "block";
}

function hideLoadingOverlay() {
  document.getElementById("loading-overlay1").style.display = "none";
}

$(".dropdown").click(function () {
  $(this).attr("tabindex", 1).focus();
  $(this).toggleClass("active");
  $(this).find(".dropdown-menu").slideToggle(300);
});
$(".dropdown").focusout(function () {
  $(this).removeClass("active");
  $(this).find(".dropdown-menu").slideUp(300);
});
$(".dropdown .dropdown-menu li").click(function () {
  $(this).parents(".dropdown").find("span").text($(this).text());
  $(this).parents(".dropdown").find("input").attr("value", $(this).attr("id"));
});


$(document).on("change", ".checkbox.main", function () {
  if ($(this).is(":checked")) {
    // If the static checkbox is checked, set all dynamically added checkboxes to checked
    $("#channel1 tbody .checkbox").prop("checked", true);
  } else {
    $("#channel1 tbody .checkbox").prop("checked", false);
  }
});

var data = {}

document.addEventListener("click", function (e) {

  const target = e.target.closest("#lock-button"); 

  if (target) {
    const closestRow = target.closest("tr");
    if (closestRow) {
      const rowText = closestRow.querySelector("td:first-child").textContent; // Assumes the row content is in the first <td>
      var channel = rowText.trim();
    }
  }
});

$(document).ready(function() {
    // Make an AJAX request to the Flask endpoint
    $.ajax({
        url: '/date_range',
        type: 'GET',
        dataType: 'json',
        success: function(data) {
            // Set the fetched dates as default values for date inputs
            $('#start-date1').val(data.startDate);
            $('#start-date1').prop('min', data.startDate);
            $("#start-date1").prop("max", data.endDate);
            $('#end-date1').val(data.endDate);
            $("#end-date1").prop("min", data.startDate);
            $("#end-date1").prop("max", data.endDate);
        },
        error: function(error) {
            console.error('Error fetching dates:', error);
        }
    });
});

const toggleStates = {};
function attachButtonListenersToDataTable() {
  // Assuming your DataTable has an ID, replace 'channel' with the actual ID
  const dataTableCont = document.getElementById("channel-container1");

  if (dataTableCont) {
    dataTableCont.addEventListener("change", function (e) {
      const target = e.target.closest(".checkbox");

      if (target) {
        const closestRow = target.closest("tr");

        if (closestRow) {
          const rowText = closestRow
            .querySelector("td:first-child")
            .textContent.trim();
          console.log(`Button clicked in row: ${rowText}`);
          // Add your logic for handling button click in a row here
          toggleStates[rowText] = target.checked;
        } else {
          console.log("Button clicked, but not in a row.");
        }
      }
    });
  } else {
    console.error("DataTable with ID 'channel' not found.");
  }
}



function sendToggleStatesToBackend() {
  console.log(toggleStates);
  // Make an AJAX request to send toggleStates to the backend using jQuery
  $.ajax({
    url: "/toggle_states",
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


function openNewTab() {
  console.log("opening new tab");
  var tabExists = false;
  window.open("/blueprint_results", "_blank");
  }

  
  $("#results-div").on("click", "#results-button", function () {
    console.log(tabNames);
    console.log("results button clicked");
    $.ajax({
      type: "POST",
      url: "/results_output",
      contentType: "application/json",
      data: JSON.stringify(tabNames),
      success: function (response) {
        console.log("results csv produced");
        openNewTab();
      },
      error: function (error) {
        console.error("Error triggering function:", error);
      },
    });
  });

  $(function () {
    $("#start-date1").datepicker();
  });

  $(function () {
    $("#end-date1").datepicker();
  });

$("#date-filter-button1").on("click", function () {
  var isChecked = $(this).prop("checked");
  var dateContainers = $(".date-inputs");

  if (isChecked) {
    console.log("date button is unchecked");
    dateContainers.addClass("greyed-out");
  } else {
    console.log("date button is checked");
    dateContainers.removeClass("greyed-out");
  }
});

function optimiseSingle(setID) {
  showLoadingOverlay(setID);
  var obj = document.getElementById("obj-input" + setID);
  var exh = document.getElementById("exh-input" + setID);
  var max = document.getElementById("max-input" + setID);
  var optButton = document.getElementById("opt-button" + setID);
  var blend = document.getElementById("blend-input" + setID);
    
  var objValue = obj.value;
  var exhValue = exh.value;
  var maxValue = max.value;
  var blendValue = blend.value;

  var dataToSend = {
    objectiveValue: objValue,
    exhaustValue: exhValue,
    maxValue: maxValue,
    blendValue: blendValue,
    tableID: setID,
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
      hideLoadingOverlay(setID);
    },
    error: function (error) {
      // Handle any errors that occur during the AJAX request
      console.error("AJAX request error:", error);
      hideLoadingOverlay(setID);
    },
  });

}

function optAll() {
  $.ajax({
    url: "get_table_ids",
    method: "GET",
    contentType: "application/json",
    success: function (response) {
      if (response && response.tableIds) {
        console.log(response.tableIds);
        var tableIds = response.tableIds;
        tableIds.forEach(function (setID) {
            showLoadingOverlay(setID);
            var obj = document.getElementById("obj-input" + setID);
            var exh = document.getElementById("exh-input" + setID);
            var max = document.getElementById("max-input" + setID);
            var optButton = document.getElementById("opt-button" + setID);
            var blend = document.getElementById("blend-input" + setID);

            var objValue = obj.value;
            var exhValue = exh.value;
            var maxValue = max.value;
            var blendValue = blend.value;

            var dataToSend = {
              objectiveValue: objValue,
              exhaustValue: exhValue,
              maxValue: maxValue,
              blendValue: blendValue,
              tableID: setID,
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
                hideLoadingOverlay(setID);
              },
              error: function (error) {
                // Handle any errors that occur during the AJAX request
                console.error("AJAX request error:", error);
                hideLoadingOverlay(setID);
              },
            });
        });
      }
    },
  });
}

