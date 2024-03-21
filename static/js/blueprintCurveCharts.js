var chartsSocket = io.connect(window.location.origin,
     { timeout: 500000
}
);

chartsSocket.on('connect', function() {
    console.log('Connected');
     });
$(document).ready(function(){

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
        generateCharts();
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
chartsSocket.on('chart_response', function(data) {
  var chartResponse = data.chartResponse;

  console.log("fetched response data from back end");
  console.log(chartResponse)
  generateChartsA(chartResponse);
  setDefaultSelections(chartResponse);
});
    function setDefaultSelections(chartResponse) {
        // Check if chartResponse contains data
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
chartsSocket.emit("budget_data");
chartsSocket.on('chart_budget', function(data) {
  var chartBudget = data.chartBudget;

  console.log("fetched budget data from back end");
  generateChartsB(chartBudget);
});

chartsSocket.emit("roi_data");
chartsSocket.on('chart_roi', function(data) {
  var chartROI = data.chartROI;

  console.log("fetched ROI data from back end");
  generateChartsC(chartROI);
});

chartsSocket.emit("budget_response_data");
chartsSocket.on('chart_budget_response', function(data) {
  var chartBudget_response = data.chartBudget_response;

  console.log("fetched budget response data from back end");
  generateChartsD(chartBudget_response);
});
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
             type: 'linear',
             position: 'bottom',
             scaleLabel: {
               display: true,
               labelString: 'Budget'
             }
           },
           y: {
             scaleLabel: {
               display: true,
               labelString: 'Response Curve'
             }
           }
         }
    }
// 1c. render block
    const response_curve_chart = new Chart(document.getElementById("response_curve_chart"),
      {
       type: 'line',
       data: response_curve_chartData,
        options: response_curve_chartOptions,
    });
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
                type: 'linear',
                position: 'bottom',
                scaleLabel: {
                    display: true,
                    labelString: 'Budget'
                }
            },
            y: {
                scaleLabel: {
                    display: true,
                    labelString: 'Profit'
                }
            }
        }
    };

    // 3c. render block
    const budget_curve_chart = new Chart(document.getElementById("budget_curve_chart"),
        {
            type: 'line',
            data: budget_chartData,
            options: budget_chartOptions,
        });
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
             type: 'linear',
             position: 'bottom',
             scaleLabel: {
               display: true,
               labelString: 'Budget'
             }
           },
           y: {
             scaleLabel: {
               display: true,
               labelString: 'ST + LT ROI'
             }
           }
         }
    }
// 4c. render block
     const roi_curve_chart = new Chart(document.getElementById("roi_curve_chart"),
      {
       type: 'line',
       data: roi_chartData,
        options: roi_chartOptions,
    });

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
                type: 'linear',
                position: 'bottom',
                scaleLabel: {
                    display: true,
                    labelString: 'Budget'
                }
            },
            y: {
                scaleLabel: {
                    display: true,
                    labelString: 'Revenue'
                }
            }
        }
    };

    // 2c. render block
    const budget_response_chart = new Chart(document.getElementById("response_budget_chart"),
        {
            type: 'line',
            data: budget_response_chartData,
            options: budget_response_chartOptions,
        });

}
