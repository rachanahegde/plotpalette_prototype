// BUILD STORYBOARD FUNCTIONALITY

document.addEventListener('DOMContentLoaded', function () {
    var el = document.getElementById('storyboard');
    displayStoryboardData(); // Load storyboard from local storage

    // Get the writing project's title from local storage to display on page
    var details = store.get('storyboardDetails');
    if(details && details.title) {
        document.getElementById('storyboardTitle').textContent = 'Storyboard for ' + details.title;
    }

    // Access data for debugging purposes - feel free to delete next two lines of code later :)
    const dataCheck = store.get('storyboardData');
    console.log(dataCheck);

    // Drag and drop scene divs using SortableJS https://github.com/SortableJS/Sortable
    Sortable.create(el, {
        animation: 150, // ms, animation speed moving items when sorting, `0` — without animation
        ghostClass: 'sortable-ghost', // Class name for the drop placeholder
        dragClass: "sortable-drag", // Class name for the dragging item
        onEnd: function() {
            saveStoryboardData();  // Save the new order of scenes after an item is placed in a new position
        }
    });

    // Delete scene divs by checking for clicks on the storyboard div (using event delegation)
    document.getElementById('storyboard').addEventListener('click', function(e) {
        // Check if the clicked element is a delete button
        if (e.target.classList.contains('delete-scene-btn')) {
            // Find the parent scene div and remove it
            var sceneCard = e.target.closest('.scene-div');
            if (sceneCard) {
                sceneCard.remove();
                saveStoryboardData();  // Update localStorage after deleting a scene
            }
        }
    });

    document.getElementById('storyboard').addEventListener('click', function(event) {
        if (event.target.classList.contains('upload-img-btn')) {
            event.preventDefault();
            event.stopPropagation();

            const button = event.target;
            const fileInput = document.createElement('input');
            fileInput.type = 'file';
            fileInput.accept = 'image/*';
            fileInput.style.display = 'none';
            document.body.appendChild(fileInput);

            fileInput.onchange = e => {
                const file = e.target.files[0];
                const fileReader = new FileReader();
                fileReader.onload = function(e) {
                    const img = button.previousElementSibling;
                    img.src = e.target.result;
                    saveStoryboardData();
                };
                fileReader.readAsDataURL(file);
            };
            fileInput.click();
            document.body.removeChild(fileInput);
        }
    });

});

// Create the scene div
// Pass in scene data object as a function parameter
function createSceneDiv(data = { title: 'Enter Scene Title', imgSource: './static/img/big_park.jpg', description: 'Click here to enter description...' }) {
    const sceneDiv = document.createElement("div");
    sceneDiv.classList.add("scene-div");

    // Create scene title
    const sceneTitle = document.createElement("div");
    sceneTitle.classList.add("scene-title", "draggable");
    const sceneTitlePara = document.createElement("p");
    sceneTitlePara.classList.add("editable");
    sceneTitlePara.setAttribute("contenteditable", "false");
    sceneTitlePara.textContent = data.title; // Placeholder title from the data object
    sceneTitle.appendChild(sceneTitlePara);

    // Create scene image div
    const sceneImgDiv = document.createElement("div");
    sceneImgDiv.classList.add("scene-img", "draggable");
    const img = document.createElement("img");
    img.src = data.imgSource; // Placeholder image of a park from the data object
    sceneImgDiv.appendChild(img);

    // Create upload image button
    const uploadImgBtn = document.createElement("button");
    uploadImgBtn.textContent = "Upload Image";
    uploadImgBtn.classList.add("upload-img-btn");
    sceneImgDiv.appendChild(uploadImgBtn);

    // Create scene description text
    const sceneText = document.createElement("div");
    sceneText.classList.add("draggable", "scene-text");
    const sceneTextP = document.createElement("p");
    sceneTextP.classList.add("editable");
    sceneTextP.setAttribute("contenteditable", "false");
    sceneTextP.textContent = data.description // Placeholder scene description from data object
    sceneText.appendChild(sceneTextP);

    // Create the delete button
    const deleteBtn = document.createElement("button");
    deleteBtn.classList.add("delete-scene-btn");
    deleteBtn.textContent = "Delete Scene";

    // Append the sceneTitle, sceneImgDiv, sceneText, and deleteBtn elements to the sceneDiv
    sceneDiv.appendChild(sceneTitle);
    sceneDiv.appendChild(sceneImgDiv);
    sceneDiv.appendChild(sceneText);
    sceneDiv.appendChild(deleteBtn);

    return sceneDiv;
}

