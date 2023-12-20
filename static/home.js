function updateSliderValue(value) {
    document.getElementById('sliderValue').textContent = value;
}

// Function to clear the challengeCode input
function clearChallengeCode() {
    document.getElementById('challengeCode').value = '';
}

// Event listener for number of players select
document.getElementById('numPlayers').addEventListener('change', function () {
    clearChallengeCode();
});

// Event listener for game duration slider
document.getElementById('gameDuration').addEventListener('input', function () {
    clearChallengeCode();
    // You can also update the selected duration text if needed
    document.getElementById('sliderValue').textContent = this.value;
});

document.addEventListener('DOMContentLoaded', function () {
    // Function to get URL parameter by name
    function getURLParameter(name) {
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get(name);
    }

    // Get the value of the "roomcode" parameter from the URL
    const roomCodeFromURL = getURLParameter('roomcode');

    // Set the value of the challengeCode input if roomCodeFromURL is not null
    if (roomCodeFromURL !== null) {
        document.getElementById('challengeCode').value = roomCodeFromURL;
    }
});

// Event listener for the copy button
document.getElementById('copyButton').addEventListener('click', function () {
    const challengeCodeInput = document.getElementById('challengeCode');

    // Combine existing text with additional text
    const textToCopy = `${window.origin}/battles?roomcode=${challengeCodeInput.value}`;

    // Create a temporary textarea element to copy text to clipboard
    const tempTextarea = document.createElement('textarea');
    tempTextarea.value = textToCopy;
    document.body.appendChild(tempTextarea);

    // Select the text in the textarea
    tempTextarea.select();
    tempTextarea.setSelectionRange(0, 99999); // For mobile devices

    if (navigator.share) {
        navigator.share({
            title: 'Share Challenge Link',
            text: textToCopy,
        })
            .then(() => console.log('Shared successfully'))
            .catch((error) => console.error('Error sharing:', error));
    } else {
        // Copy the text to the clipboard
        navigator.clipboard.writeText(textToCopy)
            .then(() => {
                console.log('Text copied to clipboard:', textToCopy);
                document.getElementById('copyButton').innerText = 'Copied';
                setTimeout(() => {
                    document.getElementById('copyButton').innerText = 'Share';
                }, 2000); // Reset the button text after 2 seconds
            })
            .catch((error) => {
                console.error('Error copying to clipboard:', error);
                // Fallback for browsers that do not support navigator.clipboard.writeText
                // Display an alert for the user to copy manually
                alert('Text copied to clipboard: ' + textToCopy);
            });
    }
    // Remove the temporary textarea
    document.body.removeChild(tempTextarea);
});