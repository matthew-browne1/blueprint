var tabNames = { 1: "Scenario 1" };

var tabCounter = 1;

var initialButtonName = document.getElementById("button-text" + tabCounter);
tabNames[tabCounter] = initialButtonName.textContent;
console.log(tabNames);


$(document).ready(function () {
  initializeInitialButton();
  sendTableIDsOnRefresh();
  newTabButtonInit();
  syncTabCounter();
  var optAllBtn = document.getElementById("optimise-all");
  optAllBtn.addEventListener("click", optAll);

});
var socket = io.connect(window.location.origin);
socket.on("connect", function () {
  console.log("connected to server");
});

var optResults = {};

function showWarningPopup() {
  $("warningPopup").show();
}
function closeWarningPopup() {
  $("warningPopup").hide();
}



function newTabButtonInit() {
  document
    .getElementById("new-tab-button")
    .addEventListener("click", spawnNewTab)
}


function spawnNewTab() {
      tabCounter++;

      // Clone the HTML content and append it to the document
      var tabContent = document.createElement("div");
      tabContent.setAttribute("id", "new-tab" + tabCounter);
      tabContent.innerHTML = `
           <button type="button" id="col-btn${tabCounter}" class="collapsible">
            <span id="button-text${tabCounter}">Scenario ${tabCounter}</span>
            <span>&nbsp;</span>
            <span>&nbsp;</span>
            <i class="fa-solid fa-pen-to-square fa-lg" onclick="editButtonTabs(${tabCounter})"></i>
            <i class="fa-solid fa-x fa-xl close-icon" id="close-button${tabCounter}"></i>
         </button>
           <div class="content" id="opt-tab${tabCounter}">
            <div class="loading-overlay" id="loading-overlay${tabCounter}">
               <div class="searchLoader">
                  <svg id="loading-wheel" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 60 60">
                  <style>
                  .st0{opacity:0.1;} .st1{opacity:0.33;} .st2{opacity:0.66;}
                  </style>
                  <path d="M30 0c1 0 1.8.8 1.8 1.8v7.8h-3.6V1.8C28.2.8 29 0 30 0zM1.8 28.2h7.8v3.6H1.8C.8 31.8 0 31 0 30s.8-1.8 1.8-1.8zM9.6 47.8l3.4-3.4 1.3-1.3 2.6 2.6-1.3 1.3-3.4 3.4-.9.9c-.4.4-.8.5-1.3.5s-.9-.2-1.3-.5c-.7-.7-.7-1.8 0-2.6l.9-.9z"/>
                  <path class="st0" d="M48.7 8.8c.7-.7 1.8-.7 2.6 0 .7.7.7 1.8 0 2.6l-.9.9-3 3-.4.3-1.3 1.3-2.6-2.6 1.7-1.7 3.9-3.8z"/>
                  <path d="M31.8 52.2v6.1c0 1-.8 1.8-1.8 1.8s-1.8-.8-1.8-1.8V50.4h3.6v1.8z"/>
                  <path class="st1" d="M50.4 28.2h7.8c1 0 1.8.8 1.8 1.8s-.8 1.8-1.8 1.8h-7.8v-3.6z"/>
                  <path d="M10.7 13.3l-1.9-1.9c-.7-.7-.7-1.8 0-2.6.7-.7 1.8-.7 2.6 0l4.3 4.3 1.3 1.3-2.6 2.6-3.7-3.7z"/>
                  <path class="st2" d="M47 44.4l.4.4 3 3 .9.9c.7.7.7 1.8 0 2.6-.4.4-.8.5-1.3.5s-.9-.2-1.3-.5l-3.8-3.8-1.7-1.7 2.6-2.6 1.2 1.2z"/>
                  </svg>
            </div>
         </div>
      <div class="content-sub">
         <div class="div-above-nav-bar" id="buttons-div${tabCounter}">
               <div class="nav-model-left">
                  <div class="split-nav">
                     <div class="top-half-nav">
                        <div class="obj-func">       
                           <div class="dropdown" id="dd-obj${tabCounter}">
                              <div class="select">
                              <span>Select KPI</span>
                              <i class="fa fa-chevron-left"></i>
                           </div>
                           <input type="hidden" name="objective" id="obj-input${tabCounter}">
                           <ul class="dropdown-menu">
                              <li id="profit">Profit</li>
                              <li id="revenue">Revenue</li>
                              <li id="roi">ROI</li>
                           </ul>
                        </div>
                     </div>
                     <div class="blend">       
                     <div class="dropdown" id="dd-blend${tabCounter}">
                        <div class="select">
                           <span>Objective Function</span>
                           <i class="fa fa-chevron-left"></i>
                        </div>
                        <input type="hidden" name="blend" id="blend-input${tabCounter}">
                        <ul class="dropdown-menu">
                           <li id="blend">Blended</li>
                           <li id="st">ST</li>
                           <li id="lt">LT</li>
                        </ul>
                     </div>
                  </div>
                  <div class="exh-bud">       
                     <div class="dropdown" id="dd-exh${tabCounter}">
                        <div class="select">
                           <span>Budget Exhaustion</span>
                           <i class="fa fa-chevron-left"></i>
                        </div>
                        <input type="hidden" name="exhaust-budget" id="exh-input${tabCounter}">
                        <ul class="dropdown-menu">
                           <li id="yes">Exhaust Budget</li>
                           <li id="no">Do Not Exhaust Budget</li>
                        </ul>
                     </div>
                  </div>
               </div>
               <div class="bottom-half-nav">
                  <input type="number" id="max-input${tabCounter}" step="5000" placeholder="Enter Max Budget">
                  
               </div>
            </div>
            <div class="date-cont" id="date-cont">
               <div class="date-range-label">
                  <label for="end-date">Date Range Filter:</label>
                  <div class="toggle-button-cover">
                     <div class="button-cover">
                        <div class="button d">
                           <input type="checkbox" class="checkbox" id="date-filter-button${tabCounter}" />
                           <div class="knobs"></div>
                           <div class="layer"></div>
                           </div>
                        </div>
                     </div>
                  </div>
                  <div class="date-inputs${tabCounter} greyed-out">
                     <input type="date" name="start-date" id="start-date${tabCounter}" class="start-date" placeholder="Start date" />
                     <input type="date" name="end-date" class="end-date" id="end-date${tabCounter}" placeholder="End date" />
                  </div>
                  </div>
                  <div class="opt-cont-parent" id="opt-button-cont">
                     <button class="button-4" role="button" id="opt-button${tabCounter}">Optimise</button>
                  </div>
               </div>
            </div>
            <div class="bo-container" id="channel-container${tabCounter}">
            <table id="channel${tabCounter}" class="hover">
               <thead>
                  <tr>
                     <th><input type="checkbox" name="select_all" value="1" id="example-select-all${tabCounter}" ></th>
                     <th>Region</th>
                     <th>Brand</th>
                     <th>Channel</th>
                     <th>Current Budget</th>
                     <th>Min Spend Cap</th>
                     <th>Max Spend Cap</th>
                     <th>Laydown</th>
                     </tr>
                  </thead>
               </table>
            </div>
         </div>
      </div>
   </div>
`;

      var mainCont = document.getElementById("main-container");
      mainCont.appendChild(tabContent);
      initializeCollapsibleButtons(tabCounter);
      initializeDataTable(tabCounter);
      //initializeButtons(tabCounter);
      closeButtonTab(tabCounter);
      dropdownButtons(tabCounter);
      $(".sparkline").each(function () {
        var $sparkline = $(this);
        var sparklineData = $sparkline.text();
        $sparkline.empty().sparkline(sparklineData, {
          type: "line",
          width: "250px",
        });
      });
      // redrawAllTables(tabCounter);
      var buttonName = document.getElementById("button-text" + tabCounter);
      tabNames[tabCounter] = buttonName.textContent;
      console.log(tabNames);
    }

