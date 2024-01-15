// Fetch data from the Flask API using jQuery
const pastelColors = [
  "#FFD1DC",
  "#FFABAB",
  "#FFC3A0",
  "#FF677D",
  "#D4A5A5",
  "#B0A4E3",
  "#94B0C2",
  "#74B3CE",
  "#AEECEF",
  "#E0BBE4",
];

$.ajax({
  url: "/chart_data",
  method: "GET",
  dataType: "json",
  success: function (data) {
    const processedData = data.reduce((acc, entry) => {
      const key = entry.Scenario;

      if (!acc[key]) {
        acc[key] = { Scenario: key, Revenue: 0, Budget: 0 };
      }

      if (entry["Budget/Revenue"] === "Revenue") {
        acc[key].Revenue += entry.Value;
      } else {
        acc[key].Budget += entry.Value;
      }

      return acc;
    }, {});

    // Extract labels and datasets for Chart.js
    const labels = Object.keys(processedData);
    const revenueData = Object.values(processedData).map(
      (entry) => entry.Revenue
    );
    const budgetData = Object.values(processedData).map(
      (entry) => entry.Budget
    );

    // Set up Chart.js data structure
    const chartData = {
      labels: labels,
      datasets: [
        {
          label: "Revenue",
          data: revenueData,
          backgroundColor: "#77DD77",
        },
        {
          label: "Budget",
          data: budgetData,
          backgroundColor: "#FF6961",
        },
      ],
    };

    const budAndRevOptions = {
      scales: {
        x: { stacked: false },
        y: { stacked: false },
      },
      responsive: true,
      maintainAspectRatio: false
    };
    const ctx = document.getElementById("myChart").getContext("2d");
    const budgetAndRevenuePerScenario = new Chart(ctx, {
      type: "bar",
      data: chartData,
      options: budAndRevOptions,
    });
    const processedDataPerScenario = data.reduce((acc, entry) => {
      const scenarioKey = entry.Scenario;

      if (!acc[scenarioKey]) {
        acc[scenarioKey] = { Scenario: scenarioKey, TotalBudget: 0 };
      }

      if (entry["Budget/Revenue"] === "Budget") {
        acc[scenarioKey].TotalBudget += entry.Value;
      }

      return acc;
    }, {});

    // Extract labels and datasets for Chart.js (Budget per Scenario)
    const scenarioLabelsPerScenario = Object.keys(processedDataPerScenario);
    const datasetPerScenario = {
      label: "Budget",
      data: scenarioLabelsPerScenario.map(
        (scenario) => processedDataPerScenario[scenario].TotalBudget
      ),
      backgroundColor: "#FF6961",
    };

    // Set up Chart.js data structure (Budget per Scenario)
    const chartDataPerScenario = {
      labels: scenarioLabelsPerScenario,
      datasets: [datasetPerScenario],
    };

    // Set up Chart.js options (Budget per Scenario)
    const chartOptionsPerScenario = {
      scales: {
        x: { stacked: true },
        y: { stacked: true },
      },
      responsive: true,
      maintainAspectRatio: false
    };

    // Set up Chart.js (Budget per Scenario)
    const ctxPerScenario = document
      .getElementById("budgetPerScenarioChart")
      .getContext("2d");
    const myChartPerScenario = new Chart(ctxPerScenario, {
      type: "bar",
      data: chartDataPerScenario,
      options: chartOptionsPerScenario,
    });

    // Process the data to calculate the total budget per channel for each scenario
    const processedDataPerChannel = data.reduce((acc, entry) => {
      const scenarioKey = entry.Scenario;
      const channelKey = entry.Channel;

      if (!acc[scenarioKey]) {
        acc[scenarioKey] = { Scenario: scenarioKey, Channels: {} };
      }

      if (!acc[scenarioKey].Channels[channelKey]) {
        acc[scenarioKey].Channels[channelKey] = 0;
      }

      if (entry["Budget/Revenue"] === "Budget") {
        acc[scenarioKey].Channels[channelKey] += entry.Value;
      }

      return acc;
    }, {});

    // Extract labels and datasets for Chart.js (Budget per Channel)
    const scenarioLabelsPerChannel = Object.keys(processedDataPerChannel);
    const channelLabels = Array.from(
      new Set(data.map((entry) => entry.Channel))
    ); // Unique channel labels
    const datasetsPerChannel = [];

    channelLabels.forEach((channel, index) => {
      const dataValues = scenarioLabelsPerChannel.map(
        (scenario) => processedDataPerChannel[scenario].Channels[channel] || 0
      );
      datasetsPerChannel.push({
        label: channel,
        data: dataValues,
        backgroundColor: pastelColors[index % pastelColors.length], // Use pastel color from the set
      });
    });

    // Set up Chart.js data structure (Budget per Channel)
    const chartDataPerChannel = {
      labels: scenarioLabelsPerChannel,
      datasets: datasetsPerChannel,
    };

    // Set up Chart.js options (Budget per Channel)
    const chartOptionsPerChannel = {
      scales: {
        x: { stacked: false },
        y: { stacked: false },
      },
      responsive: true,
      maintainAspectRatio: false
    };

    // Set up Chart.js (Budget per Channel)
    const ctxPerChannel = document
      .getElementById("budgetPerChannelChart")
      .getContext("2d");
    const myChartPerChannel = new Chart(ctxPerChannel, {
      type: "bar",
      data: chartDataPerChannel,
      options: chartOptionsPerChannel,
    });

    // Function to generate random colors for each channel
    function getRandomColor() {
      const letters = "0123456789ABCDEF";
      let color = "#";
      for (let i = 0; i < 6; i++) {
        color += letters[Math.floor(Math.random() * 16)];
      }
      return color;
    }
  } 
  
});

 $.ajax({
   url: "/polynomial_data",
   type: "GET",
   dataType: "json",
   success: function (data) {
     // Once data is received, create a scatter graph with a line of best fit
     createChart(data.x, data.y, data.lobf);
   },
   error: function (error) {
     console.log("Error:", error);
   },
 });

 
 function createChart(xData, yData, lobfData) {
   var ctx = document.getElementById("polynomialChart").getContext("2d");

   var scatterData = {
     label: "Scatter Plot",
     data: xData.map((x, i) => ({ x: x, y: yData[i] })),
     backgroundColor: "rgba(75, 192, 192, 0.5)",
     borderColor: "rgba(75, 192, 192, 1)",
     pointRadius: 5,
   };

   var lineOfBestFit = {
     label: "Line of Best Fit",
     data: xData.map((x, i) => ({ x: x, y: lobfData[i] })),
     backgroundColor: "rgba(255, 99, 132, 0.2)",
     borderColor: "rgba(255, 99, 132, 1)",
     borderWidth: 1,
     fill: false,
     showLine: true,
   };

   var chartData = {
     datasets: [scatterData, lineOfBestFit],
   };

   var chartOptions = {
     scales: {
       x: {
         type: "linear",
         position: "bottom",
         beginAtZero: true,
       },
       y: {
         type: "linear",
         position: "left",
         beginAtZero: true,
       },
     },
   };

   var myChart = new Chart(ctx, {
     type: "scatter",
     data: chartData,
     options: chartOptions,
   });
 }
