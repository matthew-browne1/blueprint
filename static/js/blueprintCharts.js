let budget_scenario_chart = null;
let revenue_scenario_chart = null;
let roi_scenario_chart = null;
let budget_channel_chart = null;
let revenue_channel_chart = null;
let roi_channel_chart = null;
let laydown_scenario_chart = null;
let laydown_channel_chart = null;

$(document).ready(function(){
    var filteredData = [];
    var chartData = [];

    // Function to populate dropdown options
    function populateDropdown(selector, options) {
        var dropdown = $(selector);
        dropdown.empty();
        var selectAllOption = $('<option></option>').attr('value', 'all').text('Select All');
        dropdown.append(selectAllOption);
        $.each(options, function(key, value) {
            var option = $('<option></option>').attr('value', value).text(value);
            dropdown.append(option);
        });
    }

    // Automatically select all options when 'Select All' is clicked
    $(document).on('change', 'select[multiple]', function() {
        var $this = $(this);
        if ($this.val() !== null && $this.val().includes('all')) {
            var allOptions = $this.find('option').not(':disabled');
            var selectedOptions = allOptions.map(function() {
                return this.value;
            }).get();
            $this.val(selectedOptions);
        }
    });

    // Function to collect and send filter selections to backend
    function applyFilters() {
        var filters = {
            MonthYear: $('#dateFilter').val(),
            Region: $('#regionFilter').val(),
            Brand: $('#brandFilter').val(),
            "Channel Group": $('#channelgroupFilter').val(),
            Channel: $('#channelFilter').val(),
            Scenario: $('#scenarioFilter').val(),
            "Budget/Revenue": $('#revenueFilter').val()
        };
        console.log("Applying filters:", filters);
        chartsSocket.emit("apply_filter", filters);
        generateCharts();
    }

    // Function to clear all filter selections
    function clearFilters() {
        $('select[multiple]').val([]);
        applyFilters();
        generateCharts();
    }

    // Establish SocketIO connection
    var chartsSocket = io.connect(window.location.origin, { timeout: 500000 });

    chartsSocket.on('connect', function() {
        console.log('Connected');
    });

    chartsSocket.emit("collect_data");
    chartsSocket.emit("apply_filter");

chartsSocket.on('chart_data', function(data) {
    chartData = data.chartData; // Update chartData when received from backend
    console.log("fetched chart data from back end");
    generateCharts();
});

chartsSocket.on('filtered_data', function(data) {
    filteredData = data.filtered_data; // Update filteredData when received from backend
    generateCharts();
});


    // Apply Filters button click event
    $('#applyFilters').on('click', function() {
        applyFilters();
    });

    // Clear Filters button click event
    $('#clearFilters').on('click', function() {
        clearFilters();
    });

    function generateCharts() {
        if (filteredData.length > 0) {
            generateChartsA(filteredData);
            generateChartsB(filteredData);
            generateChartsC(filteredData);
        } else {
            generateChartsA(chartData);
            generateChartsB(chartData);
            generateChartsC(chartData);
            generateChartsD(chartData);
        }
        console.log(filteredData)
    }

    // Listen for 'dropdown_options' event and populate dropdowns
    chartsSocket.on('dropdown_options', function(data) {
        populateDropdown('#dateFilter', data.options.MonthYear);
        populateDropdown('#channelFilter', data.options.Channel);
        populateDropdown('#channelgroupFilter', data.options['Channel Group']);
        populateDropdown('#regionFilter', data.options.Region);
        populateDropdown('#brandFilter', data.options.Brand);
        populateDropdown('#scenarioFilter', data.options.Scenario);
        populateDropdown('#revenueFilter', data.options['Budget/Revenue']);
    }).on('error', function(xhr, status, error) {
        console.error('Error fetching filter data:', error);
    });
});

