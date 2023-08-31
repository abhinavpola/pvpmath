const socket = io.connect(window.location.origin);

const startButton = document.querySelector('#startGame');
const joinButton = document.querySelector('.btn-secondary');
const challengeCodeInput = document.getElementById('challengeCode');

startButton.addEventListener('click', () => {
    console.log('Start Battle clicked');
    socket.emit('start_game');
});

// When the game has started
socket.on('game_started', (data) => {
    const roomCode = data.room_code;
    console.log(`Game has started in room ${roomCode}`);
    // Redirect to the battle room page with the room code
    window.location.href = `/battles/${roomCode}`;
});


joinButton.addEventListener('click', () => {
    const challengeCode = challengeCodeInput.value;
    console.log(`Join Battle clicked with code: ${challengeCode}`);
    // Redirect to the battle room page with the provided code
    window.location.href = `/battles/${challengeCode}`;
});


socket.on('both_players_joined', (data) => {
    const roomCode = data.room_code;
    console.log(`Both players have joined room ${roomCode}. Let the battle begin!`);

    // Start a 60-second countdown timer
    let secondsLeft = 60;
    const countdownElement = document.getElementById('countdown');

    const countdownInterval = setInterval(() => {
        if (secondsLeft <= 0) {
            clearInterval(countdownInterval);
            countdownElement.textContent = "Time's up!";
            // Implement logic to handle end of the game
        } else {
            countdownElement.textContent = `${secondsLeft} seconds left`;
            secondsLeft--;
        }
    }, 1000);
});

// ... (rest of the code) ...
