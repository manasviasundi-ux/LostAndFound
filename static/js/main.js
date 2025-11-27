// DOM Elements
const uploadForm = document.getElementById('uploadForm');
const itemImage = document.getElementById('itemImage');
const imagePreview = document.getElementById('imagePreview');
const submitBtn = document.getElementById('submitBtn');
const submitText = document.getElementById('submitText');
const submitLoader = document.getElementById('submitLoader');
const resultsSection = document.getElementById('resultsSection');
const resultsContainer = document.getElementById('resultsContainer');
const errorMessage = document.getElementById('errorMessage');

// Image preview handler
itemImage.addEventListener('change', function(e) {
    const file = e.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            imagePreview.innerHTML = `<img src="${e.target.result}" alt="Preview">`;
        };
        reader.readAsDataURL(file);
    } else {
        imagePreview.innerHTML = '';
    }
});

// Form submission handler
uploadForm.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    // Hide previous results and errors
    resultsSection.style.display = 'none';
    errorMessage.style.display = 'none';
    
    // Validate form
    const formData = new FormData(uploadForm);
    const file = itemImage.files[0];
    
    if (!file) {
        showError('Please select an image file.');
        return;
    }
    
    // Show loading state
    submitBtn.disabled = true;
    submitText.textContent = 'Searching...';
    submitLoader.style.display = 'inline-block';
    
    try {
        // Send request to Flask backend
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Display results
            displayResults(data);
        } else {
            // Show error from server
            showError(data.error || 'An error occurred while processing your request.');
        }
    } catch (error) {
        console.error('Error:', error);
        showError('Failed to connect to server. Please try again.');
    } finally {
        // Reset button state
        submitBtn.disabled = false;
        submitText.textContent = 'Search for Matches';
        submitLoader.style.display = 'none';
    }
});

// Display matching results
function displayResults(data) {
    if (!data.matches || data.matches.length === 0) {
        showError('No matches found. Try uploading a different image.');
        return;
    }
    
    resultsContainer.innerHTML = '';
    
    data.matches.forEach((match, index) => {
        const card = document.createElement('div');
        card.className = 'result-card';
        
        const score = (match.similarity * 100).toFixed(1);
        const scoreColor = score > 70 ? '#28a745' : score > 50 ? '#ffc107' : '#667eea';
        
        card.innerHTML = `
            <img src="/uploads/${match.filename}" alt="${match.item_name}" onerror="this.src='data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22200%22 height=%22200%22%3E%3Crect fill=%22%23ddd%22 width=%22200%22 height=%22200%22/%3E%3Ctext fill=%22%23999%22 font-family=%22sans-serif%22 font-size=%2218%22 dy=%2210.5%22 font-weight=%22bold%22 x=%2250%25%22 y=%2250%25%22 text-anchor=%22middle%22%3EImage Not Found%3C/text%3E%3C/svg%3E'">
            <h3>${escapeHtml(match.item_name)}</h3>
            <div class="result-info">
                <strong>Type:</strong> ${match.item_type === 'lost' ? 'Lost' : 'Found'}
            </div>
            <div class="result-info">
                <strong>Color:</strong> ${escapeHtml(match.color)}
            </div>
            <div class="result-info">
                <strong>Location:</strong> ${escapeHtml(match.location)}
            </div>
            <div class="result-info">
                <strong>Date:</strong> ${formatDate(match.date)}
            </div>
            <div class="match-score" style="background: ${scoreColor}">
                ${score}% Match
            </div>
        `;
        
        resultsContainer.appendChild(card);
    });
    
    resultsSection.style.display = 'block';
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// Show error message
function showError(message) {
    errorMessage.textContent = message;
    errorMessage.style.display = 'block';
    errorMessage.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Format date
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric' 
    });
}



