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
              if (response && response.content && response.table_ids && response.scenario_names) {
                var tableIdsString = response.table_ids;
                var scenarioNamesString = response.scenario_names;
                var scenarioNamesArray = scenarioNamesString.replace(/[{}""]/g,'').split(',');
                var tableIdsArray = tableIdsString
                  .split(",")
                  .map(function (id) {
                    return parseInt(id.trim(), 10);
                  });
                const dictionary = tableIdsArray.reduce((acc, key, index) => {
                  acc[key] = scenarioNamesArray[index];
                  return acc;
                  }, {});
                tabNames = dictionary;
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
          console.log("current tabNames are:");
          console.log(tabNames);
          $.ajax({
            url: "/save_snapshot",
            method: "POST",
            contentType: "application/json",
            data: JSON.stringify({
              content: contentToSave,
              name: snapshotName,
              scenarioNames: Object.values(tabNames)
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
                  content: contentToSave,
                  scenarioNames: Object.values(tabNames)
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