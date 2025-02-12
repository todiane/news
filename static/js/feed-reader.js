let currentFilters = {
  contentType: 'all',
  category: 'all',
  search: '',
  readStatus: 'all',
  page: 1
};
function toggleDropdown(dropdownId) {
  const dropdown = document.getElementById(dropdownId);
  const allDropdowns = document.querySelectorAll('[id$="Dropdown"]');

  // Hide all other dropdowns
  allDropdowns.forEach(d => {
    if (d.id !== dropdownId) d.classList.add('hidden');
  });

  // Toggle current dropdown
  dropdown.classList.toggle('hidden');
}

function filterContent(type) {
  currentFilters.contentType = type;
  currentFilters.page = 1;
  document.getElementById('selectedContentType').textContent =
    type === 'all' ? 'All Content' :
      type === 'articles' ? 'Articles Only' : 'Videos Only';
  fetchContent();
  toggleDropdown('contentTypeDropdown');
}

function filterCategory(category) {
  currentFilters.category = category;
  currentFilters.page = 1;
  document.getElementById('selectedCategory').textContent =
    category === 'all' ? 'All Categories' : category.charAt(0).toUpperCase() + category.slice(1);
  fetchContent();
  toggleDropdown('categoryDropdown');
}
function filterReadStatus(status) {
  currentFilters.readStatus = status;
  currentFilters.page = 1;
  document.getElementById('selectedReadStatus').textContent =
    status === 'all' ? 'All Items' :
      status === 'unread' ? 'Unread Only' :
        status === 'read' ? 'Read Only' : 'In Progress';
  fetchContent();
  toggleDropdown('readStatusDropdown');
}

let searchTimeout;
function handleSearch(event) {
  clearTimeout(searchTimeout);
  searchTimeout = setTimeout(() => {
    currentFilters.search = event.target.value;
    currentFilters.page = 1;
    fetchContent();
  }, 300);
}

function changePage(direction) {
  if (direction === 'prev' && currentFilters.page > 1) {
    currentFilters.page--;
  } else if (direction === 'next' && currentFilters.page < totalPages) {
    currentFilters.page++;
  }
  fetchContent();
}

async function fetchContent() {
  const contentGrid = document.getElementById('contentGrid');
  // Show loading state
  contentGrid.innerHTML = `
  <div class="col-span-full text-center py-12">
    <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
    <p class="text-gray-500 mt-4">Loading content...</p>
  </div>
  `;

  try {
    const queryParams = new URLSearchParams({
      content_type: currentFilters.contentType,
      category: currentFilters.category,
      search: currentFilters.search,
      read_status: currentFilters.readStatus,
      page: currentFilters.page
    });

    const response = await fetch(`/api/v1/reader?${queryParams}`);
    const data = await response.json();

    if (response.ok) {
      // Update pagination info
      totalPages = data.total_pages;
      document.querySelector('nav span').textContent =
        `Page ${currentFilters.page} of ${totalPages}`;

      // Update content grid
      contentGrid.innerHTML = data.items.map(item => `
  ${item.api_source === 'youtube' ? renderVideoCard(item) : renderArticleCard(item)}
  `).join('');
    } else {
      throw new Error(data.detail || 'Error fetching content');
    }
  } catch (error) {
    contentGrid.innerHTML = `
            <div class="col-span-full text-center py-12">
                <svg class="h-12 w-12 text-red-500 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                          d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <h3 class="text-xl text-gray-600 mt-4">Error loading content</h3>
                <p class="text-gray-500 mt-2">${error.message}</p>
            </div>
        `;
  }
}
function renderVideoCard(video) {
  const readStatus = video.read_status || {};
  const isRead = readStatus.read_at ? true : false;
  const readProgress = readStatus.last_position || 0;

  return `
  <div class="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow duration-300 ${isRead ? 'opacity-75' : ''}">
    <div class="relative">
      <img src="${video.metadata.thumbnail}"
        alt="${video.title}"
        class="w-full h-48 object-cover">
        <!-- Read Status Indicator -->
        <div class="absolute top-2 right-2 z-10">
          ${isRead ?
      `<span class="bg-green-500 text-white text-xs px-2 py-1 rounded-full">
                            Read
                        </span>` :
      `<span class="bg-blue-500 text-white text-xs px-2 py-1 rounded-full">
                            New
                        </span>`
    }
        </div>
        <!-- Progress Bar -->
        ${readProgress > 0 && !isRead ?
      `<div class="absolute bottom-0 left-0 w-full h-1 bg-gray-200">
                        <div class="h-full bg-blue-500" style="width: ${readProgress * 100}%"></div>
                    </div>` : ''
    }
        <!-- Rest of the video card content stays the same -->
        <div class="absolute inset-0 flex items-center justify-center">
          <!-- ... existing button code ... -->
        </div>
    </div>
    <div class="p-4">
      <!-- ... rest of the existing code ... -->
    </div>
  </div>
  `;
}

