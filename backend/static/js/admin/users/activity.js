//javascript for user activity
document.addEventListener('DOMContentLoaded', function () {
  const activityType = document.getElementById('activityType');
  const timeRange = document.getElementById('timeRange');
  const refreshButton = document.getElementById('refreshActivity');
  const loadMoreButton = document.getElementById('loadMore');
  const activityList = document.getElementById('activityList');
  const loadingState = document.getElementById('loadingState');
  let currentPage = 1;

  // Handle filter changes
  activityType.addEventListener('change', () => fetchActivities(true));
  timeRange.addEventListener('change', () => fetchActivities(true));
  refreshButton.addEventListener('click', () => fetchActivities(true));

  if (loadMoreButton) {
    loadMoreButton.addEventListener('click', () => {
      currentPage++;
      fetchActivities(false);
    });
  }

  async function fetchActivities(reset = false) {
    if (reset) {
      currentPage = 1;
    }

    // Show loading state
    loadingState.classList.remove('hidden');

    try {
      const response = await fetch(`/api/v1/admin/users/{{ user.id }}/activity?` + new URLSearchParams({
        type: activityType.value,
        days: timeRange.value,
        page: currentPage
      }));

      if (!response.ok) {
        throw new Error('Failed to fetch activity data');
      }

      const data = await response.json();

      if (reset) {
        activityList.innerHTML = '';
      }

      // Add new activities to the list
      data.activities.forEach(activity => {
        activityList.insertAdjacentHTML('beforeend', createActivityHTML(activity));
      });

      // Update load more button visibility
      if (loadMoreButton) {
        loadMoreButton.style.display = data.has_more ? 'inline-flex' : 'none';
      }

      // Show empty state if no activities
      if (reset && data.activities.length === 0) {
        activityList.innerHTML = `
                    <div class="text-center py-12">
                        <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                        </svg>
                        <h3 class="mt-2 text-sm font-medium text-gray-900">No activity found</h3>
                        <p class="mt-1 text-sm text-gray-500">No user activity recorded for the selected period.</p>
                    </div>
                `;
      }

    } catch (error) {
      console.error('Error fetching activities:', error);
      // Show error state
      if (reset) {
        activityList.innerHTML = `
                    <div class="text-center py-12">
                        <svg class="mx-auto h-12 w-12 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                        </svg>
                        <h3 class="mt-2 text-sm font-medium text-gray-900">Error loading activities</h3>
                        <p class="mt-1 text-sm text-gray-500">Please try refreshing the page.</p>
                    </div>
                `;
      }
    } finally {
      loadingState.classList.add('hidden');
    }
  }

  function createActivityHTML(activity) {
    return `
            <li>
                <div class="relative pb-8">
                    <span class="absolute top-4 left-4 -ml-px h-full w-0.5 bg-gray-200"></span>
                    <div class="relative flex space-x-3">
                        <!-- Activity Icon -->
                        <div>
                            <span class="h-8 w-8 rounded-full ${getActivityColor(activity.type)} flex items-center justify-center ring-8 ring-white">
                                ${getActivityIcon(activity.type)}
                            </span>
                        </div>

                        <!-- Activity Details -->
                        <div class="min-w-0 flex-1 pt-1.5 flex justify-between space-x-4">
                            <div>
                                <p class="text-sm text-gray-500">${activity.description}</p>
                                ${activity.details ? createDetailsHTML(activity.details) : ''}
                            </div>
                            <div class="text-right text-sm whitespace-nowrap text-gray-500">
                                <time datetime="${activity.timestamp}">${formatDate(activity.timestamp)}</time>
                                <div class="mt-1 text-xs text-gray-400">${activity.ip_address}</div>
                            </div>
                        </div>
                    </div>
                </div>
            </li>
        `;
  }

  function getActivityColor(type) {
    const colors = {
      'login': 'bg-green-500',
      'feed': 'bg-blue-500',
      'settings': 'bg-purple-500',
      'default': 'bg-gray-500'
    };
    return colors[type] || colors.default;
  }

  function getActivityIcon(type) {
    // Return SVG icon based on activity type
    const icons = {
      'login': '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1"/>',
      'feed': '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 5c7.18 0 13 5.82 13 13M6 11a7 7 0 017 7m-6 0a1 1 0 11-2 0 1 1 0 012 0z"/>',
      'settings': '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/>'
    };
    return `<svg class="h-5 w-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">${icons[type] || icons.default}</svg>`;
  }

  function createDetailsHTML(details) {
    if (!details || Object.keys(details).length === 0) return '';

    return `
            <div class="mt-2 text-sm text-gray-700">
                <div class="bg-gray-50 rounded px-2 py-1">
                    ${Object.entries(details).map(([key, value]) => `
                        <div class="flex justify-between">
                            <span class="font-medium">${key}:</span>
                            <span>${value}</span>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
  }

  function formatDate(timestamp) {
    return new Date(timestamp).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }
});