// Add scene when user clicks on add scene btn
document.getElementById('add-scene-btn').addEventListener('click', function() {
    const newSceneDiv = createSceneDiv();
    document.getElementById('storyboard').appendChild(newSceneDiv);

    // Encourage the user to start editing the scene description by focusing on it & making it editable.
    const newDescription = newSceneDiv.querySelector('.scene-text p');
    newDescription.setAttribute('contenteditable', 'true');
    newDescription.focus();

    saveStoryboardData();  // Save changes to storyboard
});

// Edit scene title and scene description text
document.addEventListener('click', function(e) {
    // Check if the element can be edited
    if (e.target.classList.contains('editable')) {
        // Make the element editable
        e.target.setAttribute('contenteditable', 'true');
        e.target.setAttribute('id', 'edit-text');
        e.target.focus();
    }
});

document.addEventListener('keydown', function(e) {
    // Save changes when user presses the Enter key
    if (e.key === 'Enter') {
        e.preventDefault();
        if (document.activeElement.classList.contains('editable')) {
            document.activeElement.setAttribute('contenteditable', 'false');
            document.activeElement.blur();
            saveStoryboardData();  // Save changes to storyboard
        }
    }
});

document.addEventListener('blur', function(e) {
    // Save changes when user clicks outside
    if (e.target.classList.contains('editable')) {
        // Disable editing
        e.target.setAttribute('contenteditable', 'false');
        e.target.removeAttribute('id');
        saveStoryboardData();  // Save changes to storyboard
    }
}, true);

// Save changes to text and image data in storyboard using StoreJS
function saveStoryboardData() {
    const scenes = document.querySelectorAll('.scene-div');  // Select all scene-div elements
    // Convert NodeList into an array
    const storyboardData = Array.from(scenes).map(scene => {
        return {
            // Create new object containing scene title, image, and description properties
            title: scene.querySelector('.scene-title p').textContent,
            imgSource: scene.querySelector('.scene-img img').src,
            description: scene.querySelector('.scene-text p').textContent
        };
    });

    // Store array of scene objects under the key 'storyboardData'
    store.set('storyboardData', storyboardData);
}


// Display data from local storage
function displayStoryboardData() {
    const storyboardData = store.get('storyboardData');
    if (storyboardData) {
        document.getElementById('storyboard').innerHTML = '';  // Delete content on storyboard
        // Loop through the storyboard array and
        storyboardData.forEach(data => {
            const sceneDiv = createSceneDiv(data);
            document.getElementById('storyboard').appendChild(sceneDiv);  // Add new scene to the page
        });
    }
}


// Send storyboard data to the server/flask backend to use it to prompt GPT-4
function sendStoryboardToServer() {
    const storyboardData = store.get('storyboardData');
    const genre = document.getElementById('genre').value;
    const themes = document.getElementById('themes').value;
    const setting = document.getElementById('setting').value;
    const premise = document.getElementById('premise').value;

    // Remove scenes that contain the placeholder description before sending them to the backend
    const filteredStoryboardData = storyboardData.filter(scene => scene.description !== "Enter description here...");

    const requestBody = {
        storyboard: filteredStoryboardData,
        form_action: 'generate_ideas',
        genre: genre,
        themes: themes,
        setting: setting,
        premise: premise
    };

    fetch('/process_storyboard', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody)
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            console.error('Server Error:', data.error);
            document.getElementById('error-message').textContent = data.error;
            document.getElementById('error-message').style.display = 'block';
        } else {
            displayPlotIdeasWithImages(data.plotIdeas);
        }
    })
    .catch(error => {
        console.error('Fetch Error:', error);
        document.getElementById('error-message').textContent = 'Error fetching data. Please try again.';
        document.getElementById('error-message').style.display = 'block';
    });
}


document.getElementById('generate-ideas-btn').addEventListener('click', function(event) {
    console.log("Button clicked, event listener triggered.");  // Debugging
    event.preventDefault();
    sendStoryboardToServer();
});


