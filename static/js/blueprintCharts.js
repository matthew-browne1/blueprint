let budget_scenario_chart = null;
let revenue_scenario_chart = null;
let roi_scenario_chart = null;
let budget_channel_chart = null;
let revenue_channel_chart = null;
let roi_channel_chart = null;
let laydown_scenario_chart = null;
let laydown_channel_chart = null;

$(document).ready(function() {
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

    function populateDate(selector, date, minDate, maxDate) {
      var dateInput = $(selector);
      dateInput.val(date);
      dateInput.attr("min", minDate);
      dateInput.attr("max", maxDate);
    }

    function getEarliestAndLatestDate(dates) {
      // Convert date strings to Date objects
      var dateObjects = dates.map((dateStr) => new Date(dateStr));

      // Find the earliest and latest dates
      var minDate = new Date(Math.min.apply(null, dateObjects));
      var maxDate = new Date(Math.max.apply(null, dateObjects));

      // Format dates back to YYYY-MM
      var minDateStr = minDate.toISOString().slice(0, 7);
      var maxDateStr = maxDate.toISOString().slice(0, 7);

      return { minDate: minDateStr, maxDate: maxDateStr };
    }

    $('input[name="volval"]').change(function() {
                // Reset all containers
                $('.volval-cont').css('background-color', '');
                // Change color of the associated container
                if ($('#volval1').is(':checked')) {
                    $('.volval1-cont').css('background-color', '#264F73');
                    $('#volval1-label').css('color', '#fff');
                    $(".volval2-cont").css("background-color", "#A0B1C1");
                    $("#volval2-label").css("color", "#fff");
                } else if ($('#volval2').is(':checked')) {
                    $('.volval2-cont').css('background-color', '#264F73');
                    $("#volval2-label").css("color", "#fff");
                    $(".volval1-cont").css("background-color", "#A0B1C1");
                    $("#volval1-label").css("color", "#fff");
                }
              });

    // Function to collect and send filter selections to backend
    function applyFilters() {
      var currentlySelectedMetric = selectedMetric()
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
        chartsSocket.emit("apply_filter", {'filters':filters,'metric':currentlySelectedMetric});
    }

    // Function to clear all filter selections
    function clearFilters() {
        $('select[multiple]').val([]); // Clear select field values
        applyFilters();
    }

    // Establish SocketIO connection
    var chartsSocket = io.connect(window.location.origin, { timeout: 500000 });

    chartsSocket.on('connect', function() {
        console.log('Connected');
    });

    var currentlySelectedMetric = selectedMetric()

    chartsSocket.emit("collect_data",{"metric":currentlySelectedMetric});
    // chartsSocket.emit("apply_filter", {"metric":currentlySelectedMetric});

    chartsSocket.on('chart_data', function(data) {
        chartData = data.chartData;
        var metric = selectedMetric();
        console.log(metric);
        console.log("fetched chart data from back end");
        generateCharts(metric);
    });

    chartsSocket.on('filtered_data', function(data) {
        filteredData = data.filtered_data;
        var metric = selectedMetric();
        console.log(metric);
        generateCharts(metric);
    });

    // Apply Filters button click event
    $('#applyFilters').on('click', function() {
        applyFilters();
    });

    // Clear Filters button click event
    $('#clearFilters').on('click', function() {
        clearFilters();
    });

    // Listen for 'dropdown_options' event and populate dropdowns
    chartsSocket.on('dropdown_options', function(data) {
        populateDropdown('#dateFilter', data.options.MonthYear);
        populateDropdown('#channelFilter', data.options.Channel);
        populateDropdown('#channelgroupFilter', data.options['Channel Group']);
        populateDropdown('#regionFilter', data.options.Country);
        populateDropdown('#brandFilter', data.options.Brand);
        populateDropdown('#scenarioFilter', data.options.Scenario);
        populateDropdown('#revenueFilter', data.options['Budget/Revenue']);
        
        var dates = data.options.MonthYear;
        var { minDate, maxDate } = getEarliestAndLatestDate(dates);
        populateDate('#charts-before-date', minDate, minDate, maxDate);
        populateDate('#charts-after-date', maxDate, minDate, maxDate);

        // Enable custom dropdown with search box for date filter
        enableCustomDropdown('#dateFilter');
    }).on('error', function(xhr, status, error) {
        console.error('Error fetching filter data:', error);
    });

    // Function to enable custom dropdown with search box
    function enableCustomDropdown(selector) {
        var dropdownInput = $(selector); // Corrected selector here
        var dropdownOptions = $(selector + 'Options');

        // Show dropdown options when input is focused
        dropdownInput.on("focus", function() {
            dropdownOptions.show();
        });

        // Hide dropdown options when input loses focus
        dropdownInput.on("blur", function() {
            dropdownOptions.hide();
        });

        // Filter options based on input value
        dropdownInput.on("input", function() {
            var inputValue = this.value.trim().toLowerCase();
            dropdownOptions.children(".option").each(function() {
                var optionText = $(this).text().toLowerCase();
                $(this).toggle(optionText.includes(inputValue));
            });
        });

        // Select option when clicked
        dropdownOptions.on("click", "input[type='checkbox']", function() {
            // If 'Select All' checkbox is clicked, select/deselect all options
            if ($(this).is('#selectAllDate')) {
                var isChecked = $(this).prop('checked');
                dropdownOptions.find("input[type='checkbox']").prop('checked', isChecked);
            }
            // Update the input value based on selected options
            var selectedOptions = dropdownOptions.find("input[type='checkbox']:checked").map(function() {
                return $(this).val();
            }).get();
            dropdownInput.val(selectedOptions.join(', '));
        });
    }

    // Function to generate charts
    function generateCharts(metric) {
      console.log(metric);
        if (filteredData.length > 0) {
            generateChartsA(filteredData, metric);
            generateChartsB(filteredData, metric);
            generateChartsC(filteredData, metric);
            generateChartsD(filteredData, metric);
        } else {
            generateChartsA(chartData, metric);
            generateChartsB(chartData, metric);
            generateChartsC(chartData, metric);
            generateChartsD(chartData, metric);
        }
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

      const volvalButtons = document.querySelectorAll('input[type="radio"]');
      volvalButtons.forEach((button) => {
        button.addEventListener("change", function () {
          
          var metric = selectedMetric();
          console.log("calling the generateCharts method with metric: "+metric);
          generateCharts(metric);
          
        });
      });

});


function selectedMetric() {
  const volvalButtons = document.querySelectorAll('input[type="radio"]');

  for (var i = 0; i < volvalButtons.length; i++) {
    if (volvalButtons[i].checked) {
      console.log('currently selected metric ='+volvalButtons[i].value);
      return volvalButtons[i].value;
    }
  }

  return null; // Return null if no radio button is checked
}
function generateChartsA(data, metric) {
    console.log("reaching generateChartsA method with metric: "+metric);

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
          acc[key].LT_Revenue += entry[metric];
        } else if (entry["Budget/Revenue"] === "ST Revenue") {
          acc[key].ST_Revenue += entry[metric];
        }
        else {
        acc[key].Budget += entry[metric];
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
          borderRadius: 15
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
      var metric = selectedMetric();
    
          if ( metric == "Value" ) {
              if (value < 1000000) {
                return (Math.round(value / 1000)).toLocaleString('en-US') + 'K';
              } else {
                return (Math.round(value / 1000000)).toLocaleString('en-US') + 'M';
              }
            } else {
              if (value < 1000000) {
                return (Math.round(value / 1000)).toLocaleString('en-US') + 'K';
              } else {
                return (Math.round(value / 1000000)).toLocaleString('en-US') + 'M';
              }
            }
        }
      },
     },
  },
  responsive: true,
  maintainAspectRatio: true,
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
        var metric = selectedMetric();
     
        if (metric == "Value") {
        
        const formattedValue = value < 1000000
          ? (Math.round(value / 1000 * 100) / 100).toLocaleString('en-US', { minimumFractionDigits: 1, maximumFractionDigits: 1 }) + 'K'
          : (Math.round(value / 1000000 * 100) / 100).toLocaleString('en-US', { minimumFractionDigits: 1, maximumFractionDigits: 1 }) + 'M';

        return formattedValue;
        } else {
          const formattedValue = value < 1000000
          ? (Math.round(value / 1000 * 100) / 100).toLocaleString('en-US', { minimumFractionDigits: 1, maximumFractionDigits: 1 }) + 'K'
          : (Math.round(value / 1000000 * 100) / 100).toLocaleString('en-US', { minimumFractionDigits: 1, maximumFractionDigits: 1 }) + 'M';

        return formattedValue;
        }
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
  animation: true,
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
          stack: "Stack 0",
          borderRadius: 15,
        },
        {
          label: "LT Revenue",
          data: lt_revData,
          backgroundColor: "#74B3CE",
          stack: "Stack 0",
          borderRadius: 15,
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
            return (Math.round(value / 1000)).toLocaleString('en-US') + 'K';
          } else {
            return (Math.round(value / 1000000)).toLocaleString('en-US') + 'M';
          }
        }
      },
     },
  },
  responsive: true,
  maintainAspectRatio: true,
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
        metric = selectedMetric();
        const percentageOfMax = value / maxBarValue;
        if (percentageOfMax < 0.02) {
        return '';
      }
        if (metric == 'Value') {
        
        const formattedValue = value < 1000000
          ? (Math.round(value / 1000 * 100) / 100).toLocaleString('en-US', { minimumFractionDigits: 1, maximumFractionDigits: 1 }) + 'K'
          : (Math.round(value / 1000000 * 100) / 100).toLocaleString('en-US', { minimumFractionDigits: 1, maximumFractionDigits: 1 }) + 'M';

        return formattedValue;
        } else {
          const formattedValue = value < 1000000
          ? (Math.round(value / 1000 * 100) / 100).toLocaleString('en-US', { minimumFractionDigits: 1, maximumFractionDigits: 1 }) + 'K'
          : (Math.round(value / 1000000 * 100) / 100).toLocaleString('en-US', { minimumFractionDigits: 1, maximumFractionDigits: 1 }) + 'M';

        return formattedValue;
        }
      },
      total: {
      color: 'black',
      anchor: 'center',
      align: 'center',
      formatter: (context) => {
        metric = selectedMetric();
        if (metric == "Value") {

        const totalValue = st_revData.reduce((acc, val, index) => acc + val + lt_revData[index], 0);
        const formattedTotalValue = totalValue < 1000000
          ? 'Total:' + (Math.round(totalValue / 1000 * 100) / 100).toLocaleString('en-US', { minimumFractionDigits: 1, maximumFractionDigits: 1 }) + 'K'
          : 'Total:' + (Math.round(totalValue / 1000000 * 100) / 100).toLocaleString('en-US', { minimumFractionDigits: 1, maximumFractionDigits: 1 }) + 'M';

        return formattedTotalValue;
      } else {
        const totalValue = st_revData.reduce((acc, val, index) => acc + val + lt_revData[index], 0);
        const formattedTotalValue = totalValue < 1000000
          ? 'Total: ' + (Math.round(totalValue / 1000 * 100) / 100).toLocaleString('en-US', { minimumFractionDigits: 1, maximumFractionDigits: 1 }) + 'K'
          : 'Total: ' + (Math.round(totalValue / 1000000 * 100) / 100).toLocaleString('en-US', { minimumFractionDigits: 1, maximumFractionDigits: 1 }) + 'M';

        return formattedTotalValue;
      }
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
  animation: true,
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
          stack: "Stack 0",
          borderRadius: 15,
        },
        {
          label: "LT ROI",
          data: lt_roiData,
          backgroundColor: "#94B0C2",
          stack: "Stack 0",
          borderRadius: 15,
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
       
            return (Math.round(value)).toLocaleString('en-US');
          
        }
      },
     },
  },
  responsive: true,
  maintainAspectRatio: true,
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
        ? Number(value).toFixed(2)
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
        ? Number(totalValue).toFixed(2)
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
  animation: true,
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
function generateChartsB(data, metric) {
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
          acc[scenarioKey].Channels[channelKey].LT_Revenue += entry[metric];
        } else if (entry["Budget/Revenue"] === "ST Revenue") {
          acc[scenarioKey].Channels[channelKey].ST_Revenue += entry[metric];
        }
        else {
        acc[scenarioKey].Channels[channelKey].Budget += entry[metric];
        }

     // Calculate ROIs
      acc[scenarioKey].Channels[channelKey].ST_ROI = acc[scenarioKey].Channels[channelKey].Budget !== 0 ? acc[scenarioKey].Channels[channelKey].ST_Revenue / acc[scenarioKey].Channels[channelKey].Budget : 0;
      acc[scenarioKey].Channels[channelKey].LT_ROI = acc[scenarioKey].Channels[channelKey].Budget !== 0 ? acc[scenarioKey].Channels[channelKey].LT_Revenue / acc[scenarioKey].Channels[channelKey].Budget : 0;
      acc[scenarioKey].Channels[channelKey].Total_ROI = acc[scenarioKey].Channels[channelKey].Budget !== 0 ? (acc[scenarioKey].Channels[channelKey].ST_Revenue + acc[scenarioKey].Channels[channelKey].LT_Revenue) / acc[scenarioKey].Channels[channelKey].Budget : 0;

      return acc;
    },
   {});
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
    borderWidth: 1,
    borderRadius: 15
  };
});
const channel_revenue_data = scenarios.map((scenario, index) => {
  const data = channels.map(channel => {
    const stRevenue = processedDataPerChannel[scenario]?.Channels[channel]?.ST_Revenue || 0;
    const ltRevenue = processedDataPerChannel[scenario]?.Channels[channel]?.LT_Revenue || 0;
    return stRevenue + ltRevenue;
  });
  return {
    label: scenario,
    data: data,
    backgroundColor: `hsla(${index * (360 / scenarios.length)}, 70%, 50%, 0.7)`, // Assigning different colors for each scenario
    borderColor: `hsla(${index * (360 / scenarios.length)}, 70%, 50%, 1)`,
    borderWidth: 1,
    borderRadius: 15
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
    backgroundColor: `hsla(${index * (360 / scenarios.length)}, 70%, 50%, 0.7)`, // Assigning different colors for each scenario
    borderColor: `hsla(${index * (360 / scenarios.length)}, 70%, 50%, 1)`,
    borderWidth: 1,
    borderRadius: 15
  };
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
          metric = selectedMetric();
          if (metric == "Value") {
                      if (value < 1000000) {
            return (Math.round(value / 1000)).toLocaleString('en-US') + 'K';
          } else {
            return (Math.round(value / 1000000)).toLocaleString('en-US') + 'M';
          }
          } else {
                      if (value < 1000000) {
            return (Math.round(value / 1000)).toLocaleString('en-US') + 'K';
          } else {
            return (Math.round(value / 1000000)).toLocaleString('en-US') + 'M';
          }
          }

        }
      },
     },
  },
  responsive: true,
  maintainAspectRatio: true,
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
  animation: true,
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
const totalRevenues = channel_revenue_data.flatMap(dataset => dataset.data);
const maxBarValue2 = Math.max(...totalRevenues);
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
          metric = selectedMetric();
          if (metric == "Value") {
            if (value < 1000000) {
            return (Math.round(value / 1000)).toLocaleString('en-US') + 'K';
          } else {
            return (Math.round(value / 1000000)).toLocaleString('en-US') + 'M';
          } 
          } else {
            if (value < 1000000) {
            return (Math.round(value / 1000)).toLocaleString('en-US') + 'K';
          } else {
            return (Math.round(value / 1000000)).toLocaleString('en-US') + 'M';
          }
          }

        }
      },
     },
  },
  responsive: true,
  maintainAspectRatio: true,
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
  animation: true,
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
// 6. ROI by Channel Chart
// 6a. data block
const roi_channel_chartData = {
  labels: channels.map(splitLabel(1)),
  datasets: channel_ROI_data,
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
          return (Math.round(value)).toLocaleString('en-US');
        }
      },
    },
  },
  responsive: true,
  maintainAspectRatio: true,
  layout: {
    padding: {
      top: 25,
    }
  },
  plugins: {
    tooltip: {
      callbacks:{
        title: (context) => {
          return context[0].label.replaceAll(',', ' ')
        }
      }
    },
  },
  animation: true,
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
function generateChartsC(data, metric) {
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
        acc[key][monthYear] += entry[metric];
    }
    return acc;
},
{});
 // Extract labels and datasets for laydown charts
    const laydown_scenario_labels = Object.keys(processedDataLaydown);
    const timePeriods = Object.keys(processedDataLaydown[laydown_scenario_labels[0]]).sort((a, b) => {
        const dateA = new Date(a);
        const dateB = new Date(b);
        return dateA - dateB;
    });

    const laydown_budgetData = [];

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
      datasets: laydown_scenario_labels.map((scenario) => ({
        label: scenario,
        data: timePeriods.map(
          (period) => processedDataLaydown[scenario][period] || 0
        ), // Retrieve budget data for each scenario and period
        backgroundColor: "#" + Math.random().toString(16).substr(-6), // Random background color for each scenario
        borderWidth: 1,
        borderRadius: 15
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
            return (Math.round(value / 1000)).toLocaleString('en-US') + 'K';
          } else {
            return (Math.round(value / 1000000)).toLocaleString('en-US') + 'M';
          }
        }
      },
     },
  },
  responsive: true,
  maintainAspectRatio: true,
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
  animation: true,
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
function generateChartsD(data, metric) {
// 8. Laydown by Channel Chart
// Process data for laydown channel charts
  const processedDataChannel = data.reduce((acc, entry) => {
    const key = entry.Scenario;
    const monthYear = entry.MonthYear;
    const channel = entry['Channel Group'];

      if (!acc[monthYear]) {
        acc[monthYear] = {};
      }
      if (!acc[monthYear][channel]) {
        acc[monthYear][channel] = 0;
      }
      if (entry["Budget/Revenue"] === "Budget") {
        acc[monthYear][channel] += entry[metric];
      }
    return acc;
  }, {});

// Convert month-year strings to Date objects and sort them
    const sortedMonthYears = Object.keys(processedDataChannel).sort((a, b) => {
        const dateA = new Date(a);
        const dateB = new Date(b);
        return dateA - dateB;
    });

    const laydown_channel_data = Object.keys(processedDataChannel[sortedMonthYears[0]]);

    // 8a. data block
    const laydown_channel_chartData = {
      labels: sortedMonthYears,
      datasets: laydown_channel_data.map((channel) => ({
        label: channel,
        data: sortedMonthYears.map(
          (monthYear) => processedDataChannel[monthYear][channel] || 0
        ),
        backgroundColor: "#" + Math.random().toString(16).substr(-6), // Random background color for each channel
        borderWidth: 1,
        borderRadius: 15
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
                return (Math.round(value / 1000)).toLocaleString('en-US') + 'K';
              } else {
                return (Math.round(value / 1000000)).toLocaleString('en-US') + 'M';
              }
            }
          },
        },
      },
      responsive: true,
      maintainAspectRatio: true,
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
      animation: true,
    };

// 8c. render block
    if (laydown_channel_chart === null) {
        laydown_channel_chart = new Chart(document.getElementById("laydown_channel_chart"), {
            type: "bar",
            data: laydown_channel_chartData,
            options: laydown_channel_chartOptions,
        });
    } else {
        // Update chart data
        laydown_channel_chart.data.labels = Object.keys(processedDataChannel);
        laydown_channel_chart.data.datasets = Object.keys(
          processedDataChannel[laydown_channel_chart.data.labels[0]]
        ).map((channel) => ({
          label: channel,
          data: laydown_channel_chart.data.labels.map(
            (monthYear) => processedDataChannel[monthYear][channel] || 0
          ),
          backgroundColor: "#" + Math.random().toString(16).substr(-6), // Random background color for each channel
          borderWidth: 1,
          borderRadius: 15
        }));
        laydown_channel_chart.update(); // Update the chart
    }
}