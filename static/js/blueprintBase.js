$('.circle').click(function() {
  let spWidth = $('.sidepanel').width();
  let spMarginLeft = parseInt($('.sidepanel').css('margin-left'), 10);
  let containerWidth = $('.chart-container').width();
  let w = (spMarginLeft >= 0) ? spWidth * -1 : 0;
  let cw = (w < 0) ? -w : spWidth - 22;
  let newContainerWidth = (w < 0) ? containerWidth - spWidth : containerWidth;

  $('.sidepanel').animate({
    marginLeft: w
  });

  $('.chart-container').animate({
    width: newContainerWidth
  });

  $('.circle').animate({
    left: cw
  }, function() {
    $('.fa-chevron-left').toggleClass('hide');
    $('.fa-chevron-right').toggleClass('hide');
  });
});

let sections = document.querySelectorAll('section');
let navlinks = document.querySelectorAll('nav-container a');

window.onscroll = () =>{
    sections.forEach(sec => {
        let top = window.scrollY;
        let offset = sec.offsetTop;
        let height = sec.offsetHeight;
        let id = sec.getAttribute('id');

        if(top >= offset && top < offset + height) {
            navlinks.forEach(links => {
                links.classList.remove('active');
                document.querySelector('nav-container a [href*='+ id +']').classList.add('active');
            });
        };
    });
};

// Code for populating dropdowns and handling "Select All" option
//$(document).ready(function(){
//    // Function to populate dropdown options
//    function populateDropdown(selector, options) {
//        var dropdown = $(selector);
//        dropdown.empty();
//        var selectAllOption = $('<option></option>').attr('value', 'all').text('Select All');
//        dropdown.append(selectAllOption);
//        $.each(options, function(key, value) {
//            var option = $('<option></option>').attr('value', value).text(value);
//            dropdown.append(option);
//        });
//    }
//
//    // Automatically select all options when 'Select All' is clicked
//    $(document).on('change', 'select[multiple]', function() {
//        if ($(this).val() !== null && $(this).val().includes('all')) {
//            $(this).find('option').prop('selected', true);
//            $(this).trigger('change');
//        }
//    });
//
//    // Fetch default data and populate dropdowns when the page loads
//    $.ajax({
//        url: '/filter_chart_data',
//        type: 'GET',
//        success: function(data) {
//            $('#minDate').attr('min', data.min_date).val(data.min_date);
//            $('#maxDate').attr('max', data.max_date).val(data.max_date);
//            populateDropdown('#channelFilter', data.Channel);
//            populateDropdown('#channelgroupFilter', data['Channel Group']);
//            populateDropdown('#regionFilter', data.Region);
//            populateDropdown('#countryFilter', data.Country);
//            populateDropdown('#brandFilter', data.Brand);
//            populateDropdown('#scenarioFilter', data.Scenario);
//            populateDropdown('#optimisationFilter', data['Optimisation Type']);
//            populateDropdown('#revenueFilter', data.revenue_types);
//        },
//        error: function(xhr, status, error) {
//            console.error('Error fetching filter data:', error);
//        }
//    });
//});
