// static/js/feed-management.js

let currentFeedId = null;

// Modal Management
function openModal(title, feed = null) {
  const modal = document.getElementById('feedModal');
  const modalTitle = document.getElementById('modalTitle');

  modalTitle.textContent = title;
  currentFeedId = feed ? feed.id : null;

  // Pre-fill form if editing
  if (feed) {
    document.getElementById('feedName').value = feed.name;
    document.getElementById('feedUrl').value = feed.url;
    document.getElementById('feedCategory').value = feed.category;
    document.getElementById('feedType').value = feed.feed_type;
  } else {
    document.getElementById('feedForm').reset();
  }

  modal.classList.remove('hidden');
}

function closeModal() {
  const modal = document.getElementById('feedModal');
  modal.classList.add('hidden');
  document.getElementById('feedForm').reset();
  document.getElementById('errorAlert').classList.add('hidden');
  currentFeedId = null;
}

// Form Submission
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

// Delete Feed
async function deleteFeed(feedId) {
  if (!confirm('Are you sure you want to delete this feed?')) return;

  try {
    const response = await fetch(`/api/v1/feed/${feedId}`, {
      method: 'DELETE'
    });

    if (!response.ok) {
      throw new Error('Failed to delete feed');
    }

    // Reload page to show updated feed list
    window.location.reload();

  } catch (error) {
    console.error('Error deleting feed:', error);
    alert('Error deleting feed');
  }
}

// Refresh Feed
async function refreshFeed(feedId) {
  const refreshButton = document.querySelector(`button[data-feed-id="${feedId}"]`);
  const originalContent = refreshButton.innerHTML;

  // Show loading state
  refreshButton.disabled = true;
  refreshButton.innerHTML = `
        <svg class="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
        </svg>
    `;

  try {
    const response = await fetch(`/api/v1/feed/refresh/${feedId}`, {
      method: 'POST'
    });

    if (!response.ok) {
      throw new Error('Failed to refresh feed');
    }

    // Show success message
    alert('Feed refreshed successfully');

  } catch (error) {
    console.error('Error refreshing feed:', error);
    alert('Error refreshing feed');
  } finally {
    // Reset button state
    refreshButton.disabled = false;
    refreshButton.innerHTML = originalContent;
  }
}

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
  const feedForm = document.getElementById('feedForm');
  if (feedForm) {
    feedForm.addEventListener('submit', handleFeedSubmit);
  }

  // Close modal when clicking outside
  const modal = document.getElementById('feedModal');
  if (modal) {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        closeModal();
      }
    });
  }
});