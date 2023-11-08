const socket = io.connect();

const problemText = document.getElementById('questionBox');
const answerBoxInput = document.getElementById('answerBox');
const scoreText = document.getElementById('scoreText');
const aliasText = document.getElementById('aliasText');
const countdownElement = document.getElementById('countdown');

// Function to extract query parameter from URL
function getQueryParam(param) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(param);
}

function getPathParameter() {
    const pathSegments = window.location.pathname.split('/');
    return pathSegments[2]; // Assuming 'room_code' is the third segment (index 2)
}

function displayScores(scores) {
    // Get the element with id "scoreText"
    var scoreSectionElement = document.getElementById("scoreSection");

    // Clear any existing content inside the element
    scoreSectionElement.innerHTML = "";

    // Create a table element
    var table = document.createElement("table");
    table.className = "table";

    // Create table header row
    var headerRow = table.createTHead().insertRow();
    var headerCell1 = headerRow.insertCell();
    headerCell1.textContent = "Player Name";
    var headerCell2 = headerRow.insertCell();
    headerCell2.textContent = "Score";

    // Create table body
    var tbody = document.createElement("tbody");

    // Iterate over the scores dictionary and populate the table rows
    for (var playerName in scores) {
        var row = tbody.insertRow();
        var cell1 = row.insertCell();
        cell1.textContent = playerName;
        var cell2 = row.insertCell();
        cell2.textContent = scores[playerName];
    }

    // Append the table body to the table element
    table.appendChild(tbody);

    // Append the table to the scoreSectionElement
    scoreSectionElement.appendChild(table);
}


window.onload = function () {
    answerBoxInput.focus();
    // Extract 'room_code' path parameter from the URL
    window.roomCode = getPathParameter();

    // Extract the 'old_socket_id' query parameter from the URL
    const paramValue = getQueryParam('old_socket_id');

    // Emit the event as soon as the page loads
    socket.emit('client_battle_load', { room_code: window.roomCode, old_socket_id: paramValue });
};

socket.on('server_update_name', (data) => {
    aliasText.innerHTML = data['alias']
})

// Listen for timer updates
socket.on('server_timer_update', (data) => {
    const timeLeft = data.time;
    countdownElement.textContent = `${timeLeft} seconds left`;
});

socket.on('server_generated_problem', (data) => {
    answerBoxInput.value = ''
    problemText.innerHTML = data['problem']
    scoreText.innerHTML = data['score']
})

socket.on('server_game_ended', (data) => {
    answerBoxInput.disabled = true
    countdownElement.style.display = 'none'
    displayScores(data['scores'])
})

answerBoxInput.oninput = function() {
    socket.emit('client_submitted_answer', { room_code: window.roomCode, answer: answerBoxInput.value } )
  };
  