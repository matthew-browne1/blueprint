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
      console.log("/channel"+tableID)

       var tabChannelTable = $("#channel" + tableID).DataTable({
         destroy: true,
         dom: "Blfrtip",
         ajax: {
           url: "/channel_main",
           contentType: "application/json",
           dataSrc: tableID.toString(),
         },
         drawCallback: function () {
           $(".sparkline" + tableID)
             .map(function () {
               return $("canvas", this).length ? null : this;
             })
             .sparkline("html", {
               type: "line",
               width: "250px",
             });
         },
         columns: [
          { data: null },
           { data: "Region" },
           { data: "Brand" },
           { data: "Channel" },
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
                 ? '<span class="sparkline' +
                     tableID +
                     '">' +
                     data.toString() +
                     "</span>"
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
           { className: "dt-head-center", targets: [0, 1, 2, 3, 4, 5, 6, 7] }
         ],
         rowId: "row_id",
       });
       
        var channelEditorTab = new $.fn.dataTable.Editor({
          ajax: {
            type: "POST",
            url: "/table_data_editor",
            contentType: "application/json", // Set the content type to JSON
            data: function (d) {
              d.tableId = tableID;
              return JSON.stringify(d); // Convert the data to JSON string
            }
          },
          table: "#channel" + tableID,
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
        tabChannelTable.on(
          "mouseenter",
          "tbody td:nth-child(0), tbody td:nth-child(7), tbody td:nth-child(6)",
          function (e) {
            $(this).css({
              cursor: "text",
              userSelect: "none",
            });
          }
        );

         tabChannelTable.on(
           "mouseleave",
           "tbody td:nth-child(0), tbody td:nth-child(7), tbody td:nth-child(6)",
           function (e) {
             $(this).css({
               cursor: "default",
               userSelect: "auto",
             });
           }
         );

         tabChannelTable.on(
           "click",
           "tbody td:nth-child(7), tbody td:nth-child(6)",
           function (e) {
             channelEditorTab.inline(this);
           }
         );
          $("#example-select-all"+tableID).on("click", function () {
            // Get all rows with search applied
            var rows = tabChannelTable.rows({ search: "applied" }).nodes();
            // Check/uncheck checkboxes for all rows in the table
            $('input[type="checkbox"]', rows).prop("checked", this.checked);
            if (!this.checked) {
              $(rows).addClass("disabled");
            } else {
              $(rows).removeClass("disabled");
            }
          });
             $("#channel"+tableID+" tbody").on(
               "change",
               'input[type="checkbox"]',
               function () {
                 // If checkbox is not checked
                 if (!this.checked) {
                   var el = $("#example-select-all"+tableID).get(0);
                   // If "Select all" control is checked and has 'indeterminate' property
                   if (el && el.checked && "indeterminate" in el) {
                     // Set visual state of "Select all" control
                     // as 'indeterminate'
                     el.indeterminate = true;
                   }
                 }
               });
              $("#frm-example"+tableID).on("submit", function (e) {
                var form = this;

                // Iterate over all checkboxes in the table
                tabChannelTable.$('input[type="checkbox"]').each(function () {
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

                $("#channel"+tableID+" tbody").on(
                  "change",
                  'input[type="checkbox"]',
                  function () {
                    var row = $(this).closest("tr");
                    var rowId = tabChannelTable.row(row).id();
                    var isChecked = $(this).prop("checked");
                    if (isChecked) {
                      tabChannelTable
                        .row(row)
                        .nodes()
                        .to$()
                        .removeClass("disabled");
                      console.log("removing class");
                    } else {
                      tabChannelTable.row(row).nodes().to$().addClass("disabled");
                      console.log("adding class");
                    }
                  }
                );
                    $.ajax({
                      url: "/date_range",
                      type: "GET",
                      dataType: "json",
                      success: function (data) {
                        console.log("fetching and applying dates");
                        // Set the fetched dates as default values for date inputs

                        var startDate = new Date(data.startDate)
                          .toISOString()
                          .split("T")[0];
                        var endDate = new Date(data.endDate)
                          .toISOString()
                          .split("T")[0];

                        $("#start-date"+tableID).val(startDate);
                        $("#start-date"+tableID).prop("min", startDate);
                        $("#start-date"+tableID).prop("max", endDate);
                        $("#end-date"+tableID).val(endDate);
                        $("#end-date"+tableID).prop("min", startDate);
                        $("#end-date"+tableID).prop("max", endDate);
                      },
                      error: function (error) {
                        console.error("Error fetching dates:", error);
                      },
                    });
                function getDisabledRowIds() {
                  var disabledRowIds = [];

                  tabChannelTable
                    .rows(".disabled")
                    .data()
                    .each(function (row) {
                      var rowId = row.row_id;
                      disabledRowIds.push(rowId);
                    });

                  return disabledRowIds;
                }

                  var obj = document.getElementById("obj-input" + tableID);
                  var exh = document.getElementById("exh-input" + tableID);
                  var max = document.getElementById("max-input" + tableID);
                  var optButton = document.getElementById("opt-button" + tableID);
                  var blend = document.getElementById("blend-input" + tableID);
                  var ftol = document.getElementById("ftol-input" + tableID);
                  var ssize = document.getElementById("step-size-input" + tableID);

                  optButton.addEventListener("click", function () {
                    showLoadingOverlay(tableID);
                    var objValue = obj.value;
                    var exhValue = exh.value;
                    var maxValue = max.value;
                    var blendValue = blend.value;
                    var ftolValue = ftol.value;
                    var ssizeValue = ssize.value;
                    var disabledRowIds = getDisabledRowIds();
                    var tabName = fetchTabName(1);

                    var dataToSend = {
                      objectiveValue: objValue,
                      exhaustValue: exhValue,
                      maxValue: maxValue,
                      blendValue: blendValue,
                      tableID: tableID,
                      ftolValue: ftolValue,
                      ssizeValue: ssizeValue,
                      disabledRows: disabledRowIds,
                      tabName: tabName
                    };
                        var dateButtonIsChecked = $(
                          "#date-filter-button"+tableID
                        ).prop("checked");
                        var startDate = $("#start-date"+tableID).val();
                        var endDate = $("#end-date"+tableID).val();
                        var dateTuple = [startDate, endDate];
                        if (!dateButtonIsChecked) {
                          dataToSend["dates"] = dateTuple;
                        }
                    console.log(dataToSend);

                    // Use jQuery AJAX to send the data to the Flask endpoint
                    tabSocket.emit("optimise", {dataToSend: dataToSend});
                  });
              

     },
     error: function (error) {
       console.error("Error creating copy of data:", error);
     },
   });
  $("#date-filter-button"+tableID).on("click", function () {
    var isChecked = $(this).prop("checked");
    var dateContainers = $(".date-inputs"+tableID);

    if (!isChecked) {
      console.log("date button is unchecked");
      dateContainers.addClass("greyed-out");
    } else {
      console.log("date button is checked");
      dateContainers.removeClass("greyed-out");
    }
  });

}

function fetchTabName(setID) {
  var buttonText = document.getElementById("button-text" + setID);
  var tabName = buttonText.innerText;
  return tabName;
}

// function initializeButtons(setID) {
//   var obj = document.getElementById("obj-input" + setID);
//   var exh = document.getElementById("exh-input" + setID);
//   var max = document.getElementById("max-input" + setID);
//   var optButton = document.getElementById("opt-button" + setID);
//   var blend = document.getElementById("blend-input" + setID);

//   optButton.addEventListener("click", function () {
//     showLoadingOverlay(setID)
//     var objValue = obj.value;
//     var exhValue = exh.value;
//     var maxValue = max.value;
//     var blendValue = blend.value;

//     var dataToSend = {
//       objectiveValue: objValue,
//       exhaustValue: exhValue,
//       maxValue: maxValue,
//       blendValue: blendValue,
//       tableID: setID
//     };

//     // Use jQuery AJAX to send the data to the Flask endpoint
//     $.ajax({
//       type: "POST", // Use POST method
//       url: "/optimise", // Replace with your actual Flask endpoint URL
//       contentType: "application/json",
//       data: JSON.stringify(dataToSend), // Convert data to JSON format
//       success: function (response) {
//         // Handle the response from the Flask endpoint here
//         console.log(response);
//         optResults = response;
//         // alert(JSON.stringify(response))
//         hideLoadingOverlay(setID)
//       },
//       error: function (error) {
//         // Handle any errors that occur during the AJAX request
//         console.error("AJAX request error:", error);
//       },
//     });
//   });
// }

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


function showLoadingOverlay(tableID) {
  document.getElementById("loading-overlay"+tableID).style.display = "block";
}

function hideLoadingOverlay(tableID) {
  document.getElementById("loading-overlay"+tableID).style.display = "none";
}

function destroyTables(tableID) {
  for (var i = 1; i < tableID; i++) {
    console.log(i);
    $('#channel' + i).DataTable().clear().destroy();
    console.log("#channel"+i+" destroyed");
  }
}
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
var tabSocket = io.connect(window.location.origin);

tabSocket.on('connect', function() {
  console.log("connected to server");
});

tabSocket.on('opt_complete', function(data) {
  var tableID = data.data;
  console.log('hiding the loading overlay for channel table '+tableID)
  hideLoadingOverlay(tableID);
  showResultsButton();
});

