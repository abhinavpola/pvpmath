const socket = io.connect(window.location.origin);

const problemText = document.getElementById('questionBox');
const answerBoxInput = document.getElementById('answerBox');

// Function to extract query parameter from URL
function getQueryParam(param) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(param);
}

function getPathParameter() {
    const pathSegments = window.location.pathname.split('/');
    return pathSegments[2]; // Assuming 'room_code' is the third segment (index 2)
}

window.onload = function () {
    answerBoxInput.focus();
    // Extract 'room_code' path parameter from the URL
    const roomCode = getPathParameter();

    // Extract the 'old_socket_id' query parameter from the URL
    const paramValue = getQueryParam('old_socket_id');

    // Emit the event as soon as the page loads
    socket.emit('client_battle_load', { room_code: roomCode, old_socket_id: paramValue });
};

// Listen for timer updates
socket.on('server_timer_update', (data) => {
    const timeLeft = data.time;
    const countdownElement = document.getElementById('countdown');
    countdownElement.textContent = `${timeLeft} seconds left`;
});

socket.on('server_generated_problem', (data) => {
    problemText.innerHTML = data['problem']
})

socket.on('server_hello', (data) => {
    console.log(data)
})

answerBoxInput.oninput = function() {
    console.log("answer changing to " + answerBoxInput.value);
  };
  