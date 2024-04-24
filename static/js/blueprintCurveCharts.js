let response_curve_chart = null;
let budget_response_chart = null;
let budget_curve_chart = null;
let roi_curve_chart = null;
let tv_curve_chart = null;

var chartsSocket = io.connect(window.location.origin,
     { timeout: 500000
}
);

chartsSocket.on('connect', function() {
    console.log('Connected');
     });
$(document).ready(function(){
    var filtered_chartResponse = [];
    var chartResponse = [];
    var filtered_chartBudget = [];
    var chartBudget = [];
    var filtered_chartROI = [];
    var chartROI = [];
    var filtered_chartBudget_response = [];
    var chartBudget_response = [];
    var tv_chartData = [];

   // Function to populate dropdown options
function populateDropdown(selector, options) {
    var dropdown = $(selector);
    dropdown.empty();
    $.each(options, function(key, value) {
        var option = $('<option></option>').attr('value', value).text(value);
        dropdown.append(option);
    });
}
      // Function to collect and send filter selections to backend
    function applyFilters() {
        var filters = {
            Region: $('#regionFilter').val(),
            Brand: $('#brandFilter').val(),
            "Optimisation Type": $('#optimisationFilter').val()
        };
        console.log("Applying filters:", filters);
        chartsSocket.emit("apply_filter_curve", filters);
    }

        // Listen for 'dropdown_options' event and populate dropdowns
    chartsSocket.on('dropdown_options1', function(data) {
        populateDropdown('#regionFilter', data.options.Region);
        populateDropdown('#brandFilter', data.options.Brand);
        populateDropdown('#optimisationFilter', data.options['Optimisation Type']);
    }).on('error', function(xhr, status, error) {
        console.error('Error fetching filter data:', error);
    });

       // Apply Filters button click event
    $('#applyFilters').on('click', function() {
        applyFilters();
    });

chartsSocket.emit("response_data");
chartsSocket.emit("apply_curve_filter");

chartsSocket.on('chart_response', function(data) {
  chartResponse = data.chartResponse;

  console.log("fetched response data from back end");
  generateCurveChartsA();
  setDefaultSelections(chartResponse);
});

function setDefaultSelections(chartResponse) {
        if (chartResponse.length > 0) {
            var defaultSelections = {
                Region: chartResponse[0].Region,
                Brand: chartResponse[0].Brand,
                "Optimisation Type": chartResponse[0]['Optimisation Type']
            };

            // Set default selections in dropdowns
            $('#regionFilter').val(defaultSelections.Region);
            $('#brandFilter').val(defaultSelections.Brand);
            $('#optimisationFilter').val(defaultSelections['Optimisation Type']);
        }
    }

chartsSocket.on('filtered_data_response', function(data) {
  filtered_chartResponse = data.filtered_data;

  console.log("fetched filtered response data from back end");
  generateCurveChartsA();
});

function generateCurveChartsA() {
    var title = "Curve Charts for ";
    var dataToUse = [];

    if (filtered_chartResponse.length > 0) {
        dataToUse = filtered_chartResponse;
    } else {
        dataToUse = chartResponse;
    }

    if (dataToUse.length > 0) {
        title += "Country - " + dataToUse[0].Region + ", Brand - " + dataToUse[0].Brand + ", Optimisation Type - " + dataToUse[0]['Optimisation Type'];
    } else {
        title += "No Data Available";
    }

    $('#dynamic-title').text(title);

    if (dataToUse.length > 0) {
        generateChartsA(dataToUse);
    }
}

chartsSocket.emit("budget_data");
chartsSocket.on('chart_budget', function(data) {
  chartBudget = data.chartBudget;

  console.log("fetched budget data from back end");
  generateCurveChartsB();
});

chartsSocket.on('filtered_data_budget', function(data) {
  filtered_chartBudget = data.filtered_data;

  console.log("fetched filtered budget data from back end");
  generateCurveChartsB();
});

function generateCurveChartsB() {
        if (filtered_chartBudget.length > 0) {
            generateChartsB(filtered_chartBudget);
        } else {
            generateChartsB(chartBudget);
        }
    }

chartsSocket.emit("roi_data");
chartsSocket.on('chart_roi', function(data) {
  chartROI = data.chartROI;

  console.log("fetched ROI data from back end");
  generateCurveChartsC();
});

chartsSocket.on('filtered_data_roi', function(data) {
  filtered_chartROI = data.filtered_data;

  console.log("fetched filtered ROI data from back end");
  generateCurveChartsC();
});

function generateCurveChartsC() {
        if (filtered_chartROI.length > 0) {
            generateChartsC(filtered_chartROI);
        } else {
            generateChartsC(chartROI);
        }
    }

chartsSocket.emit("budget_response_data");
chartsSocket.on('chart_budget_response', function(data) {
  chartBudget_response = data.chartBudget_response;

  console.log("fetched budget response data from back end");
  generateCurveChartsD();
});

chartsSocket.on('filtered_data_budget_response', function(data) {
  filtered_chartBudget_response = data.filtered_data;

  console.log("fetched filtered budget response data from back end");
  generateCurveChartsD();
});

function generateCurveChartsD() {
        if (filtered_chartBudget_response.length > 0) {
            generateChartsD(filtered_chartBudget_response);
        } else {
            generateChartsD(chartBudget_response);
        }
    }

chartsSocket.emit("tv_data");
chartsSocket.on("tv_chart_data", function(data) {
    tv_chartData = data.tv_chartData
    generateCurveChartsE();
})

function generateCurveChartsE() {
    generateChartsE(tv_chartData);
}


});

