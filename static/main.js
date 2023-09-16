const socket = io.connect(window.location.origin);

// HTML Inputs
const startButton = document.querySelector('#startGame');
const joinButton = document.querySelector('#joinGame');
const challengeCodeInput = document.getElementById('challengeCode');
const waitingSpinner = document.getElementById('waitingSpinner');

startButton.addEventListener('click', () => {
    console.log('Start Battle clicked');
    socket.emit('client_start_game');
});

joinButton.addEventListener('click', () => {
    const challengeCode = challengeCodeInput.value;
    console.log(`Join Battle clicked with code: ${challengeCode}`);
    socket.emit('client_join_game', { room_code: challengeCode });
});

// Receiving room code from server
socket.on('server_room_created', (data) => {
    const roomCode = data.room_code;
    console.log(`Room ${roomCode} created`);
    challengeCodeInput.value = roomCode;
});

// Player 1 joined, waiting for player 2
socket.on('server_waiting_for_next_player', () => {
    waitingSpinner.removeAttribute("hidden");
})

// Both players joined, redirect to /battles
socket.on('server_both_players_joined', (data) => {
    const roomCode = data.room_code;
    console.log(`Both players have joined room ${roomCode}. Let the battle begin!`);
    // Redirect to the battle room page with the valid room code
    window.location.href = `/battles/${roomCode}?old_socket_id=${socket.id}`;
});

// Invalid room code
socket.on('server_invalid_room', (data) => {
    const errorMessage = data.message;
    alert(errorMessage); // Display an alert dialog with the error message
});