function syncTabCounter() {
  $.ajax({
    url: "/sync_tab_counter",
    type: "GET",
    contentType: "application/json",
    success: function (response) {
      if (response && response.lastNumber) {
        var lastNumber = response.lastNumber;
        tabCounter = lastNumber;
        console.log("tabCounter being set to: ", lastNumber);
      }
    },
    error: function (error) {
      console.error("error fetching last number", error);
    },
  });
}

function initializeInitialButton() {
  var content = document.getElementById("opt-tab1");
  var coll = document.getElementById("col-btn1");
  var table = document.getElementById("channel-container1");
  var buttonsDiv = document.getElementById("buttons-div1");
  coll.addEventListener("click", function () {
    this.classList.toggle("active");
    console.log("col-btn" + tabCounter);
    switch (table.style.maxHeight) {
      case "100%":
        table.style.maxHeight = "0%";
        table.style.opacity = 0;
        content.style.maxHeight = buttonsDiv.scrollHeight + "px";
        break;
      case "0%":
        table.style.maxHeight = "100%";
        table.style.opacity = 1;
        content.style.maxHeight = "100%";
        break;
    }
  });
  table.style.maxHeight = "0%";
  table.style.opacity = 0;
  content.style.maxHeight = buttonsDiv.scrollHeight + "px";
}

