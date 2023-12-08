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

function displayScores(scores, percentiles) {
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
    const scoresArray = Object.entries(scores);
    scoresArray.sort((a, b) => b[1] - a[1]);

    scoresArray.forEach(([playerName, score]) => {
        var row = tbody.insertRow();
        var cell1 = row.insertCell();
        cell1.textContent = playerName;
        var cell2 = row.insertCell();
        cell2.textContent = score;
        var cell3 = row.insertCell();
        cell3.textContent = percentiles[playerName];
    });

    // Append the table body to the table element
    table.appendChild(tbody);

    // Append the table to the scoreSectionElement
    scoreSectionElement.appendChild(table);
}


window.onload = function () {
    answerBoxInput.focus();

    window.roomCode = getQueryParam('roomcode')
    window.playerName = getQueryParam('playername')

    // Emit the event as soon as the page loads
    socket.emit('client_battle_load', { room_code: window.roomCode, player_name: window.playerName });
};

socket.on('server_start_timer', (data) => {
    const timeLimit = data.time_limit; // in seconds
    let timeLeft = timeLimit; // initial time left

    // Function to update the countdown text
    function updateCountdown() {
        countdownElement.textContent = `${timeLeft} seconds left`;

        // Check if time has run out
        if (timeLeft <= 0) {
            clearInterval(timerInterval);
            // Additional logic when the timer reaches zero
            console.log("game timer has ended!")
            socket.emit('client_time_ended', { room_code: window.roomCode })
        } else {
            timeLeft--; // decrease time left
        }
    }

    // Initial update
    updateCountdown();

    // Start the timer
    const timerInterval = setInterval(updateCountdown, 1000); // update every 1000ms (1 second)
});


socket.on('server_generated_problem', (data) => {
    answerBoxInput.value = ''
    problemText.innerHTML = data['problem']
    scoreText.innerHTML = data['score']
})

socket.on('server_game_ended', (data) => {
    answerBoxInput.disabled = true
    countdownElement.style.display = 'none'
    displayScores(data['scores'], data['percentiles'])
})

answerBoxInput.oninput = function() {
    socket.emit('client_submitted_answer', { room_code: window.roomCode, answer: answerBoxInput.value } )
  };
  