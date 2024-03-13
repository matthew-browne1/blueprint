var chartsSocket = io.connect(window.location.origin,
     { timeout: 500000
}
);

chartsSocket.on('connect', function() {
    console.log('Connected');
     });

chartsSocket.emit("response_data");
chartsSocket.on('chart_response', function(data) {
  var chartResponse = data.chartResponse;

  console.log("fetched response data from back end");
//  console.log(chartResponse);
  generateChartsA(chartResponse);
});

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

function generateChartsA(data) {
    console.log("reaching generateChartsA method");

 // 1. Response Curve by Channel Group Chart
 const selectedBrand = "Shreddies"; // Initial scenario selection

  // Filter data for the selected brand
     const filteredData = data.filter(entry => entry.Brand === selectedBrand);
        filteredData.forEach(entry => {entry.OptimizationType = "ST";});

// Prepare data for the chart
    const response_chartData = {};
    filteredData.forEach(entry => {
        const channelGroup = entry["Channel Group"];
        if (!response_chartData[channelGroup]) {
            response_chartData[channelGroup] = [];
    }
    // Limiting to the first 20 points
    if (response_chartData[channelGroup].length < 40) {
        response_chartData[channelGroup].push({ x: entry.Budget, y: entry["Predicted Revenue"]});
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

 // 2. Response Curve by Channel Chart

    const filteredDataChannel = data.filter(entry => entry.Brand === selectedBrand);
        filteredDataChannel.forEach(entry => {
            entry.OptimizationType = "ST";
            entry["Channel Group"] = "social";
        });

// Prepare data for the chart
    const response_channel_Data = {};
    filteredDataChannel.forEach(entry => {
        const channel = entry.Channel;
        if (!response_channel_Data[channel]) {
             response_channel_Data[channel] = [];
    }
    // Limiting to the first 20 points
    if ( response_channel_Data[channel].length < 40) {
         response_channel_Data[channel].push({ x: entry.Budget, y: entry["Predicted Revenue"]});
    }
});

//2a. data block
    const response_channel_chartData = {
        datasets: Object.keys(response_channel_Data).map(channel => {
        return {
            label: channel,
            data:  response_channel_Data[channel],
            borderColor: '#' + (Math.random().toString(16) + '000000').substring(2, 8), // Random color for each line
            fill: false,
            radius: 0,
        };
    })
};
// 2b. config block
    const response_channel_chartOptions = {
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
// 2c. render block
    const response_channel_chart = new Chart(document.getElementById("response_channel_chart"),
      {
       type: 'line',
       data: response_channel_chartData,
        options: response_channel_chartOptions,
    });

}
function generateChartsB(data) {
    console.log("reaching generateChartsB method");
// 3. Budget Curve Chart
     const selectedBrand = "Shreddies"; // Initial scenario selection
  // Filter data for the selected brand
     const filteredData = data.filter(entry => entry.Brand === selectedBrand);
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
    filteredData.forEach(entry => {
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
    }
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
     const selectedBrand = "Shreddies"; // Initial scenario selection
  // Filter data for the selected brand
     const filteredData = data.filter(entry => entry.Brand === selectedBrand);
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
    filteredData.forEach(entry => {
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
    // 5. Budget Response Curve Chart
     const selectedBrand = "Shreddies"; // Initial scenario selection
  // Filter data for the selected brand
     const filteredData = data
        .filter(entry => entry.Brand === selectedBrand)
        .sort((a, b) => a.Budget - b.Budget);
 // 5a. data block
     const budget_response_chartData = {
       labels: [], // Budget values will be used as labels on the x-axis
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
    filteredData.forEach(entry => {
        budget_response_chartData.labels.push(entry.Budget);
        budget_response_chartData.datasets[0].data.push(entry["Total Revenue"]);
        budget_response_chartData.datasets[1].data.push(entry["Predicted Revenue"]);
});

console.log(budget_response_chartData.datasets);

// 5b. config block
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
    }
// 5c. render block
     const budget_response_chart = new Chart(document.getElementById("response_budget_chart"),
      {
       type: 'line',
       data: budget_response_chartData,
        options: budget_response_chartOptions,
    });

   }