function initializeCollapsibleButtons(colID) {
  var content = document.getElementById("opt-tab" + colID);
  var coll = document.getElementById("col-btn" + colID);
  var table = document.getElementById("channel-container" + colID);
  var buttonsDiv = document.getElementById("buttons-div" + colID);
  console.log("col-btn" + tabCounter);
  coll.addEventListener("click", function () {
    this.classList.toggle("active");
    console.log("col-btn" + tabCounter);
    switch (table.style.maxHeight) {
      case "100%":
        table.style.maxHeight = "0%";
        table.style.opacity = 0;
        content.style.maxHeight = buttonsDiv.scrollHeight + "px";
        break;
      case "0%":
        table.style.maxHeight = "100%";
        table.style.opacity = 1;
        content.style.maxHeight = "100%";
        break;
    }
  });
  table.style.maxHeight = "0%";
  table.style.opacity = 0;
  content.style.maxHeight = buttonsDiv.scrollHeight + "px";
}

function closeButtonTab(tabID) {
  var closeButton = document.getElementById("close-button" + tabID);
  closeButton.addEventListener("click", function () {
    var tab = document.getElementById("new-tab" + tabID);
    $.ajax({
      url: "/channel_delete",
      type: "POST", // You might need to adjust the method based on your backend API
      contentType: "application/json",
      data: JSON.stringify({ tabID: tabID }),
      success: function (response) {
        console.log("Response from backend:", response);
        // Add any further handling based on the backend response
        sendTableIDsOnRefresh();
        syncTabNames();
      },
      error: function (error) {
        console.error("error deleting tab:", error);
        sendTableIDsOnRefresh();
        syncTabNames();
      },
    });
    tab.remove();
  });
}

function syncTabNames() {
  $.ajax({
    url: "/get_table_ids",
    method: "GET",
    contentType: "application/json",
    success: function (response) {
      if (response && response.tableIds) {
        var tableIds = response.tableIds;
        const idsToRemove = Object.keys(tabNames).filter(
          (key) => !tableIds.includes(key)
        );
        idsToRemove.forEach((key) => delete tabNames[key]);
        console.log("successfully removed:" + idsToRemove);
      }
    },
  });
}

