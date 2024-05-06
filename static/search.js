$('.type-mis').on('click', function () {
    let value = $(this).text(); 

    let sections = $('section');
    console.log(sections);
    for (let i = 0; i < sections.length; i++) {
        sections[i].style.display = "block";

        if (!(sections[i].classList.contains(value))) {
            sections[i].style.display = "none";
        }
    }
});

$('.test').on('change', function () {
    let value = this.value;
    let filter = value.toUpperCase();
    let sections = $('section');
    for (let i = 0; i < sections.length; i++) {
        sections[i].style.display = "block";
        if (!(sections[i].id.toUpperCase().indexOf(filter) > -1)) {
            sections[i].style.display = "none";
        }
    }
});
