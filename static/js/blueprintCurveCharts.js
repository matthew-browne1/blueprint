//// Fetch data from the Flask API using jQuery

var chartsSocket = io.connect(window.location.origin,
     { timeout: 500000
}
);

chartsSocket.on("connect", function () {
  console.log("connected to server");
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

function generateChartsA(data) {
    console.log("reaching generateChartsA method");

 // 1. Response Curve by Channel Group Chart
 const selectedBrand = "Nesquik"; // Initial scenario selection

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
     const selectedBrand = "Nesquik"; // Initial scenario selection
  // Filter data for the selected brand
     const filteredData = data.filter(entry => entry.Brand === selectedBrand);
 // 3a. data block
     const budget_chartData = {
       labels: [], // Budget values will be used as labels on the x-axis
       datasets: [
         {
           label: 'Revenue',
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
           label: 'Historical Budget (not optimized)',
           data: [], // Historical budget values (not optimized)
           backgroundColor: 'rgba(255, 99, 132, 0.7)', // Background color of the scatter plot
           borderColor: 'rgba(255, 99, 132, 1)', // Border color of the scatter plot
           pointStyle: 'circle', // Style of the data points (circle)
           borderWidth: 1 // Border width of the scatter plot
         },
         {
           label: 'Historical Budget (optimized)',
           data: [], // Historical budget values (optimized)
           backgroundColor: 'rgba(75, 192, 192, 0.7)', // Background color of the scatter plot
           borderColor: 'rgba(75, 192, 192, 1)', // Border color of the scatter plot
           pointStyle: 'circle', // Style of the data points (circle)
           borderWidth: 1 // Border width of the scatter plot
         },
         {
            label: 'Profit',
            data: [], // Profit values will be used as data points on the y-axis
            backgroundColor: 'rgba(255, 206, 86, 0.2)', // Background color of the line
            borderColor: 'rgba(255, 206, 86, 1)', // Border color of the line
            borderWidth: 1, // Border width of the line
        },
        {
            label: 'Profit Max',
            data: [], // Profit values will be used as data points on the y-axis
            backgroundColor: 'rgba(255, 206, 86, 0.2)', // Background color of the line
            borderColor: 'rgba(255, 206, 86, 1)', // Border color of the line
            borderWidth: 1, // Border width of the line
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
     const selectedBrand = "Nesquik"; // Initial scenario selection
  // Filter data for the selected brand
     const filteredData = data.filter(entry => entry.Brand === selectedBrand);
 // 3a. data block
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
// 3b. config block
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
// 3c. render block
     const roi_curve_chart = new Chart(document.getElementById("roi_curve_chart"),
      {
       type: 'line',
       data: roi_chartData,
        options: roi_chartOptions,
    });

   }

