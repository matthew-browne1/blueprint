$(document).ready(function () {
  
  $("#load-list").click(function () {
    openLoadPopup();
  });
  $("#save-list").click(function () {
    openSavePopup();
  }); 

});

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
    columns: [
      { data: "name" },
      { data: "table_ids" }
    ],
    select: 'single',
    autoWidth: false,
    rowId: 'DT_RowId'
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
    columns: [
      { data: "name" },
      { data: "table_ids" }
    ],
    select: 'single',
    autoWidth: false,
    rowId: 'DT_RowId'
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
    select: {
      style: "os",
      selector: "td:not(:nth-child(5)):not(:nth-child(6))",
    },
    autoWidth: false,
    columnDefs: [
      { width: "80px", targets: 0 },
      { width: "80px", targets: 1 },
      { width: "80px", targets: 2 },
      { width: "80px", targets: 3 },
      { width: "80px", targets: 4 },
      { width: "80px", targets: 5 },
      { width: "250px", targets: 6 },
    ],
    rowId: "row_id",
  });
  //attachButtonListenersToDataTable();
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
    "tbody td:nth-child(5), tbody td:nth-child(6)",
    function (e) {
      $(this).css({
        cursor: "text",
        userSelect: "none",
      });
    }
  );

  channelTable.on(
    "mouseleave",
    "tbody td:nth-child(5), tbody td:nth-child(6)",
    function (e) {
      $(this).css({
        cursor: "default",
        userSelect: "auto",
      });
    }
  );

  channelTable.on(
    "click",
    "tbody td:nth-child(5), tbody td:nth-child(6)",
    function (e) {
      channelEditor.inline(this);
    }
  );
  channelTable.on("page.dt", function () {
    channelTable.ajax.reload(null, false);
  });
}

function loadFunc() {
  var selectedRow = $("#load-table").DataTable().rows({ selected: true }).data()[0];

  if (selectedRow) {
    var selectedSaveId = selectedRow.DT_RowId;

      $.ajax({
        type: "POST",
        url: "/load_selected_row",
        contentType: "application/json",
        data: JSON.stringify({ selectedSaveId: selectedSaveId}),
        success: function (postResponse) {
          console.log("POST request successful", postResponse);
          console.log("commencing GET request");

          $.ajax({
            url: "/load_selected_row",
            method: "GET",
            contentType: "application/json",
            success: function (response) {
              if (response && response.content && response.table_ids) {
                var tableIdsString = response.table_ids;

                var tableIdsArray = tableIdsString
                  .split(",")
                  .map(function (id) {
                    return parseInt(id.trim(), 10);
                  });

                var startingFromSecondElement = tableIdsArray.slice(1);

                var contentToLoad = response.content;
                document.getElementById("all-content").innerHTML =
                  contentToLoad;

                initializeInitialButton();
                initializeInitialTable();
                dropdownButtons(1);
                //initializeButtons(1);
                newTabButtonInit();
                console.log("attempting to reinitialize load and save table");
               
                initializeLoadTable();
                initializeSavesTable();
                
                startingFromSecondElement.forEach(function (id) {
                  dropdownButtons(id);
                  initializeDataTable(id);
                  // attachButtonListenersToDataTable(id);
                  // redrawAllSparklines(id);
                  initializeCollapsibleButtons(id);
                  //initializeButtons(id);
                  closeButtonTab(id);
                });
              }
              sendTableIDsOnRefresh();
              syncTabCounter();
              closeLoadPopup();
              
            },
          });
        }
      })
    

    console.log("Selected Save ID:", selectedSaveId);
  } else {
    console.log("No row selected.");
  }
}
function saveFunc() {
  console.log("save button clicked");

  var snapshotName = window.prompt("Please provide a name for this snapshot:");
  if (snapshotName !== null) {
    $.ajax({
      url: "get_table_ids",
      method: "GET",
      contentType: "application/json",
      success: function (response) {
        if (response && response.tableIds) {
          console.log(response.tableIds);
          var tableIds = response.tableIds;

          destroyTables(tableIds.length + 1);

          if (isSaveTableInitialized) {
            saveTable.destroy();
            isSaveTableInitialized = false;
            console.log("destroyed save table");
          }
          if (isLoadTableInitialized) {
            loadTable.destroy();
            isLoadTableInitialized = false;
            console.log("destroyed load table");
          }
          
          closeSavePopup();
          var contentToSave = document.getElementById("all-content").innerHTML;

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
              tableIds.forEach(function (id) {
                initializeDataTable(id);
              });
              initializeSavesTable();
              initializeLoadTable();
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
}
function overwriteSave() {
  if(isSaveTableInitialized) {
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
              
              destroyTables(tableIds.length+1);
              $('#saves-table').DataTable().destroy();
              $('#load-table').DataTable().destroy();
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
                  content: contentToSave
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
          }
        });
      }
  }
}