// ANY EDITS MADE TO THIS FUNCTION, REMEMBER TO ALSO CHANGE THEM IN THE IDENTICAL FUNCTION IN SAVEUI.JS
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
function initializeInitialTable() {
  var channelTable = $("#channel1").DataTable({
    dom: "Blfrtip",
    destroy: true,
    ajax: {
      url: "/channel_main",
      contentType: "application/json",
      dataSrc: "1",
    },
    drawCallback: function () {
      $(".sparkline1")
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
          return '<input type="checkbox">';
        },
      },
      { className: "dt-head-center", targets: [0, 1, 2, 3, 4, 5, 6, 7] },
    ],
    rowId: "row_id",
    createdRow: function (row, data, dataIndex) {
      $(row).addClass("disabled");
    },
  });

  channelTable.rows().nodes().to$().addClass('disabled');
  
  $.ajax({
    url: "/date_range",
    type: "GET",
    dataType: "json",
    success: function (data) {
      console.log("fetching and applying dates");
      // Set the fetched dates as default values for date inputs

      var startDate = new Date(data.startDate).toISOString().split("T")[0];
      var endDate = new Date(data.endDate).toISOString().split("T")[0];

      $("#start-date1").val(startDate);
      $("#start-date1").prop("min", startDate);
      $("#start-date1").prop("max", endDate);
      $("#end-date1").val(endDate);
      $("#end-date1").prop("min", startDate);
      $("#end-date1").prop("max", endDate);
    },
    error: function (error) {
      console.error("Error fetching dates:", error);
    },
  });

  var channelEditor = new $.fn.dataTable.Editor({
    ajax: {
      type: "POST",
      url: "/table_data_editor",
      contentType: "application/json", // Set the content type to JSON
      data: function (d) {
        d.tableId = "1";
        return JSON.stringify(d); // Convert the data to JSON string
      },
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
    var isChecked = $(this).prop("checked");
    if (isChecked) {
      channelTable.row(row).nodes().to$().removeClass("disabled");
      console.log("removing class");
    } else {
      channelTable.row(row).nodes().to$().addClass("disabled");
      console.log("adding class");
    }
  });



  document.addEventListener("DOMContentLoaded", function () {
    var obj = document.getElementById("obj-input1");
    var exh = document.getElementById("exh-input1");
    var max = document.getElementById("max-input1");
    var optButton = document.getElementById("opt-button1");
    var blend = document.getElementById("blend-input1");


    optButton.addEventListener("click", function () {
      showLoadingOverlay(1);
      var objValue = obj.value;
      var exhValue = exh.value;
      var maxValue = max.value;
      var blendValue = blend.value;

      var disabledRowIds = getDisabledRowIds(1);
      var tabName = fetchTabName(1);
      console.log("tabName:" + tabName);
      var dataToSend = {
        objectiveValue: objValue,
        exhaustValue: exhValue,
        maxValue: maxValue,
        blendValue: blendValue,
        tableID: 1,

        disabledRows: disabledRowIds,
        tabName: tabName,
      };

      var dateButtonIsChecked = $("#date-filter-button1").prop("checked");
      var startDate = $("#start-date1").val();
      var endDate = $("#end-date1").val();
      var dateTuple = [startDate, endDate];
      if (dateButtonIsChecked) {
        dataToSend["dates"] = dateTuple;
      }
      console.log(dataToSend);
      
      if (disabledRowIds.length < 85) {
        $("#warningPopup").show();
        $("#continueWarning").click(function () {
          // Hide modal
          $("#warningPopup").hide();
          // Emit socket event
          socket.emit("optimise", { dataToSend: dataToSend });
        });

        // Event listener for close button
        $("#cancelWarning").click(function () {
          // Hide modal
          $("#warningPopup").hide();
          hideLoadingOverlay(1);
        });
      } else {
        socket.emit("optimise", { dataToSend: dataToSend });
      }
    });
  });

  $("#date-filter-button1").on("click", function () {
    var isChecked = $(this).prop("checked");
    var dateContainers = $(".date-inputs");

    if (!isChecked) {
      console.log("date button is unchecked");
      dateContainers.addClass("greyed-out");
    } else {
      console.log("date button is checked");
      dateContainers.removeClass("greyed-out");
    }
  });
}

initializeInitialTable();