function generateChartsA(data) {
    console.log("reaching generateChartsA method");

 // 1. Response Curve by Channel Group Chart
    // Prepare data for the chart
    const response_chartData = {};
    data.forEach(entry => {
        const channelGroup = entry["Channel Group"];
        if (!response_chartData[channelGroup]) {
            response_chartData[channelGroup] = [];
        }
        // Limiting to the first 40 points
        if (response_chartData[channelGroup].length < 40) {
            response_chartData[channelGroup].push({ x: entry.Budget, y: entry["Predicted Revenue"] });
        }
    });

// 1a. data block
    const response_curve_chartData = {
        datasets: Object.keys(response_chartData).map(channelGroup => {
        return {
            label: channelGroup,
            data: response_chartData[channelGroup],
            borderColor: '#' + (Math.random().toString(16) + '000000').substring(2, 8), // Random color for each line
            fill: false,
            radius: 0,
        };
    })
};
// 1b. config block
    const response_curve_chartOptions = {
      scales: {
        x: {
          type: "linear",
          position: "bottom",
          scaleLabel: {
            display: true,
            labelString: "Budget",
          },
        },
        y: {
          scaleLabel: {
            display: true,
            labelString: "Response Curve",
          },
        },
      },
      responsive: true,
      maintainAspectRatio: true,
      animation: true
    };
// 1c. render block
   if (response_curve_chart === null) {
        response_curve_chart = new Chart(document.getElementById("response_curve_chart"), {
            type: 'line',
            data: response_curve_chartData,
            options: response_curve_chartOptions,
        });
    } else {
        response_curve_chart.data = response_curve_chartData;
        response_curve_chart.options = response_curve_chartOptions;
        response_curve_chart.update();
    }
}
function generateChartsB(data) {
    console.log("reaching generateChartsB method");
    // 3. Budget Curve Chart
     // 3a. data block
    const budget_chartData = {
        labels: [],
        datasets: [
            {
                label: 'Revenue',
                data: [],
                backgroundColor: 'rgba(54, 162, 235, 0.2)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1,
                pointRadius: [],
                pointBackgroundColor: [],
                pointBorderColor: 'rgba(54, 162, 235, 1)',
                pointBorderWidth: 2
            },
            {
                label: 'Historical Budget (not optimized)',
                data: [],
                backgroundColor: 'rgba(255, 99, 132, 0.7)',
                borderColor: 'rgba(255, 99, 132, 1)',
                pointStyle: 'circle',
                borderWidth: 1
            },
            {
                label: 'Historical Budget (optimized)',
                data: [],
                backgroundColor: 'rgba(75, 192, 192, 0.7)',
                borderColor: 'rgba(75, 192, 192, 1)',
                pointStyle: 'circle',
                borderWidth: 1
            },
            {
                label: 'Profit',
                data: [],
                backgroundColor: 'rgba(255, 206, 86, 0.2)',
                borderColor: 'rgba(255, 206, 86, 1)',
                borderWidth: 1,
                pointRadius: [],
                pointBackgroundColor: [],
                pointBorderColor: 'rgba(255, 206, 86, 1)',
                pointBorderWidth: 2
            },
            {
                label: 'Profit Max',
                data: [],
                backgroundColor: 'rgba(0, 39, 129, 0.2)',
                borderColor: 'rgba(0, 39, 129, 1)',
                borderWidth: 1,
            }
        ]
    };

    data.forEach(entry => {
        budget_chartData.labels.push(entry.Budget);
        budget_chartData.datasets[0].data.push(entry.Revenue);
        budget_chartData.datasets[1].data.push(entry["Historical Profit (not optimised)"]);
        budget_chartData.datasets[2].data.push(entry["Historical Profit (optimised)"]);
        budget_chartData.datasets[3].data.push(entry.Profit);
        budget_chartData.datasets[4].data.push(entry["Profit Max"]);
    });

    // 3b. config block
    const budget_chartOptions = {
      scales: {
        x: {
          type: "linear",
          position: "bottom",
          scaleLabel: {
            display: true,
            labelString: "Budget",
          },
        },
        y: {
          scaleLabel: {
            display: true,
            labelString: "Profit",
          },
        },
      },
      responsive: true,
      maintainAspectRatio: true,
      animation: true,
    };

    // 3c. render block
 if (budget_curve_chart === null) {
        budget_curve_chart = new Chart(document.getElementById("budget_curve_chart"), {
            type: 'line',
            data: budget_chartData,
            options: budget_chartOptions,
        });
    } else {
        budget_curve_chart.data = budget_chartData;
        budget_curve_chart.options = budget_chartOptions;
        budget_curve_chart.update();
    }
}
function generateChartsC(data) {
    console.log("reaching generateChartsC method");
    // 4. ROI Curve Chart
 // 4a. data block
     const roi_chartData = {
       labels: [], // Budget values will be used as labels on the x-axis
       datasets: [
         {
           label: 'ROI',
           data: [], // Profit values will be used as data points on the y-axis
           backgroundColor: 'rgba(54, 162, 235, 0.2)', // Background color of the line
           borderColor: 'rgba(54, 162, 235, 1)', // Border color of the line
           borderWidth: 1, // Border width of the line
           pointRadius: [], // Radius of the data points
           pointBackgroundColor: [], // Background color of the data points
           pointBorderColor: 'rgba(54, 162, 235, 1)', // Border color of the data points
           pointBorderWidth: 2 // Border width of the data points
         },
         {
           label: 'Break Even: £1',
           data: [], // Historical budget values (not optimized)
           backgroundColor: 'rgba(255, 99, 132, 0.7)', // Background color of the scatter plot
           borderColor: 'rgba(255, 99, 132, 1)', // Border color of the scatter plot
           pointStyle: 'circle', // Style of the data points (circle)
           borderWidth: 1 // Border width of the scatter plot
         },
         {
           label: 'Break Even: £4',
           data: [], // Historical budget values (optimized)
           backgroundColor: 'rgba(75, 192, 192, 0.7)', // Background color of the scatter plot
           borderColor: 'rgba(75, 192, 192, 1)', // Border color of the scatter plot
           pointStyle: 'circle', // Style of the data points (circle)
           borderWidth: 1 // Border width of the scatter plot
         },
         {
            label: 'Break Even: £8',
            data: [], // Profit values will be used as data points on the y-axis
            backgroundColor: 'rgba(255, 206, 86, 0.2)', // Background color of the line
            borderColor: 'rgba(255, 206, 86, 1)', // Border color of the line
            borderWidth: 1, // Border width of the line
        },
       ]
     };
    data.forEach(entry => {
        roi_chartData.labels.push(entry.Budget);
        roi_chartData.datasets[0].data.push(entry.ROI);
        roi_chartData.datasets[1].data.push(entry["Break Even: £1"]);
        roi_chartData.datasets[2].data.push(entry["Break Even: £4"]);
        roi_chartData.datasets[3].data.push(entry["Break Even: £8"]);
});
// 4b. config block
        const roi_chartOptions = {
          scales: {
            x: {
              type: "linear",
              position: "bottom",
              scaleLabel: {
                display: true,
                labelString: "Budget",
              },
            },
            y: {
              scaleLabel: {
                display: true,
                labelString: "ST + LT ROI",
              },
            },
          },
          responsive: true,
          maintainAspectRatio: true,
          animation: true,
        };
// 4c. render block
    if (roi_curve_chart === null) {
        roi_curve_chart = new Chart(document.getElementById("roi_curve_chart"), {
            type: 'line',
            data: roi_chartData,
            options: roi_chartOptions,
        });
    } else {
        roi_curve_chart.data = roi_chartData;
        roi_curve_chart.options = roi_chartOptions;
        roi_curve_chart.update();
    }
   }
