// static/js/feed-validation.js

let urlValidationTimeout;

// Add event listener to URL input for validation
document.addEventListener('DOMContentLoaded', () => {
  const urlInput = document.getElementById('feedUrl');
  const feedTypeSelect = document.getElementById('feedType');

  if (urlInput) {
    urlInput.addEventListener('input', handleUrlChange);
  }

  if (feedTypeSelect) {
    feedTypeSelect.addEventListener('change', () => {
      if (urlInput.value) {
        validateUrl(urlInput.value, feedTypeSelect.value);
      }
    });
  }
});

function handleUrlChange(event) {
  const urlInput = event.target;
  const feedType = document.getElementById('feedType').value;

  // Clear any existing timeout
  if (urlValidationTimeout) {
    clearTimeout(urlValidationTimeout);
  }

  // Remove any existing validation messages
  removeValidationMessage(urlInput);

  // Set new timeout
  urlValidationTimeout = setTimeout(() => {
    if (urlInput.value) {
      validateUrl(urlInput.value, feedType);
    }
  }, 500);
}

async function validateUrl(url, feedType) {
  const urlInput = document.getElementById('feedUrl');
  const submitButton = document.querySelector('button[type="submit"]');

  // Show loading state
  showValidationLoading(urlInput);
  submitButton.disabled = true;

  try {
    const response = await fetch(`/api/v1/feed/validate-url?url=${encodeURIComponent(url)}&feed_type=${feedType}`);
    const data = await response.json();

    if (data.valid) {
      showValidationSuccess(urlInput);
      submitButton.disabled = false;
    } else {
      showValidationError(urlInput, data.error);
      submitButton.disabled = true;
    }
  } catch (error) {
    showValidationError(urlInput, 'Error validating URL');
    submitButton.disabled = true;
  }
}

function showValidationLoading(input) {
  removeValidationMessage(input);

  const loadingDiv = document.createElement('div');
  loadingDiv.className = 'validation-message text-gray-500 text-sm mt-1';
  loadingDiv.innerHTML = `
        <svg class="inline-block animate-spin h-4 w-4 text-gray-500 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
        </svg>
        Validating URL...
    `;

  input.parentNode.appendChild(loadingDiv);
}

function showValidationSuccess(input) {
  removeValidationMessage(input);

  const successDiv = document.createElement('div');
  successDiv.className = 'validation-message text-green-600 text-sm mt-1';
  successDiv.innerHTML = `
        <svg class="inline-block h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
        </svg>
        Valid feed URL
    `;

  input.parentNode.appendChild(successDiv);
  input.classList.remove('border-red-500');
  input.classList.add('border-green-500');
}

function showValidationError(input, message) {
  removeValidationMessage(input);

  const errorDiv = document.createElement('div');
  errorDiv.className = 'validation-message text-red-600 text-sm mt-1';
  errorDiv.innerHTML = `
        <svg class="inline-block h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
        </svg>
        ${message}
    `;

  input.parentNode.appendChild(errorDiv);
  input.classList.remove('border-green-500');
  input.classList.add('border-red-500');
}

function removeValidationMessage(input) {
  // Remove any existing validation messages
  const existingMessage = input.parentNode.querySelector('.validation-message');
  if (existingMessage) {
    existingMessage.remove();
  }

  // Remove validation styles from input
  input.classList.remove('border-red-500', 'border-green-500');
}

// Update the form submission handler to include validation
async function handleFeedSubmit(event) {
  event.preventDefault();

  const form = event.target;
  const submitButton = form.querySelector('button[type="submit"]');
  const loadingSpinner = document.getElementById('loadingSpinner');
  const submitButtonText = document.getElementById('submitButtonText');
  const errorAlert = document.getElementById('errorAlert');
  const errorMessage = document.getElementById('errorMessage');

  // Show loading state
  submitButton.disabled = true;
  loadingSpinner.classList.remove('hidden');
  submitButtonText.classList.add('hidden');
  errorAlert.classList.add('hidden');

  try {
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());

    // Validate URL before submitting
    const validationResponse = await fetch(
      `/api/v1/feed/validate-url?url=${encodeURIComponent(data.url)}&feed_type=${data.feed_type}`
    );
    const validationResult = await validationResponse.json();

    if (!validationResult.valid) {
      throw new Error(validationResult.error || 'Invalid feed URL');
    }

    // Submit the form if validation passes
    const url = currentFeedId
      ? `/api/v1/feed/${currentFeedId}`
      : '/api/v1/feed';

    const response = await fetch(url, {
      method: currentFeedId ? 'PUT' : 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data)
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to save feed');
    }

    // Success - reload page to show updated feeds
    window.location.reload();

  } catch (error) {
    // Show error message
    errorMessage.textContent = error.message;
    errorAlert.classList.remove('hidden');

    // Reset button state
    submitButton.disabled = false;
    loadingSpinner.classList.add('hidden');
    submitButtonText.classList.remove('hidden');
  }
}
