const socket = io.connect(window.location.origin);

// Emit the player's joining event when the page loads
const roomCode = window.location.pathname.split('/').pop();
socket.emit('join_game', { room_code: roomCode, player_id: socket.id });

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