function getDisabledRowIds(tableID) {
  var disabledRowIds = [];

  // Assuming DataTables is initialized on the table with the ID 'channel'+tableID
  var dataTable = $("#channel" + tableID).DataTable();

  // Use the DataTables API to get rows with the 'disabled' class
  dataTable
    .rows(".disabled")
    .data()
    .each(function (row) {
      var rowId = row.row_id; // Make sure 'row_id' is a valid property of your data
      disabledRowIds.push(rowId);
    });

  return disabledRowIds;
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

var data = {};

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

$(document).ready(function () {
  // Make an AJAX request to the Flask endpoint
  $.ajax({
    url: "/date_range",
    type: "GET",
    dataType: "json",
    success: function (data) {
      console.log("fetching and applying dates");
      // Set the fetched dates as default values for date inputs

      var startDate = new Date(data.startDate).toISOString().split("T")[0];
      var endDate = new Date(data.endDate).toISOString().split("T")[0];

      $("#start-date1").val(startDate);
      $("#start-date1").prop("min", startDate);
      $("#start-date1").prop("max", endDate);
      $("#end-date1").val(endDate);
      $("#end-date1").prop("min", startDate);
      $("#end-date1").prop("max", endDate);
    },
    error: function (error) {
      console.error("Error fetching dates:", error);
    },
  });
});

function openNewTab() {
  console.log("opening new tab");
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

function fetchTabName(setID) {
  var buttonText = document.getElementById("button-text" + setID);
  var tabName = buttonText.innerText;
  return tabName;
}

function optAll() {
  var optAllArray = [];
  var warningBool = false;
  $.ajax({
    url: "get_table_ids",
    method: "GET",
    contentType: "application/json",
    success: function (response) {
      if (response && response.tableIds) {
        console.log(response.tableIds);
        var tableIds = response.tableIds;
        tableIds.forEach(function (tableId) {
          showLoadingOverlay(tableId);
          var obj = document.getElementById("obj-input" + tableId);
          var exh = document.getElementById("exh-input" + tableId);
          var max = document.getElementById("max-input" + tableId);
          var blend = document.getElementById("blend-input" + tableId);


          var objValue = obj.value;
          var exhValue = exh.value;
          var maxValue = max.value;
          var blendValue = blend.value;

          var disabledRowIds = getDisabledRowIds(tableId);
          var tabName = fetchTabName(tableId);

          console.log("tab name is:");
          console.log(tabName);
          var dataToSend = {
            objectiveValue: objValue,
            exhaustValue: exhValue,
            maxValue: maxValue,
            blendValue: blendValue,
            tableID: tableId,

            disabledRows: disabledRowIds,
            tabName: tabName,
          };

          var dateButtonIsChecked = $(
            "#date-filter-button" + tableId
          ).prop("checked");
          var startDate = $("#start-date" + tableId).val();
          var endDate = $("#end-date" + tableId).val();
          var dateTuple = [startDate, endDate];
          if (dateButtonIsChecked) {
            dataToSend["dates"] = dateTuple;
          }

          optAllArray.push({ dataToSend: dataToSend });
          if (disabledRowIds.length < 85) {
            warningBool = true;
          }
        });
        if (warningBool == true) {

          $("#warningPopup").show();
          $("#continueWarning").click(function () {
       
            $("#warningPopup").hide();
      
            optAllArray.forEach(function(data) {
              socket.emit("optimise", data);
          });
        });
        $("#cancelWarning").click(function () {
                
          $("#warningPopup").hide();
          
          tableIds.forEach(function (tableId) {
            hideLoadingOverlay(tableId);
          });
        });
        } else {
        optAllArray.forEach(function(data) {
          socket.emit("optimise", data);
        });
      }
      }
    },
  });
}

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
      console.log("pinged create_copy");
      console.log("/channel" + tableID);

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
                '<input type="checkbox">'
              );
            },
          },
          { className: "dt-head-center", targets: [0, 1, 2, 3, 4, 5, 6, 7] },
        ],
        rowId: "row_id",
        createdRow: function (row, data, dataIndex) {
          $(row).addClass("disabled");
        },
      });

      var channelEditorTab = new $.fn.dataTable.Editor({
        ajax: {
          type: "POST",
          url: "/table_data_editor",
          contentType: "application/json", // Set the content type to JSON
          data: function (d) {
            d.tableId = tableID;
            return JSON.stringify(d); // Convert the data to JSON string
          },
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
      $("#example-select-all" + tableID).on("click", function () {
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
      $("#channel" + tableID + " tbody").on(
        "change",
        'input[type="checkbox"]',
        function () {
          // If checkbox is not checked
          if (!this.checked) {
            var el = $("#example-select-all" + tableID).get(0);
            // If "Select all" control is checked and has 'indeterminate' property
            if (el && el.checked && "indeterminate" in el) {
              // Set visual state of "Select all" control
              // as 'indeterminate'
              el.indeterminate = true;
            }
          }
        }
      );
      $("#frm-example" + tableID).on("submit", function (e) {
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

      $("#channel" + tableID + " tbody").on(
        "change",
        'input[type="checkbox"]',
        function () {
          var row = $(this).closest("tr");
          var rowId = tabChannelTable.row(row).id();
          var isChecked = $(this).prop("checked");
          if (isChecked) {
            tabChannelTable.row(row).nodes().to$().removeClass("disabled");
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

          var startDate = new Date(data.startDate).toISOString().split("T")[0];
          var endDate = new Date(data.endDate).toISOString().split("T")[0];

          $("#start-date" + tableID).val(startDate);
          $("#start-date" + tableID).prop("min", startDate);
          $("#start-date" + tableID).prop("max", endDate);
          $("#end-date" + tableID).val(endDate);
          $("#end-date" + tableID).prop("min", startDate);
          $("#end-date" + tableID).prop("max", endDate);
        },
        error: function (error) {
          console.error("Error fetching dates:", error);
        },
      });


      var obj = document.getElementById("obj-input" + tableID);
      var exh = document.getElementById("exh-input" + tableID);
      var max = document.getElementById("max-input" + tableID);
      var optButton = document.getElementById("opt-button" + tableID);
      var blend = document.getElementById("blend-input" + tableID);


      optButton.addEventListener("click", function () {
        showLoadingOverlay(tableID);
        var objValue = obj.value;
        var exhValue = exh.value;
        var maxValue = max.value;
        var blendValue = blend.value;

        var disabledRowIds = getDisabledRowIds(tableID);
        var tabName = fetchTabName(tableID);

        var dataToSend = {
          objectiveValue: objValue,
          exhaustValue: exhValue,
          maxValue: maxValue,
          blendValue: blendValue,
          tableID: tableID,

          disabledRows: disabledRowIds,
          tabName: tabName,
        };
        var dateButtonIsChecked = $("#date-filter-button" + tableID).prop(
          "checked"
        );
        var startDate = $("#start-date" + tableID).val();
        var endDate = $("#end-date" + tableID).val();
        var dateTuple = [startDate, endDate];
        if (dateButtonIsChecked) {
          dataToSend["dates"] = dateTuple;
        }
        console.log(dataToSend);

        // Use jQuery AJAX to send the data to the Flask endpoint
        if (disabledRowIds.length < 85) {
          $("#warningPopup").show();
          $("#continueWarning").click(function () {
            // Hide modal
            $("#warningPopup").hide();
            // Emit socket event
            socket.emit("optimise", { dataToSend: dataToSend });
          });
  
          // Event listener for close button
          $("#cancelWarning").click(function () {
            // Hide modal
            $("#warningPopup").hide();
            hideLoadingOverlay(tableID);
          });
        } else {
          socket.emit("optimise", { dataToSend: dataToSend });
        }
      });
    },
    error: function (error) {
      console.error("Error creating copy of data:", error);
    },
  });
  
  $("#date-filter-button" + tableID).on("click", function () {
    var isChecked = $(this).prop("checked");
    var dateContainers = $(".date-inputs" + tableID);

    if (!isChecked) {
      console.log("date button is unchecked");
      dateContainers.addClass("greyed-out");
    } else {
      console.log("date button is checked");
      dateContainers.removeClass("greyed-out");
    }
  });
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

function showLoadingOverlay(tableID) {
  document.getElementById("loading-overlay" + tableID).style.display = "block";
}

function hideLoadingOverlay(tableID) {
  document.getElementById("loading-overlay" + tableID).style.display = "none";
}

function destroyTables(tableID) {
  for (var i = 1; i < tableID; i++) {
    console.log(i);
    $("#channel" + i)
      .DataTable()
      .clear()
      .destroy();
    console.log("#channel" + i + " destroyed");
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

tabSocket.on("connect", function () {
  console.log("connected to server");
});

tabSocket.on("opt_complete", function (data) {
  var tableID = data.data;
  console.log("hiding the loading overlay for channel table " + tableID);
  hideLoadingOverlay(tableID);
  showResultsButton();
});

// SAVEUI BELOW

$(document).ready(function () {
  $("#load-list").click(function () {
    openLoadPopup();
  });
  $("#save-list").click(function () {
    openSavePopup();
  });
  $("#load-popup-close").click(function () {
    closeLoadPopup();
  });
  $("#loadButtonPopup").click(function () {
    loadFunc();
  });
  $("#save-popup-close").click(function () {
    closeSavePopup();
  });
  $("#saveButtonPopup").click(function () {
    saveFunc();
  });
  $("#overwriteSave").click(function () {
    overwriteSave();
  });

});

function editButton() {
  var setText = document.getElementById("button-text1");
  var newText = prompt("Rename Tab:");

  if (newText !== null) {
    setText.textContent = newText;
    tabNames[1] = newText;
  }
}

function editButtonTabs(tabID) {
  var setText = document.getElementById("button-text" + tabID);
  var newText = prompt("Rename Tab:");

  if (newText !== null) {
    setText.textContent = newText;
    tabNames[tabID] = newText;
    console.log(tabNames);
  }
  syncTabNames();
}

function openLoadPopup() {
  $("#loadPopup").show();
  initializeLoadTable();
}
var savesTable;
function closeLoadPopup() {
  $("#loadPopup").hide();
}
function openSavePopup() {
  $("#savePopup").show();
  initializeSavesTable();
}
function closeSavePopup() {
  $("#savePopup").hide();
}

var isSaveTableInitialized = false;
var isLoadTableInitialized = false;
var saveTable;
var loadTable;

function initializeLoadTable() {
  if ($.fn.DataTable.isDataTable("#load-table")) {
    console.log("load table already exists");
    loadTable.ajax.reload();
    return;
  }

  console.log("initializing snapshot load table");
  loadTable = $("#load-table").DataTable({
    dom: "Blfrtip",
    ajax: {
      url: "/get_saves",
      contentType: "application/json",
      dataSrc: "data",
    },
    columns: [{ data: "name" }, { data: "table_ids" }],
    select: "single",
    autoWidth: false,
    rowId: "DT_RowId",
  });
  isLoadTableInitialized = true;
}
function initializeSavesTable() {
  if ($.fn.DataTable.isDataTable("#saves-table")) {
    console.log("saves table already exists");
    saveTable.ajax.reload();
    return;
  }

  console.log("initializing saves table");
  saveTable = $("#saves-table").DataTable({
    dom: "Blfrtip",
    ajax: {
      url: "/get_saves",
      contentType: "application/json",
      dataSrc: "data",
    },
    columns: [{ data: "name" }, { data: "table_ids" }],
    select: "single",
    autoWidth: false,
    rowId: "DT_RowId",
  });
  saveTable.on("select", function () {
    $("#overwriteSave").show();
  });

  saveTable.on("deselect", function () {
    $("#overwriteSave").hide();
  });
  isSaveTableInitialized = true;
}

function reloadSaveTable() {
  if (saveTable && $.fn.DataTable.isDataTable("#save-table")) {
    console.log("save table reloading contents");
    saveTable.ajax.reload();
  } else {
    console.log("save table not initialized");
  }
}

function loadFunc() {
  var selectedRow = $("#load-table")
    .DataTable()
    .rows({ selected: true })
    .data()[0];

  if (selectedRow) {
    var selectedSaveId = selectedRow.DT_RowId;

    $.ajax({
      type: "POST",
      url: "/load_selected_row",
      contentType: "application/json",
      data: JSON.stringify({ selectedSaveId: selectedSaveId }),
      success: function (postResponse) {
        console.log("POST request successful", postResponse);
        console.log("commencing GET request");

        $.ajax({
          url: "/load_selected_row",
          method: "GET",
          contentType: "application/json",
          success: function (response) {
            if (
              response &&
              response.content &&
              response.scenario_names
            ) {
              var scenarioNamesString = response.scenario_names;
              var scenarioNamesArray = scenarioNamesString
                .replace(/[{}""]/g, "")
                .split(",");
              
             

              var arrayToLoad = response.content;

              console.log("printing the loaded array:", arrayToLoad);
              // call buildDatatable funciton here
              
            }
            sendTableIDsOnRefresh();
            syncTabCounter();
            closeLoadPopup();
          },
        });
      },
    });

    console.log("Selected Save ID:", selectedSaveId);
  } else {
    console.log("No row selected.");
  }
}

function enteredBudget(tableID) {
  const budgetInput = document.getElementById('max-input'+tableID);
  const budgetValue = budgetInput.value;
  return budgetValue;
}

function selectedDropDownOptions(tableID) {
  
  const selectedKPI = document.getElementById('obj-input'+tableID);
  const selectedBlendOption = document.getElementById('blend-input'+tableID);
  const selectedBudgetOption = document.getElementById('exh-input'+tableID);

  const kpiValue = selectedKPI.value;
  const selectedBlendValue = selectedBlendOption.value;
  const selectedBudgetValue = selectedBudgetOption.value;

  var optionsArray = [kpiValue,selectedBlendValue, selectedBudgetValue];

  return optionsArray;
}

function dateOptions(tableID) {
  var dateArray = [];
  var startDateElement = document.getElementById("start-date"+tableID);
  var endDateElement = document.getElementById("end-date"+tableID);
  var startDateValue = startDateElement.value;
  var endDateValue = endDateElement.value;
  var dateBool = null;
  var dateButtonIsChecked = $("#date-filter-button"+tableID).prop("checked");
  if (dateButtonIsChecked) {
    dateBool = true;
  } else {
    dateBool = false;
  }
  dateArray = [startDateValue, endDateValue];
  return [dateBool, dateArray];
}


function saveFunc() {
  console.log("save button clicked");

  var snapshotName = window.prompt("Please provide a name for this snapshot:");
  if (snapshotName !== null) {
    var objToSend = {};
    $.ajax({
      url: "get_table_ids",
      method: "GET",
      contentType: "application/json",
      success: function (response) {
        if (response && response.tableIds) {
          console.log(response.tableIds);
          var tableIds = response.tableIds;

    
          closeSavePopup();

          // contentToSave captures the html of every tab, every table.
          // var contentToSave = document.getElementById("all-content").innerHTML;
          // I need to make it scan each table.

            tableIds.forEach(function(tableID) {
              var disabledRowIds = getDisabledRowIds(tableID);
              var budget = enteredBudget(tableID);
              var [dateBool, dateArray] = dateOptions(tableID);
              var options = selectedDropDownOptions(tableID);
              var savedDataFromTable = {
                disabledRowIds: disabledRowIds,
                enteredBudget: budget,
                dateBool: dateBool,
                dateArray: dateArray,
                optionsArray: options
              }
              objToSend[tableID] = savedDataFromTable;
            });
           
          }
             
          console.log("current tabNames are:");
          console.log(tabNames);
          $.ajax({
            url: "/save_snapshot",
            method: "POST",
            contentType: "application/json",
            data: JSON.stringify({
              content: objToSend,
              name: snapshotName,
              scenarioNames: Object.values(tabNames),
            }),
            success: function (response) {
              console.log(response);
              
            },
            error: function (error) {
              console.error("Error saving snapshot:", error);
            },
          });
        
      },
    });
  }
}

function overwriteSave() {
  if (isSaveTableInitialized) {
    var selectedRow = saveTable.row({ selected: true }).data();
    if (selectedRow) {
      var selectedSaveId = selectedRow.DT_RowId;
      // Send a POST request to the Flask backend with the selected row data
      $.ajax({
        url: "get_table_ids",
        method: "GET",
        contentType: "application/json",
        success: function (response) {
          if (response && response.tableIds) {
            console.log(response.tableIds);
            var tableIds = response.tableIds;

            destroyTables(tableIds.length + 1);
            $("#saves-table").DataTable().destroy();
            $("#load-table").DataTable().destroy();
            console.log("saves and load tables destroyed");
            isSaveTableInitialized = false;
            isLoadTableInitialized = false;
            closeSavePopup();
            var contentToSave =
              document.getElementById("all-content").innerHTML;
            $.ajax({
              url: "/overwrite_save",
              method: "POST",
              contentType: "application/json",
              data: JSON.stringify({
                selectedSaveId: selectedSaveId,
                content: contentToSave,
                scenarioNames: Object.values(tabNames),
              }),
              success: function (response) {
                console.log(response);
                initializeInitialTable();
                tableIds.forEach(function (id) {
                  initializeDataTable(id);
                });
                initializeSavesTable();
                initializeLoadTable();
                console.log("reinitialized all tables");
                console.log("Save overwritten successfully:", response);
                // Handle any further actions based on the backend response
              },
              error: function (error) {
                console.error("Error overwriting save:", error);
              },
            });
          }
        },
      });
    }
  }
}

function buildDatatableFromLoad (data) {
  const {disabledRowIds, enteredBudget, dateBool, dateArray, optionsArray} = data;

}