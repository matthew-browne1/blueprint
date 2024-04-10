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
          return (
            '<input type="checkbox" name="id[]" checked value="' +
            $("<div/>").text(data).html() +
            '">'
          );
        },
      },
      { className: "dt-head-center", targets: [0, 1, 2, 3, 4, 5, 6, 7] },
    ],
    rowId: "row_id",
  });
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


    var obj = document.getElementById("obj-input1");
    var exh = document.getElementById("exh-input1");
    var max = document.getElementById("max-input1");
    var optButton = document.getElementById("opt-button1");
    var blend = document.getElementById("blend-input1");
    var ftol = document.getElementById("ftol-input1");
    var ssize = document.getElementById("step-size-input1");

    optButton.addEventListener("click", function () {
      showLoadingOverlay(1);
      var objValue = obj.value;
      var exhValue = exh.value;
      var maxValue = max.value;
      var blendValue = blend.value;
      var ftolValue = ftol.value;
      var ssizeValue = ssize.value;
      var disabledRowIds = getDisabledRowIds();
      var tabName = fetchTabName(1);
      console.log("tabName:" + tabName);
      var dataToSend = {
        objectiveValue: objValue,
        exhaustValue: exhValue,
        maxValue: maxValue,
        blendValue: blendValue,
        tableID: 1,
        ftolValue: ftolValue,
        ssizeValue: ssizeValue,
        disabledRows: disabledRowIds,
        tabName: tabName,
      };

      var dateButtonIsChecked = $("#date-filter-button1").prop("checked");
      var startDate = $("#start-date1").val();
      var endDate = $("#end-date1").val();
      var dateTuple = [startDate, endDate];
      if (!dateButtonIsChecked) {
        dataToSend["dates"] = dateTuple;
      }
      console.log(dataToSend);
      socket.emit("optimise", { dataToSend: dataToSend });

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

var socket = io.connect(window.location.origin);

socket.on("connect", function () {
  console.log("connected to server");
});