function displayPlotIdeasWithImages(plotIdeas) {
    const ideasDisplay = document.getElementById('plot_ideas_display');
    ideasDisplay.innerHTML = '';
    plotIdeas.forEach(idea => {
        const ideaCard = document.createElement('div');
        ideaCard.className = 'idea-card';
        ideaCard.innerHTML = `
            <div class="idea-title"><p>${idea.title}</p></div>
            <div class="idea-content"><p>${idea.description}</p></div>
            <img src="${idea.image_url}" alt="Image for ${idea.title}" style="width:100%;">
            <button class="add-to-storyboard-btn">Add to Storyboard</button>`;
        ideasDisplay.appendChild(ideaCard);

        ideaCard.querySelector('.add-to-storyboard-btn').addEventListener('click', function() {
            addToStoryboard(idea);
        });
    });
}

/* Note - The below function WORKS correctly but does NOT store image data in local storage */
function addToStoryboard(idea) {
    const data = {
        title: idea.title,
        imgSource: idea.image_url,
        description: idea.description
    };
    const newSceneDiv = createSceneDiv(data);
    document.getElementById('storyboard').appendChild(newSceneDiv);
    saveStoryboardData();
}


/* Five act structure modelled on this: https://www.masterclass.com/articles/five-act-structure */
function addFiveActStructure() {
    const acts = [
        { title: "Act I: The Exposition", description: "Introduce main characters and central conflict through inciting incident." },
        { title: "Act II: The Rising Action", description: "Increase the conflict as character pursue their goals." },
        { title: "Act III: The Climax", description: "The turning point of the story where the tension peaks." },
        { title: "Act IV: The Falling Action", description: "Events that lead to the resolution of the conflict." },
        { title: "Act V: The Resolution", description: "The story ends with all conflicts resolved and loose ends tied up." }
    ];

    acts.forEach(act => {
        const sceneDiv = createSceneDiv({
            title: act.title,
            imgSource: './static/img/big_park.jpg',
            description: act.description
        });
        document.getElementById('storyboard').appendChild(sceneDiv);
    });

    saveStoryboardData();
}

/* The 12 stages of the hero's journey (taken from: https://www.grammarly.com/blog/heros-journey/) */
const heroJourneyStages = [
    { title: "The Call to Adventure", description: "The hero receives the call to adventure (i.e. through a dream)." },
    { title: "Refusal of the Call", description: "The hero initially refuses the call to adventure due to fear or insecurity." },
    { title: "Meeting the Mentor", description: "The hero encounters a mentor who provides advice and guidance." },
    { title: "Crossing the Threshold", description: "The hero leaves behind the known world and crosses the threshold into the unknown, often encountering tests, trials, and challenges along the way." },
    { title: "Tests, Allies, and Enemies", description: "The hero faces tests, finds allies, and meets enemies." },
    { title: "Approach to the Inmost Cave", description: "The hero approaches the innermost cave or the heart of darkness, often facing their greatest fears and challenges." },
    { title: "The Ordeal", description: "The hero faces their greatest challenge." },
    { title: "The Reward", description: "The hero receives a reward (i.e. knowledge or powerful object) to aid them on their journey." },
    { title: "The Road Back", description: "The hero begins the journey back to their ordinary life, encountering new challenges/obstacles on the way." },
    { title: "The Resurrection", description: "The hero experiences a moment of death and rebirth, often symbolized by a physical or metaphorical transformation." },
    { title: "The Return", description: "The hero returns home transformed and shares their newfound wisdom." },
    { title: "The Freedom to Live", description: "The hero achieves a state of freedom and enlightenment, often living happily ever after." }
];

function addHeroJourneyTemplate() {
    heroJourneyStages.forEach(stage => {
        const sceneDiv = createSceneDiv({
            title: stage.title,
            imgSource: './static/img/big_park.jpg',
            description: stage.description
        });
        document.getElementById('storyboard').appendChild(sceneDiv);
    });

    saveStoryboardData();
}

document.getElementById('add-five-act-structure-btn').addEventListener('click', addFiveActStructure);
document.getElementById('add-hero-journey-btn').addEventListener('click', addHeroJourneyTemplate);

