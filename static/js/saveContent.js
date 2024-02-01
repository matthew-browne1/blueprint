var allDiv = document.getElementById("all-content");

var saveButton = document.getElementById("content-save-button");
var loadButton = document.getElementById("content-load-button");

saveButton.addEventListener("click", function () {
  console.log("save button clicked");

  var snapshotName = window.prompt("Please provide a name for this snapshot:");
  if (snapshotName !== null) {
          $.ajax({
            url: "load_snapshot",
            method: "GET",
            contentType: "application/json",
            success: function (response) {
              if (response && response.table_ids) {
                var tableIdsString = response.table_ids;

                var tableIdsArray = tableIdsString
                  .split(",")
                  .map(function (id) {
                    return parseInt(id.trim(), 10);
                  });

                var startingFromSecondElement = tableIdsArray.slice(1);

                destroyTables(startingFromSecondElement.length+1);

                var contentToSave =
                  document.getElementById("all-content").innerHTML;
                  
                  $.ajax({
                    url: "/save_snapshot",
                    method: "POST",
                    contentType: "application/json",
                    data: JSON.stringify({
                      content: contentToSave,
                      name: snapshotName,
                    }),
                    success: function (response) {
                      console.log(response);
                      initializeInitialTable();
                      startingFromSecondElement.forEach( function (id) {
                        initializeDataTable(id);
                      });
                      console.log("reinitialized all tables");
                    },
                    error: function (error) {
                      console.error("Error saving snapshot:", error);
                    },
                  });
              }
            },
          });
    } 
});

function initializeInitialTable() {
  var channelTable = $("#channel1").DataTable({
    dom: "Blfrtip",
    ajax: {
      url: "/channel_main",
      contentType: "application/json",
      dataSrc: "1",
    },
    drawCallback: function () {
      $(".sparkline").sparkline("html", {
        type: "line",
        width: "250px",
      });
    },
    columns: [
      { data: "Channel" },
      { data: "Carryover" },
      { data: "Alpha" },
      { data: "Beta", render: $.fn.DataTable.render.number(",", ".", 0, "") },
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
          return type === "display"
            ? '<span class="sparkline">' + data.toString() + "</span>"
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
  });
  attachButtonListenersToDataTable();
  var channelEditor = new $.fn.dataTable.Editor({
    ajax: "/channel_editor",
    table: "#channel1",
    fields: [
      {
        label: "Min Spend Cap:",
        name: "Min_Spend_Cap",
      },
      {
        label: "Max Spend Cap:",
        name: "Max_Spend_Cap",
      },
    ],
    idSrc: "DT_RowId",
  });

  channelTable.on(
    "click",
    "tbody td:nth-child(6), tbody td:nth-child(7)",
    function (e) {
      channelEditor.inline(this);
    }
  );

  channelTable.on("page.dt", function () {
    channelTable.ajax.reload(null, false);
  });
}
$(document).on("click", "#content-load-button", function () {
  
    // Other code to load content from localStorage
    $.ajax({
      url: "load_snapshot",
      method: "GET",
      contentType: "application/json",
      success: function (response) {
        
        if (response && response.content && response.table_ids) {
          var tableIdsString = response.table_ids;
          
          var tableIdsArray = tableIdsString.split(",").map(function (id) {
            return parseInt(id.trim(), 10);
          });

          var startingFromSecondElement = tableIdsArray.slice(1);
          
          var contentToLoad = response.content;
          document.getElementById("all-content").innerHTML = contentToLoad;
          
          initializeInitialButton();
          initializeInitialTable();         
          dropdownButtons(1);
          initializeButtons(1);
          newTabButtonInit();
          startingFromSecondElement.forEach(function (id) {
            dropdownButtons(id);
            initializeDataTable(id);
            // attachButtonListenersToDataTable(id);
            // redrawAllSparklines(id);
            initializeCollapsibleButtons(id);
            initializeButtons(id);
            closeButtonTab(id);
          });
        }
        sendTableIDsOnRefresh();
        syncTabCounter();
      }
    });
    
});

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