// IMAGE GENERATION PAGE FUNCTIONALITY

// Create Toggleable Tabs - modified code from w3schools
function openTab(evt, tabName) {
    // Declare variables
    var i, tabcontent, tablinks;

    // Get all elements with class="tabcontent" and hide them
    tabcontent = document.getElementsByClassName("tabcontent");
    for (i = 0; i < tabcontent.length; i++) {
        tabcontent[i].style.display = "none";
    }

    // Get all elements with class="tablinks" and remove the class "active"
    tablinks = document.getElementsByClassName("tablinks");
    for (i = 0; i < tablinks.length; i++) {
        tablinks[i].className = tablinks[i].className.replace(" active", "");
    }

    // Show the current tab
    document.getElementById(tabName).style.display = "block";

    // Add an "active" class to the button that opened the tab
    if (evt.currentTarget) {
        evt.currentTarget.className += " active";
    }

    localStorage.setItem('selectedTab', tabName);
}


window.onload = function() {
    var selectedTab = localStorage.getItem('selectedTab');
    if (selectedTab) {
        var evt = new Event('click');
        openTab(evt, selectedTab);
    }
};


// Switch tabs when user clicks on the 'Next' button
function clickNextTab() {
    const currentTab = document.querySelector('.tablinks.active');

    let nextTab;
    if (currentTab.textContent.trim() === 'Create Character') {
        nextTab = document.querySelector('button[onclick="openTab(event, \'CreateScene\')"]');
    }

    if (nextTab) {
        nextTab.click();
    }
}

// Add event listener to all the Next buttons
const nextButtons = document.getElementsByClassName('nextTabBtn');
for (let i = 0; i < nextButtons.length; i++) {
    nextButtons[i].addEventListener('click', clickNextTab);
}