function generateChartsD(data) {
    console.log("reaching generateChartsD method");
    // 2. Budget Response Curve Chart
    // Sort data
    const sortedData = data.sort((a, b) => a.Budget - b.Budget);

    // 2a. data block
    const budget_response_chartData = {
        labels: [],
        datasets: [
            {
                label: 'Optimised Revenue',
                data: [],
                backgroundColor: 'rgba(54, 162, 235, 0.2)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1,
                pointRadius: [],
                pointBackgroundColor: [],
                pointBorderColor: 'rgba(54, 162, 235, 1)',
                pointBorderWidth: 2
            },
            {
                label: 'Predicted Revenue',
                data: [],
                backgroundColor: 'rgba(255, 99, 71, 0.2)',
                borderColor: 'rgba(255, 99, 71, 1)',
                borderWidth: 1,
                pointRadius: [],
                pointBackgroundColor: [],
                pointBorderColor: 'rgba(54, 162, 235, 1)',
                pointBorderWidth: 2
            },
        ]
    };
    sortedData.forEach(entry => {
        budget_response_chartData.labels.push(entry.Budget);
        budget_response_chartData.datasets[0].data.push(entry["Total Revenue"]);
        budget_response_chartData.datasets[1].data.push(entry["Predicted Revenue"]);
    });

    // 2b. config block
    const budget_response_chartOptions = {
      scales: {
        x: {
          type: "linear",
          position: "bottom",
          scaleLabel: {
            display: true,
            labelString: "Budget",
          },
        },
        y: {
          scaleLabel: {
            display: true,
            labelString: "Revenue",
          },
        },
      },
      responsive: true,
      maintainAspectRatio: true,
      animation: true,
    };

    // 2c. render block
    if (budget_response_chart === null) {
        budget_response_chart = new Chart(document.getElementById("response_budget_chart"), {
            type: 'line',
            data: budget_response_chartData,
            options: budget_response_chartOptions,
        });
    } else {
        budget_response_chart.data = budget_response_chartData;
        budget_response_chart.options = budget_response_chartOptions;
        budget_response_chart.update();
    }
}