function generateChartsA(data) {
    console.log("reaching generateChartsA method");
   // Process data for scenario charts
    const processedData = data.reduce((acc, entry) => {
      const key = entry.Scenario;

      if (!acc[key]) {
        acc[key] = {
        Scenario: key,
        Budget: 0,
        LT_Revenue: 0,
        ST_Revenue: 0,
        LT_ROI: 0,
        ST_ROI: 0,
        ROI: 0
        };
      }

       if (entry["Budget/Revenue"] === "LT Revenue") {
          acc[key].LT_Revenue += entry.Value;
        } else if (entry["Budget/Revenue"] === "ST Revenue") {
          acc[key].ST_Revenue += entry.Value;
        }
        else {
        acc[key].Budget += entry.Value;
        }

     // Calculate ROIs
      acc[key].ST_ROI = acc[key].Budget !== 0 ? acc[key].ST_Revenue / acc[key].Budget : 0;
      acc[key].LT_ROI = acc[key].Budget !== 0 ? acc[key].LT_Revenue / acc[key].Budget : 0;
      acc[key].Total_ROI = acc[key].Budget !== 0 ? (acc[key].ST_Revenue + acc[key].LT_Revenue) / acc[key].Budget : 0;

      return acc;
    }, {});
    // Extract labels and datasets for scenario charts
    const scenario_labels = Object.keys(processedData);
    const budgetData = Object.values(processedData).map((entry) => entry.Budget);
    const lt_revData = Object.values(processedData).map((entry) => entry.LT_Revenue);
    const st_revData = Object.values(processedData).map((entry) => entry.ST_Revenue);
    const lt_roiData = Object.values(processedData).map((entry) => entry.LT_ROI);
    const st_roiData = Object.values(processedData).map((entry) => entry.ST_ROI);
    const roiData = Object.values(processedData).map((entry) => entry.Total_ROI);
   //console.log(st_roiData);
 // Function to break scenario into 2 lines
function splitLabel(maxWords) {
  return function(label) {
    const words = label.split(/\s+/).filter(Boolean);
    if (words.length <= maxWords) {
      return label;
    } else {
      const chunks = [];
      for (let i = 0; i < words.length; i += maxWords) {
        chunks.push(words.slice(i, i + maxWords).join(' '));
      }
      return chunks;
    }
  };
}
// 1. Spend by Scenario Chart
// 1a. data block
    const budget_scenario_chartData = {
      labels: scenario_labels.map(splitLabel(3)),
      datasets: [
        {
          label: "Budget",
          data: budgetData,
          backgroundColor: "#FF6961",
        },
      ],
    };
// 1b. config block
 const budget_scenario_chartOptions = {
  scales: {
   x: {
      stacked: false,
      title: {
        display: true,
        text: 'Scenario',
        font: {
          family: 'arial',
          weight: 'bold',
          size: '16',
        },
      },
      ticks: {
        font: {
          family: 'Arial',
          size: '12',
          weight: 'bold',
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
        text: 'Budget',
        font: {
          family: 'arial',
          weight: 'bold',
          size: '16',
        },
      },
    ticks: {
        font: {
          family: 'Arial',
          size: '12',
          weight: 'bold',
        },
     callback: function(value, index, values) {
          if (value < 1000000) {
            return '£' + (Math.round(value / 1000)).toLocaleString('en-US') + 'K';
          } else {
            return '£' + (Math.round(value / 1000000)).toLocaleString('en-US') + 'M';
          }
        }
      },
     },
  },
  responsive: false,
  maintainAspectRatio: false,
  layout: {
        padding: {
            top: 25,
        }
    },
  plugins: {
    datalabels: {
      color: 'black',
      anchor: 'end',
      align: 'top',
      offset: 4,
      formatter: (value, context) => {
        const formattedValue = value < 1000000
          ? '£' + (Math.round(value / 1000 * 100) / 100).toLocaleString('en-US', { minimumFractionDigits: 1, maximumFractionDigits: 1 }) + 'K'
          : '£' + (Math.round(value / 1000000 * 100) / 100).toLocaleString('en-US', { minimumFractionDigits: 1, maximumFractionDigits: 1 }) + 'M';

        return formattedValue;
      },
      labels: {
        title: {
          font: {
            weight: 'bold',
          },
        },
        value: {
          color: 'black',
        },
      },
    },
       legend: {
    display: false,
  },
  tooltip: {
    callbacks:{
        title: (context) => {
        return context[0].label.replaceAll(',', ' ')}
    }
  },
  },
  animation: false,
};
 // 1c. render block
   if (budget_scenario_chart === null) {
        budget_scenario_chart = new Chart(document.getElementById("budget_scenario_chart"),
            {
                type: "bar",
                data: budget_scenario_chartData,
                plugins: [ChartDataLabels],
                options: budget_scenario_chartOptions,
            });
    } else {
        budget_scenario_chart.data.labels = scenario_labels.map(splitLabel(3));
        budget_scenario_chart.data.datasets[0].data = budgetData;
        budget_scenario_chart.update();
    }

// 2. Revenue by Scenario Chart
const maxBarValue = Math.max(...st_revData.concat(lt_revData));
// 2a. data block
    const revenue_scenario_chartData = {
      labels: scenario_labels.map(splitLabel(3)),
      datasets: [
                {
          label: "ST Revenue",
          data: st_revData,
          backgroundColor: "#FFC3A0",
          stack: 'Stack 0',
        },
                {
          label: "LT Revenue",
          data: lt_revData,
          backgroundColor: "#74B3CE",
          stack: 'Stack 0',
        },
      ],
    };
// 2b. config block
    const revenue_scenario_chartOptions = {
   scales: {
   x: {
      stacked: true,
      title: {
        display: true,
        text: 'Scenario',
        font: {
          family: 'arial',
          weight: 'bold',
          size: '16',
        },
      },
      ticks: {
        font: {
          family: 'Arial',
          size: '12',
          weight: 'bold',
        },
      },
      grid: {
        display: false,
      },
      autoSkip: false,
    },
    y: {
    stacked: true,
          title: {
        display: true,
        text: 'Revenue',
        font: {
          family: 'arial',
          weight: 'bold',
          size: '16',
        },
      },
    ticks: {
        font: {
          family: 'Arial',
          size: '12',
          weight: 'bold',
        },
     callback: function(value, index, values) {
          if (value < 1000000) {
            return '£' + (Math.round(value / 1000)).toLocaleString('en-US') + 'K';
          } else {
            return '£' + (Math.round(value / 1000000)).toLocaleString('en-US') + 'M';
          }
        }
      },
     },
  },
  responsive: false,
  maintainAspectRatio: false,
  layout: {
        padding: {
            top: 25,
        }
    },
  plugins: {
    datalabels: {
      color: 'black',
      anchor: 'center',
      align: 'top',
      offset: 4,
      formatter: (value, context) => {
        const percentageOfMax = value / maxBarValue;
      if (percentageOfMax < 0.02) {
        return '';
      }
        const formattedValue = value < 1000000
          ? '£' + (Math.round(value / 1000 * 100) / 100).toLocaleString('en-US', { minimumFractionDigits: 1, maximumFractionDigits: 1 }) + 'K'
          : '£' + (Math.round(value / 1000000 * 100) / 100).toLocaleString('en-US', { minimumFractionDigits: 1, maximumFractionDigits: 1 }) + 'M';

        return formattedValue;
      },
      total: {
      color: 'black',
      anchor: 'center',
      align: 'center',
      formatter: (context) => {
        const totalValue = st_revData.reduce((acc, val, index) => acc + val + lt_revData[index], 0);
        const formattedTotalValue = totalValue < 1000000
          ? 'Total: £' + (Math.round(totalValue / 1000 * 100) / 100).toLocaleString('en-US', { minimumFractionDigits: 1, maximumFractionDigits: 1 }) + 'K'
          : 'Total: £' + (Math.round(totalValue / 1000000 * 100) / 100).toLocaleString('en-US', { minimumFractionDigits: 1, maximumFractionDigits: 1 }) + 'M';

        return formattedTotalValue;
      },
      labels: {
        title: {
          font: {
            weight: 'bold',
          },
        },
        value: {
          color: 'black',
        },
      },
    },
    },
  tooltip: {
    callbacks:{
        title: (context) => {
        return context[0].label.replaceAll(',', ' ')}
    }
  },
  },
  animation: false,
};
// 2c. render block
    if (revenue_scenario_chart === null) {
        revenue_scenario_chart = new Chart(document.getElementById("revenue_scenario_chart"), {
            type: "bar",
            data: revenue_scenario_chartData,
            plugins: [ChartDataLabels],
            options: revenue_scenario_chartOptions,
        });
    } else {
        revenue_scenario_chart.data.labels = revenue_scenario_chartData.labels;
        revenue_scenario_chart.data.datasets[0].data = revenue_scenario_chartData.datasets[0].data;
        revenue_scenario_chart.data.datasets[1].data = revenue_scenario_chartData.datasets[1].data;
        revenue_scenario_chart.update();
    }

// 3. ROI by Scenario Chart
// 3a. data block
    const roi_scenario_chartData = {
      labels: scenario_labels.map(splitLabel(3)),
      datasets: [
                {
          label: "ST ROi",
          data: st_roiData,
          backgroundColor: "#B0A4E3",
          stack: 'Stack 0',
        },
                {
          label: "LT ROI",
          data: lt_roiData,
          backgroundColor: "#94B0C2",
          stack: 'Stack 0',
        },
      ],
    };
// 3b. config block
    const roi_scenario_chartOptions = {
   scales: {
   x: {
      stacked: true,
      title: {
        display: true,
        text: 'Scenario',
        font: {
          family: 'arial',
          weight: 'bold',
          size: '16',
        },
      },
      ticks: {
        font: {
          family: 'Arial',
          size: '12',
          weight: 'bold',
        },
      },
      grid: {
        display: false,
      },
      autoSkip: false,
    },
    y: {
    stacked: true,
          title: {
        display: true,
        text: 'ROI',
        font: {
          family: 'arial',
          weight: 'bold',
          size: '16',
        },
      },
    ticks: {
        font: {
          family: 'Arial',
          size: '12',
          weight: 'bold',
        },
     callback: function(value, index, values) {
            return '£' + (Math.round(value)).toLocaleString('en-US');
          }
      },
     },
  },
  responsive: false,
  maintainAspectRatio: false,
  layout: {
        padding: {
            top: 25,
        }
    },
  plugins: {
    datalabels: {
      color: 'black',
      anchor: 'center',
      align: 'top',
      offset: 4,
      formatter: (value, context) => {
    const formattedValue = value !== null && value !== undefined
        ? '£' + Number(value).toFixed(2)
        : '';

    return formattedValue;
},
      total: {
      color: 'black',
      anchor: 'center',
      align: 'center',
      formatter: (context) => {
        const totalValue = roiData
    const formattedValue = totalValue !== null && totalValue !== undefined
        ? '£' + Number(totalValue).toFixed(2)
        : '';

    return formattedValue;
},
      },
      labels: {
        title: {
          font: {
            weight: 'bold',
          },
        },
        value: {
          color: 'black',
        },
      },
    },
  tooltip: {
    callbacks:{
        title: (context) => {
        return context[0].label.replaceAll(',', ' ')}
    }
  },
  },
  animation: false,
};
// 3c. render block
if (roi_scenario_chart === null) {
    roi_scenario_chart = new Chart(document.getElementById("roi_scenario_chart"), {
        type: "bar",
        data: roi_scenario_chartData,
        plugins: [ChartDataLabels],
        options: roi_scenario_chartOptions,
    });
} else {
    roi_scenario_chart.data.labels = roi_scenario_chartData.labels;
    roi_scenario_chart.data.datasets[0].data = roi_scenario_chartData.datasets[0].data;
    roi_scenario_chart.data.datasets[1].data = roi_scenario_chartData.datasets[1].data;
    roi_scenario_chart.update();
}
}
function generateChartsB(data) {
        console.log("reaching generateChartsB method");
// Process data for channel charts
     const processedDataPerChannel = data.reduce((acc, entry) => {
      const scenarioKey = entry.Scenario;
      const channelKey = entry.Channel;

      if (!acc[scenarioKey]) {
        acc[scenarioKey] = { Scenario: scenarioKey, Channels: {} };
      }

      if (!acc[scenarioKey].Channels[channelKey]) {
        acc[scenarioKey].Channels[channelKey] = {
        Budget: 0,
        LT_Revenue: 0,
        ST_Revenue: 0,
        LT_ROI: 0,
        ST_ROI: 0,
        Total_ROI: 0
        };
      }
       if (entry["Budget/Revenue"] === "LT Revenue") {
          acc[scenarioKey].Channels[channelKey].LT_Revenue += entry.Value;
        } else if (entry["Budget/Revenue"] === "ST Revenue") {
          acc[scenarioKey].Channels[channelKey].ST_Revenue += entry.Value;
        }
        else {
        acc[scenarioKey].Channels[channelKey].Budget += entry.Value;
        }

     // Calculate ROIs
      acc[scenarioKey].Channels[channelKey].ST_ROI = acc[scenarioKey].Channels[channelKey].Budget !== 0 ? acc[scenarioKey].Channels[channelKey].ST_Revenue / acc[scenarioKey].Channels[channelKey].Budget : 0;
      acc[scenarioKey].Channels[channelKey].LT_ROI = acc[scenarioKey].Channels[channelKey].Budget !== 0 ? acc[scenarioKey].Channels[channelKey].LT_Revenue / acc[scenarioKey].Channels[channelKey].Budget : 0;
      acc[scenarioKey].Channels[channelKey].Total_ROI = acc[scenarioKey].Channels[channelKey].Budget !== 0 ? (acc[scenarioKey].Channels[channelKey].ST_Revenue + acc[scenarioKey].Channels[channelKey].LT_Revenue) / acc[scenarioKey].Channels[channelKey].Budget : 0;

      return acc;
    },
   {});
   //console.log(processedDataPerChannel);
// Extract labels and datasets for scenario charts
const scenarios = Object.keys(processedDataPerChannel);
const channels = Object.keys(processedDataPerChannel[scenarios[0]].Channels);
const channel_budget_data = scenarios.map((scenario, index) => {
  const data = channels.map(channel => {
    const budget = processedDataPerChannel[scenario]?.Channels[channel]?.Budget || 0; // Handling potential undefined values
    return budget;
  });
  return {
    label: scenario,
    data: data,
    backgroundColor: `hsla(${(index * (360 / scenarios.length))}, 70%, 50%, 0.7)`, // Assigning different colors for each scenario
    borderColor: `hsla(${(index * (360 / scenarios.length))}, 70%, 50%, 1)`,
    borderWidth: 1
  };
});
//console.log(channel_budget_data);
const channel_revenue_data = scenarios.map((scenario, index) => {
  const data = channels.map(channel => {
    const stRevenue = processedDataPerChannel[scenario]?.Channels[channel]?.ST_Revenue || 0;
    const ltRevenue = processedDataPerChannel[scenario]?.Channels[channel]?.LT_Revenue || 0;
    return stRevenue + ltRevenue;
  });
  return {
    label: scenario,
    data: data,
    backgroundColor: `hsla(${(index * (360 / scenarios.length))}, 70%, 50%, 0.7)`, // Assigning different colors for each scenario
    borderColor: `hsla(${(index * (360 / scenarios.length))}, 70%, 50%, 1)`,
    borderWidth: 1,
  };
});
const channel_ROI_data = scenarios.map((scenario, index) => {
  const data = channels.map(channel => {
    const totalROI = processedDataPerChannel[scenario]?.Channels[channel]?.Total_ROI || 0;
    return totalROI;
  });
  return {
    label: scenario,
    data: data,
    backgroundColor: `hsla(${(index * (360 / scenarios.length))}, 70%, 50%, 0.7)`, // Assigning different colors for each scenario
    borderColor: `hsla(${(index * (360 / scenarios.length))}, 70%, 50%, 1)`,
    borderWidth: 1,
  };
});
//console.log(channel_revenue_data);
 // Function to generate random colors for each channel
function getRandomColor() {
  const letters = "0123456789ABCDEF";
  let color = "#";
  for (let i = 0; i < 6; i++) {
    color += letters[Math.floor(Math.random() * 16)];
  }
  return color;
}
function splitLabel(maxWords) {
  return function(label) {
    const words = label.split(/\s+/).filter(Boolean);
    if (words.length <= maxWords) {
      return label;
    } else {
      const chunks = [];
      for (let i = 0; i < words.length; i += maxWords) {
        chunks.push(words.slice(i, i + maxWords).join(' '));
      }
      return chunks;
    }
  };
}
// 4. Spend by Channel Chart
// 4a. data block
    const budget_channel_chartData = {
      labels: channels.map(splitLabel(1)),
      datasets: channel_budget_data ,
    };
// 4b. config block
 const budget_channel_chartOptions = {
  scales: {
   x: {
      stacked: false,
      title: {
        display: true,
        text: 'Channel',
        font: {
          family: 'arial',
          weight: 'bold',
          size: '16',
        },
      },
      ticks: {
        font: {
          family: 'Arial',
          size: '12',
          weight: 'bold',
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
        text: 'Budget',
        font: {
          family: 'arial',
          weight: 'bold',
          size: '16',
        },
      },
    ticks: {
        font: {
          family: 'Arial',
          size: '12',
          weight: 'bold',
        },
     callback: function(value, index, values) {
          if (value < 1000000) {
            return '£' + (Math.round(value / 1000)).toLocaleString('en-US') + 'K';
          } else {
            return '£' + (Math.round(value / 1000000)).toLocaleString('en-US') + 'M';
          }
        }
      },
     },
  },
  responsive: false,
  maintainAspectRatio: false,
  layout: {
        padding: {
            top: 25,
        }
    },
  plugins: {
    legend: {
      position: 'top',
      display: true,
      labels: {
        font: {
          family: 'Arial',
          size: 12,
          weight: 'bold'
        }
      }
    },
  tooltip: {
    callbacks:{
        title: (context) => {
        return context[0].label.replaceAll(',', ' ')}
    }
  },
  },
  animation: false,
};
// 4c. render block
if (budget_channel_chart === null) {
    budget_channel_chart = new Chart(document.getElementById("budget_channel_chart"), {
        type: "bar",
        data: budget_channel_chartData,
        options: budget_channel_chartOptions,
    });
} else {
    budget_channel_chart.data.labels = budget_channel_chartData.labels;
    budget_channel_chart.data.datasets = budget_channel_chartData.datasets;
    budget_channel_chart.update();
}
// 5. Revenue by Channel Chart
// Function to handle dropdown selection
function handleDropdownChange() {
  const selectedValue = document.getElementById('revenueFilter').value;
  const channel_revenue_data_filtered = scenarios.map((scenario, index) => {
    const data = channels.map(channel => {
      let revenue = 0;
      if (selectedValue === 'ST') {
        revenue = processedDataPerChannel[scenario]?.Channels[channel]?.ST_Revenue || 0;
      } else if (selectedValue === 'LT') {
        revenue = processedDataPerChannel[scenario]?.Channels[channel]?.LT_Revenue || 0;
      } else if (selectedValue === 'ALL') {
        const stRevenue = processedDataPerChannel[scenario]?.Channels[channel]?.ST_Revenue || 0;
        const ltRevenue = processedDataPerChannel[scenario]?.Channels[channel]?.LT_Revenue || 0;
        revenue = stRevenue + ltRevenue;
      }
      return revenue;
    });
    return {
      label: scenario,
      data: data,
      backgroundColor: `hsla(${(index * (360 / scenarios.length))}, 70%, 50%, 0.7)`, // Assigning different colors for each scenario
      borderColor: `hsla(${(index * (360 / scenarios.length))}, 70%, 50%, 1)`,
      borderWidth: 1,
    };
  });
  revenue_channel_chart.data.datasets = channel_revenue_data_filtered;
  revenue_channel_chart.update();
}
// Event listener
document.getElementById("revenueFilter").addEventListener("change", handleDropdownChange);
const totalRevenues = channel_revenue_data.flatMap(dataset => dataset.data);
const maxBarValue2 = Math.max(...totalRevenues);
//console.log(maxBarValue2);
// 5a. data block
    const revenue_channel_chartData = {
      labels: channels.map(splitLabel(1)),
      datasets: channel_revenue_data ,
    };
// 5b. config block
    const revenue_channel_chartOptions = {
   scales: {
   x: {
      stacked: false,
      title: {
        display: true,
        text: 'Channel',
        font: {
          family: 'arial',
          weight: 'bold',
          size: '16',
        },
      },
      ticks: {
        font: {
          family: 'Arial',
          size: '12',
          weight: 'bold',
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
        text: 'Revenue',
        font: {
          family: 'arial',
          weight: 'bold',
          size: '16',
        },
      },
    ticks: {
        font: {
          family: 'Arial',
          size: '12',
          weight: 'bold',
        },
     callback: function(value, index, values) {
          if (value < 1000000) {
            return '£' + (Math.round(value / 1000)).toLocaleString('en-US') + 'K';
          } else {
            return '£' + (Math.round(value / 1000000)).toLocaleString('en-US') + 'M';
          }
        }
      },
     },
  },
  responsive: false,
  maintainAspectRatio: false,
  layout: {
        padding: {
            top: 25,
        }
    },
  plugins: {
        legend: {
      position: 'top',
      display: true,
      labels: {
        font: {
          family: 'Arial',
          size: 12,
          weight: 'bold'
        }
      }
    },
  tooltip: {
    callbacks:{
        title: (context) => {
        return context[0].label.replaceAll(',', ' ')}
    }
  },
  },
  animation: false,
};
// 5c. render block
if (revenue_channel_chart === null) {
    revenue_channel_chart = new Chart(document.getElementById("revenue_channel_chart"), {
        type: "bar",
        data: revenue_channel_chartData,
        options: revenue_channel_chartOptions,
    });
} else {
    revenue_channel_chart.data.labels = revenue_channel_chartData.labels;
    revenue_channel_chart.data.datasets = revenue_channel_chartData.datasets;
    revenue_channel_chart.update();
}
// 6. ROI by Channel Chart
function handleDropdownChange() {
  const selectedValue = document.getElementById('revenueFilter').value;
  let dataKey = '';
  if (selectedValue === 'ST Revenue') {
    dataKey = 'ST_ROI';
  } else if (selectedValue === 'LT Revenue') {
    dataKey = 'LT_ROI';
  } else if (selectedValue === 'ALL') {
    dataKey = 'Total_ROI';
  }
  const channel_ROI_data_filtered = scenarios.map((scenario, index) => {
    const data = channels.map(channel => {
      return processedDataPerChannel[scenario]?.Channels[channel]?.[dataKey] || 0;
    });
    return {
      label: scenario,
      data: data,
      backgroundColor: `hsla(${(index * (360 / scenarios.length))}, 70%, 50%, 0.7)`,
      borderColor: `hsla(${(index * (360 / scenarios.length))}, 70%, 50%, 1)`,
      borderWidth: 1,
    };
  });
  roi_channel_chart.data.datasets = channel_ROI_data_filtered;
  roi_channel_chart.update();
}

document.addEventListener("DOMContentLoaded", function() {
  document.getElementById("revenueFilter").value = "ST Revenue";
  handleDropdownChange();
});

// 6a. data block
    const roi_channel_chartData = {
      labels: channels.map(splitLabel(1)),
      datasets: channel_revenue_data,
    };
// 6b. config block
    const roi_channel_chartOptions = {
   scales: {
   x: {
      stacked: false,
      title: {
        display: true,
        text: 'Scenario',
        font: {
          family: 'arial',
          weight: 'bold',
          size: '16',
        },
      },
      ticks: {
        font: {
          family: 'Arial',
          size: '12',
          weight: 'bold',
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
        text: 'ROI',
        font: {
          family: 'arial',
          weight: 'bold',
          size: '16',
        },
      },
    ticks: {
        font: {
          family: 'Arial',
          size: '12',
          weight: 'bold',
        },
     callback: function(value, index, values) {
            return '£' + (Math.round(value)).toLocaleString('en-US');
          }
      },
     },
  },
  responsive: false,
  maintainAspectRatio: false,
  layout: {
        padding: {
            top: 25,
        }
    },
  plugins: {
  tooltip: {
    callbacks:{
        title: (context) => {
        return context[0].label.replaceAll(',', ' ')}
    }
  },
  },
  animation: false,
};
// 6c. render block
if (roi_channel_chart === null) {
    roi_channel_chart = new Chart(document.getElementById("roi_channel_chart"), {
        type: "bar",
        data: roi_channel_chartData,
        options: roi_channel_chartOptions,
    });
} else {
    roi_channel_chart.data.labels = roi_channel_chartData.labels;
    roi_channel_chart.data.datasets = roi_channel_chartData.datasets;
    roi_channel_chart.update();
}
}
function generateChartsC(data) {
        console.log("reaching generateChartsC method");
// Process data for laydown scenario charts
const processedDataLaydown = data.reduce((acc, entry) => {
    const key = entry.Scenario;
    const monthYear = entry.MonthYear;
    if (!acc[key]) {
        acc[key] = {};
    }
    if (!acc[key][monthYear]) {
        acc[key][monthYear] = 0;
    }
    if (entry["Budget/Revenue"] === "Budget") {
        acc[key][monthYear] += entry.Value;
    }
    return acc;
},
{});
// Extract labels and datasets for laydown charts
const laydown_scenario_labels = Object.keys(processedDataLaydown);
const laydown_budgetData = [];
const timePeriods = Object.keys(processedDataLaydown[laydown_scenario_labels[0]]);

// Iterate through each scenario and time period to extract data
laydown_scenario_labels.forEach(scenario => {
    timePeriods.forEach(period => {
        laydown_budgetData.push(processedDataLaydown[scenario][period] || 0);
    });
});

// 7. Laydown by Scenario Chart
// 7a. data block
    const laydown_scenario_chartData = {
      labels: timePeriods,
      datasets: laydown_scenario_labels.map(scenario => ({
        label: scenario,
        data: timePeriods.map(period => processedDataLaydown[scenario][period] || 0), // Retrieve budget data for each scenario and period
        backgroundColor: '#' + Math.random().toString(16).substr(-6), // Random background color for each scenario
        borderWidth: 1,
    })),
    };
// 7b. config block
 const laydown_scenario_chartOptions = {
  scales: {
   x: {
      stacked: false,
      title: {
        display: true,
        text: 'Month/Year',
        font: {
          family: 'arial',
          weight: 'bold',
          size: '16',
        },
      },
      ticks: {
        font: {
          family: 'Arial',
          size: '12',
          weight: 'bold',
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
        text: 'Budget',
        font: {
          family: 'arial',
          weight: 'bold',
          size: '16',
        },
      },
    ticks: {
        font: {
          family: 'Arial',
          size: '12',
          weight: 'bold',
        },
     callback: function(value, index, values) {
          if (value < 1000000) {
            return '£' + (Math.round(value / 1000)).toLocaleString('en-US') + 'K';
          } else {
            return '£' + (Math.round(value / 1000000)).toLocaleString('en-US') + 'M';
          }
        }
      },
     },
  },
  responsive: false,
  maintainAspectRatio: false,
  layout: {
        padding: {
            top: 25,
        }
    },
  plugins: {
    legend: {
      position: 'top',
      display: true,
      labels: {
        font: {
          family: 'Arial',
          size: 12,
          weight: 'bold'
        }
      }
    },
  tooltip: {
    callbacks:{
        title: (context) => {
        return context[0].label.replaceAll(',', ' ')}
    }
  },
  },
  animation: false,
};
// 7c. render block
if (laydown_scenario_chart === null) {
    laydown_scenario_chart = new Chart(document.getElementById("laydown_scenario_chart"), {
        type: "bar",
        data: laydown_scenario_chartData,
        options: laydown_scenario_chartOptions,
    });
} else {
    laydown_scenario_chart.data.labels = laydown_scenario_chartData.labels;
    laydown_scenario_chart.data.datasets = laydown_scenario_chartData.datasets;
    laydown_scenario_chart.update();
}
}
function generateChartsD(data) {
// 8. Laydown by Channel Chart
// Process data for laydown channel charts
const uniqueScenarios = [...new Set(data.map(entry => entry.Scenario))];

// Populate dropdown list with unique scenarios
const channelDropdown = document.getElementById("channel_dropdown");
uniqueScenarios.forEach(scenario => {
  const option = document.createElement("option");
  option.value = scenario;
  option.text = scenario;
  channelDropdown.appendChild(option);
});

// Set default selected option as the first one
channelDropdown.selectedIndex = 0;
let selectedScenario = uniqueScenarios[0];

// Declare laydown_channel_chart before the updateChart function
let laydown_channel_chart;

// Add event listener to dropdown for scenario selection
channelDropdown.addEventListener('change', function() {
  selectedScenario = this.value;
  updateChart(selectedScenario);
});

// Initial chart rendering
updateChart(selectedScenario);

function updateChart(selectedScenario) {
  const processedDataChannel = data.reduce((acc, entry) => {
    const key = entry.Scenario;
    const monthYear = entry.MonthYear;

    if (key === selectedScenario) {
      const channel = entry['Channel Group'];
      if (!acc[monthYear]) {
        acc[monthYear] = {};
      }
      if (!acc[monthYear][channel]) {
        acc[monthYear][channel] = 0;
      }
      if (entry["Budget/Revenue"] === "Budget") {
        acc[monthYear][channel] += entry.Value;
      }
    }
    return acc;
  }, {});

  // Check if laydown_channel_chart is initialized
  if (!laydown_channel_chart) {
    const laydown_channel_labels = Object.keys(processedDataChannel);
    const laydown_channel_data = Object.keys(processedDataChannel[laydown_channel_labels[0]]);

    // 8a. data block
    const laydown_channel_chartData = {
      labels: laydown_channel_labels,
      datasets: laydown_channel_data.map(channel => ({
        label: channel,
        data: laydown_channel_labels.map(monthYear => processedDataChannel[monthYear][channel] || 0),
        backgroundColor: '#' + Math.random().toString(16).substr(-6), // Random background color for each channel
        borderWidth: 1,
      })),
    };

    // 8b. config block
    const laydown_channel_chartOptions = {
      scales: {
        x: {
          stacked: true,
          title: {
            display: true,
            text: 'Month/Year',
            font: {
              family: 'arial',
              weight: 'bold',
              size: '16',
            },
          },
          ticks: {
            font: {
              family: 'Arial',
              size: '12',
              weight: 'bold',
            },
          },
          grid: {
            display: false,
          },
          autoSkip: false,
        },
        y: {
          stacked: true,
          title: {
            display: true,
            text: 'Budget',
            font: {
              family: 'arial',
              weight: 'bold',
              size: '16',
            },
          },
          ticks: {
            font: {
              family: 'Arial',
              size: '12',
              weight: 'bold',
            },
            callback: function(value, index, values) {
              if (value < 1000000) {
                return '£' + (Math.round(value / 1000)).toLocaleString('en-US') + 'K';
              } else {
                return '£' + (Math.round(value / 1000000)).toLocaleString('en-US') + 'M';
              }
            }
          },
        },
      },
      responsive: false,
      maintainAspectRatio: false,
      layout: {
        padding: {
          top: 25,
        }
      },
      plugins: {
        legend: {
          position: 'top',
          display: true,
          labels: {
            font: {
              family: 'Arial',
              size: 12,
              weight: 'bold'
            }
          }
        },
        tooltip: {
          callbacks:{
            title: (context) => {
              return context[0].label.replaceAll(',', ' ')
            }
          }
        },
      },
      animation: false,
    };

    // 8c. render block
    laydown_channel_chart = new Chart(document.getElementById("laydown_channel_chart"), {
      type: "bar",
      data: laydown_channel_chartData,
      options: laydown_channel_chartOptions,
    });
  } else {
    // Update chart data
    laydown_channel_chart.data.labels = Object.keys(processedDataChannel);
    laydown_channel_chart.data.datasets = Object.keys(processedDataChannel[laydown_channel_chart.data.labels[0]]).map(channel => ({
      label: channel,
      data: laydown_channel_chart.data.labels.map(monthYear => processedDataChannel[monthYear][channel] || 0),
      backgroundColor: '#' + Math.random().toString(16).substr(-6), // Random background color for each channel
      borderWidth: 1,
    }));
    laydown_channel_chart.update();
  }
}
}