// NAVIGATION BAR
// To bold the font of the current nav link for the page that the user is looking at
document.addEventListener("DOMContentLoaded", function() {
    var current_path = window.location.pathname;
    var nav_links = document.querySelectorAll(".nav-bar a");
    nav_links.forEach(function(link) {
        if (link.getAttribute("href") === current_path) {
            link.classList.add("current");
        }
    });
});