function generateChartsE(data) {
    console.log("reaching generateChartsE method");
    const processedDataLaydown = data.reduce((acc, entry) => {
        console.log(entry);
        const key = entry.Optimised;
        const monthYear = entry.MonthYear;
        if (!acc[key]) {
          acc[key] = {};
        }
        if (!acc[monthYear][key]) {
          acc[monthYear][key] = 0;
        }
        if (entry["Budget/Revenue"] === "Budget") {
          acc[monthYear][key] += entry.Value;
        }
        return acc;
    });

    const laydown_scenario_labels = Object.keys(processedDataLaydown);
    const timePeriods = Object.keys(processedDataLaydown[laydown_scenario_labels[0]]).sort((a, b) => {
        const dateA = new Date(a);
        const dateB = new Date(b);
        return dateA - dateB;
    });

    const laydown_TvData = [];
    laydown_scenario_labels.forEach((scenario) => {
        timePeriods.forEach((period) => {
            laydown_TvData.push(processedDataLaydown[scenario][period] || 0);
        });
    });

    const laydown_scenario_chartData = {
      labels: timePeriods,
      datasets: laydown_scenario_labels.map((scenario) => ({
        label: scenario,
        data: timePeriods.map(
          (period) => processedDataLaydown[scenario][period] || 0
        ), // Retrieve budget data for each scenario and period
        backgroundColor: "#" + Math.random().toString(16).substr(-6), // Random background color for each scenario
        borderWidth: 1,
        borderRadius: 15,
      })),
    };
     const laydown_scenario_chartOptions = {
       scales: {
         x: {
           stacked: false,
           title: {
             display: true,
             text: "Month/Year",
             font: {
               family: "arial",
               weight: "bold",
               size: "16",
             },
           },
           ticks: {
             font: {
               family: "Arial",
               size: "12",
               weight: "bold",
             },
           },
           grid: {
             display: false,
           },
           autoSkip: false,
         },
         y: {
           stacked: false,
           title: {
             display: true,
             text: "Budget",
             font: {
               family: "arial",
               weight: "bold",
               size: "16",
             },
           },
           ticks: {
             font: {
               family: "Arial",
               size: "12",
               weight: "bold",
             },
             callback: function (value, index, values) {
               if (value < 1000000) {
                 return (
                   "£" + Math.round(value / 1000).toLocaleString("en-US") + "K"
                 );
               } else {
                 return (
                   "£" +
                   Math.round(value / 1000000).toLocaleString("en-US") +
                   "M"
                 );
               }
             },
           },
         },
       },
       responsive: true,
       maintainAspectRatio: true,
       layout: {
         padding: {
           top: 25,
         },
       },
       plugins: {
         legend: {
           position: "top",
           display: true,
           labels: {
             font: {
               family: "Arial",
               size: 12,
               weight: "bold",
             },
           },
         },
         tooltip: {
           callbacks: {
             title: (context) => {
               return context[0].label.replaceAll(",", " ");
             },
           },
         },
       },
       animation: true,
     };
     if (laydown_scenario_chart === null) {
       laydown_scenario_chart = new Chart(
         document.getElementById("tv_curve_chart"),
         {
           type: "bar",
           data: laydown_scenario_chartData,
           options: laydown_scenario_chartOptions,
         }
       );
     } else {
       laydown_scenario_chart.data.labels = laydown_scenario_chartData.labels;
       laydown_scenario_chart.data.datasets =
         laydown_scenario_chartData.datasets;
       laydown_scenario_chart.update();
     }
}