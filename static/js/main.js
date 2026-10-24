// Feed content is untrusted: escape before putting it into innerHTML
function esc(value) {
  const d = document.createElement('div');
  d.textContent = value == null ? '' : String(value);
  return d.innerHTML.replace(/"/g, '&quot;');
}
function stripTags(html) {
  const d = document.createElement('div');
  d.innerHTML = html || '';
  return d.textContent || '';
}

// static/js/main.js
document.addEventListener('DOMContentLoaded', function () {
  const loadMoreButton = document.getElementById('load-more');

  if (loadMoreButton) {
    loadMoreButton.addEventListener('click', function () {
      const apiUrl = this.getAttribute('data-url');
      const currentPage = parseInt(this.getAttribute('data-page'));

      // Visual feedback that button was clicked
      loadMoreButton.innerText = 'Loading...';
      loadMoreButton.classList.add('opacity-70');

      // Build the URL with proper pagination
      let url = apiUrl;
      if (url.includes('?')) {
        url += '&page=' + currentPage;
      } else {
        url += '?page=' + currentPage;
      }

      // Fetch the next page content
      fetch(url)
        .then(response => {
          if (!response.ok) {
            throw new Error('Network response was not ok');
          }
          return response.json();
        })
        .then(data => {
          // Reset button state
          loadMoreButton.innerText = 'Load More';
          loadMoreButton.classList.remove('opacity-70');

          if (data.results && data.results.length > 0) {
            // Update page counter for next load
            loadMoreButton.setAttribute('data-page', currentPage + 1);

            // Get content container
            const contentContainer = document.getElementById('content-container');

            // Process and append new content
            data.results.forEach(content => {
              const card = createNewsCard(content);
              contentContainer.appendChild(card);
            });

            // If we've reached the end, hide the button
            if (!data.next || data.results.length < 12) {
              loadMoreButton.classList.add('hidden');
            }

            // Scroll a bit to show new content
            window.scrollBy({
              top: 300,
              behavior: 'smooth'
            });
          } else {
            // No more content, hide button
            loadMoreButton.classList.add('hidden');
          }
        })
        .catch(error => {
          console.error('Error loading more content:', error);

          // Reset button and show error
          loadMoreButton.innerText = 'Load More';
          loadMoreButton.classList.remove('opacity-70');

          // Show error toast
          const errorToast = document.createElement('div');
          errorToast.className = 'fixed bottom-4 left-1/2 transform -translate-x-1/2 bg-red-500 text-white px-4 py-2 rounded shadow-lg';
          errorToast.textContent = 'Failed to load more content. Please try again.';
          document.body.appendChild(errorToast);

          // Remove error message after 3 seconds
          setTimeout(() => {
            errorToast.classList.add('opacity-0');
            errorToast.style.transition = 'opacity 0.5s ease';
            setTimeout(() => errorToast.remove(), 500);
          }, 3000);
        });
    });
  }

  // Function to create a news card from content data
  function createNewsCard(content) {
    const card = document.createElement('div');
    card.className = 'bg-white rounded-lg shadow-md overflow-hidden transition-transform duration-300 hover:shadow-xl hover:-translate-y-1';

    let cardImage = '';
    if (content.image_url) {
      cardImage = `<img src="${content.image_url}" alt="${esc(content.title)}" class="absolute h-full w-full object-cover">`;
    } else {
      cardImage = `
        <div class="absolute h-full w-full bg-gray-200 flex items-center justify-center">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-16 w-16 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
        </div>
      `;
    }

    let videoOverlay = '';
    if (content.content_type === 'video') {
      videoOverlay = `
        <div class="absolute inset-0 flex items-center justify-center">
          <div class="bg-black bg-opacity-50 rounded-full p-3">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
        </div>
      `;
    }

    const categoryBadge = content.category ?
      `<span class="bg-blue-600 text-white text-xs font-semibold px-2 py-1 rounded">${content.category}</span>` :
      `<span class="bg-blue-600 text-white text-xs font-semibold px-2 py-1 rounded">General</span>`;

    const pubDate = new Date(content.published_date);
    const formattedDate = pubDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });

    card.innerHTML = `
      <div class="relative pb-48">
        ${cardImage}
        ${videoOverlay}
        <div class="absolute top-0 right-0 m-2">
          ${categoryBadge}
        </div>
      </div>
      <div class="p-4">
        <div class="flex items-center text-xs text-gray-500 mb-2">
          <span class="mr-2">${esc(content.source_name || 'Unknown Source')}</span>
          <span>${formattedDate}</span>
        </div>
        <h3 class="font-bold text-lg mb-2 line-clamp-2 h-14">${esc(content.title)}</h3>
        <p class="text-gray-600 text-sm line-clamp-3 h-14 mb-4">${esc(content.ai_summary || stripTags(content.description))}</p>
        <a href="${esc(content.url)}" target="_blank" class="text-blue-600 hover:text-blue-800 text-sm font-medium inline-flex items-center">
          Read more
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 ml-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3" />
          </svg>
        </a>
      </div>
    `;

    return card;
  }
  // Handle dark mode toggle if implemented
  const darkModeToggle = document.getElementById('dark-mode-toggle');
  if (darkModeToggle) {
    darkModeToggle.addEventListener('click', function () {
      document.documentElement.classList.toggle('dark');

      // Save preference to localStorage
      if (document.documentElement.classList.contains('dark')) {
        localStorage.setItem('darkMode', 'enabled');
      } else {
        localStorage.setItem('darkMode', 'disabled');
      }
    });

    // Check for saved dark mode preference
    if (localStorage.getItem('darkMode') === 'enabled') {
      document.documentElement.classList.add('dark');
    }
  }
});
