const socket = io.connect(window.location.origin);

// Listen for timer updates
socket.on('server_timer_update', (data) => {
    const timeLeft = data.time;
    const countdownElement = document.getElementById('countdown');
    countdownElement.textContent = `${timeLeft} seconds left`;
});