function renderArticleCard(article) {
  const readStatus = article.read_status || {};
  const isRead = readStatus.read_at ? true : false;
  const readProgress = readStatus.last_position || 0;

  return `
  <div class="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow duration-300 ${isRead ? 'opacity-75' : ''}"
    data-article-id="${article.id}">
    <div class="p-6">
      <div class="flex justify-between items-start">
        <div class="flex-1">
          <h3 class="text-xl font-semibold text-gray-900">${article.title}</h3>
        </div>
        <!-- Read Status Controls -->
        <div class="flex items-center space-x-2 ml-4">
          <button onclick="toggleReadStatus('${article.id}', ${isRead})"
            class="group relative">
            ${isRead ?
      `<svg class="h-6 w-6 text-green-500 hover:text-gray-500" fill="currentColor" viewBox="0 0 20 20">
                                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
                                </svg>` :
      `<svg class="h-6 w-6 text-gray-400 hover:text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                                </svg>`
    }
            <!-- Tooltip -->
            <span class="hidden group-hover:block absolute z-10 -top-10 left-1/2 transform -translate-x-1/2 px-2 py-1 bg-gray-900 text-white text-xs rounded whitespace-nowrap">
              ${isRead ? 'Mark as unread' : 'Mark as read'}
            </span>
          </button>
        </div>
      </div>
      <p class="text-gray-600 mt-2">${article.content.substring(0, 200)}...</p>

      <!-- Progress Bar -->
      ${readProgress > 0 && !isRead ?
      `<div class="mt-4 w-full h-1 bg-gray-200 rounded">
                        <div class="h-full bg-blue-500 rounded" style="width: ${readProgress * 100}%"></div>
                    </div>
                    <p class="text-xs text-gray-500 mt-1">Progress: ${Math.round(readProgress * 100)}%</p>` : ''
    }

      <div class="flex justify-between items-center mt-4">
        <a href="${article.url}"
          class="text-blue-500 hover:text-blue-700 font-medium"
          target="_blank"
          rel="noopener noreferrer"
          onclick="initReadingTracking('${article.id}'); markArticleOpened('${article.id}')">
          Read more →
        </a>
        <span class="text-sm text-gray-500">${formatDate(article.published_date)}</span>
      </div>
    </div>
  </div>
  `;
}

function formatDate(dateString) {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  });
}

// Handle clicks outside dropdowns
document.addEventListener('click', function (event) {
  if (!event.target.closest('[id$="Btn"]')) {
    document.querySelectorAll('[id$="Dropdown"]').forEach(dropdown => {
      dropdown.classList.add('hidden');
    });
  }
});

// Initial content load
fetchContent();

function markArticleOpened(articleId) {
  // Record when an article is opened
  fetch(`/api/v1/feed-history/${articleId}/progress`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      position: 0,
      duration: 0
    })
  }).catch(error => console.error('Error marking article as opened:', error));
}

// Reading tracking state
const readingTracker = {
  startTime: null,
  articleId: null,
  scrollDebounce: null,
  lastPosition: 0,
  isReading: false,
  updateInterval: null
};

// Initialize reading tracking when an article is opened
function initReadingTracking(articleId) {
  // Clear any existing tracking
  stopReadingTracking();

  readingTracker.articleId = articleId;
  readingTracker.startTime = Date.now();
  readingTracker.isReading = true;

  // Start periodic updates
  readingTracker.updateInterval = setInterval(() => {
    if (readingTracker.isReading) {
      updateReadingProgress();
    }
  }, 30000); // Update every 30 seconds

  // Add scroll listener
  window.addEventListener('scroll', handleScroll);

  // Add visibility change listener
  document.addEventListener('visibilitychange', handleVisibilityChange);
}

// Handle scroll events with debouncing
function handleScroll() {
  if (!readingTracker.isReading) return;

  clearTimeout(readingTracker.scrollDebounce);
  readingTracker.scrollDebounce = setTimeout(() => {
    const scrollPosition = calculateReadingPosition();
    if (scrollPosition !== readingTracker.lastPosition) {
      readingTracker.lastPosition = scrollPosition;
      updateReadingProgress();
    }
  }, 500); // Debounce scroll events to 500ms
}

// Calculate reading position based on scroll
function calculateReadingPosition() {
  const article = document.querySelector('.article-content');
  if (!article) return 0;

  const rect = article.getBoundingClientRect();
  const windowHeight = window.innerHeight;
  const articleHeight = article.scrollHeight;

  // Calculate percentage through content
  let position = Math.max(0, -rect.top) / (articleHeight - windowHeight);
  return Math.min(1, Math.max(0, position));
}

// Handle tab visibility changes
function handleVisibilityChange() {
  if (document.hidden) {
    // User switched away from the tab
    updateReadingProgress();
  } else {
    // User returned to the tab
    readingTracker.startTime = Date.now();
  }
}

// Update reading progress to the server
async function updateReadingProgress() {
  if (!readingTracker.articleId || !readingTracker.isReading) return;

  const duration = Math.floor((Date.now() - readingTracker.startTime) / 1000);
  const position = readingTracker.lastPosition;

  try {
    const response = await fetch(`/api/v1/feed-history/${readingTracker.articleId}/progress`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        position: position,
        duration: duration
      })
    });

    if (!response.ok) {
      throw new Error('Failed to update reading progress');
    }
  } catch (error) {
    console.error('Error updating reading progress:', error);
  }
}

// Stop tracking reading progress
function stopReadingTracking() {
  if (readingTracker.isReading) {
    // Send final update
    updateReadingProgress();

    // Clear tracking state
    readingTracker.isReading = false;
    readingTracker.articleId = null;
    readingTracker.startTime = null;
    readingTracker.lastPosition = 0;

    // Clear intervals and listeners
    clearInterval(readingTracker.updateInterval);
    window.removeEventListener('scroll', handleScroll);
    document.removeEventListener('visibilitychange', handleVisibilityChange);
  }
}
// Function to toggle read status
async function toggleReadStatus(articleId, currentStatus) {
  try {
    const endpoint = `/api/v1/feed-history/${articleId}/${currentStatus ? 'mark-unread' : 'mark-read'}`;
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      throw new Error('Failed to update read status');
    }

    // Update UI without refreshing the whole list
    const card = document.querySelector(`[data-article-id="${articleId}"]`);
    if (card) {
      if (currentStatus) {
        // Marking as unread
        card.classList.remove('opacity-75');
        card.querySelector('svg').outerHTML = `
  <svg class="h-6 w-6 text-gray-400 hover:text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>`;
      } else {
        // Marking as read
        card.classList.add('opacity-75');
        card.querySelector('svg').outerHTML = `
  <svg class="h-6 w-6 text-green-500 hover:text-gray-500" fill="currentColor" viewBox="0 0 20 20">
    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
  </svg>`;
      }
    }

    // Show a brief success message
    showNotification(`Article marked as ${currentStatus ? 'unread' : 'read'}`);

  } catch (error) {
    console.error('Error toggling read status:', error);
    showNotification('Failed to update read status', 'error');
  }
}

// Function to show notifications
function showNotification(message, type = 'success') {
  const notification = document.createElement('div');
  notification.className = `fixed bottom-4 right-4 px-4 py-2 rounded-lg text-white ${type === 'success' ? 'bg-green-500' : 'bg-red-500'
    } transition-opacity duration-300`;
  notification.textContent = message;

  document.body.appendChild(notification);

  // Fade out and remove after 3 seconds
  setTimeout(() => {
    notification.style.opacity = '0';
    setTimeout(() => {
      notification.remove();
    }, 300);
  }, 3000);
}
