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


