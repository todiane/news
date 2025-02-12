// State management
let currentPage = 1;
const itemsPerPage = 10;
let currentFilters = {
  timeRange: 'all',
  category: 'all',
  search: ''
};

// Tab handling
document.querySelectorAll('.tab-button').forEach(button => {
  button.addEventListener('click', () => {
    const tabId = button.getAttribute('data-tab');
    switchTab(tabId);
  });
});

function switchTab(tabId) {
  // Update button states
  document.querySelectorAll('.tab-button').forEach(btn => {
    btn.classList.remove('border-blue-500', 'text-blue-600');
    btn.classList.add('border-transparent', 'text-gray-500');
  });
  const activeButton = document.querySelector(`[data-tab="${tabId}"]`);
  activeButton.classList.add('border-blue-500', 'text-blue-600');
  activeButton.classList.remove('border-transparent', 'text-gray-500');

  // Show active content
  document.querySelectorAll('.tab-content').forEach(content => {
    content.classList.add('hidden');
  });
  document.getElementById(tabId).classList.remove('hidden');

  // Load data if reading history tab
  if (tabId === 'reading-history') {
    loadReadingHistory();
  }
}

// Filter handlers
document.getElementById('timeFilter').addEventListener('change', (e) => {
  currentFilters.timeRange = e.target.value;
  currentPage = 1;
  loadReadingHistory();
});

document.getElementById('categoryFilter').addEventListener('change', (e) => {
  currentFilters.category = e.target.value;
  currentPage = 1;
  loadReadingHistory();
});

document.getElementById('searchHistory').addEventListener('input', (e) => {
  currentFilters.search = e.target.value;
  currentPage = 1;
  loadReadingHistory();
});

// Pagination handlers
['prevPage', 'prevPageMobile'].forEach(id => {
  document.getElementById(id).addEventListener('click', () => {
    if (currentPage > 1) {
      currentPage--;
      loadReadingHistory();
    }
  });
});

['nextPage', 'nextPageMobile'].forEach(id => {
  document.getElementById(id).addEventListener('click', () => {
    currentPage++;
    loadReadingHistory();
  });
});

async function loadReadingHistory() {
  try {
    const response = await fetch(`/api/v1/feed-history?` + new URLSearchParams({
      page: currentPage,
      items_per_page: itemsPerPage,
      time_range: currentFilters.timeRange,
      category: currentFilters.category,
      search: currentFilters.search
    }), {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    });

    if (!response.ok) throw new Error('Failed to fetch reading history');

    const data = await response.json();
    updateHistoryTable(data.items);
    updatePagination(data.total_items);
    toggleEmptyState(data.items.length === 0);

  } catch (error) {
    console.error('Error loading reading history:', error);
    showError(error.message);
  }
}

function updateHistoryTable(items) {
  const tbody = document.getElementById('historyTableBody');
  tbody.innerHTML = items.map(item => `
        <tr>
            <td class="px-6 py-4 whitespace-nowrap">
                <div class="flex items-center">
                    <div class="ml-4">
                        <div class="text-sm font-medium text-gray-900">${item.title}</div>
                        <div class="text-sm text-gray-500">${item.source}</div>
                    </div>
                </div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
                <span class="px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800">
                    ${item.category}
                </span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                ${formatDate(item.read_at)}
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
                <div class="w-full bg-gray-200 rounded-full h-2.5">
                    <div class="bg-blue-600 h-2.5 rounded-full" style="width: ${item.progress}%"></div>
                </div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                <a href="${item.url}" target="_blank" class="text-blue-600 hover:text-blue-900">View</a>
            </td>
        </tr>
    `).join('');
}

function updatePagination(totalItems) {
  const totalPages = Math.ceil(totalItems / itemsPerPage);
  const start = (currentPage - 1) * itemsPerPage + 1;
  const end = Math.min(currentPage * itemsPerPage, totalItems);

  document.getElementById('startIndex').textContent = start;
  document.getElementById('endIndex').textContent = end;
  document.getElementById('totalItems').textContent = totalItems;

  document.getElementById('prevPage').disabled = currentPage === 1;
  document.getElementById('prevPageMobile').disabled = currentPage === 1;
  document.getElementById('nextPage').disabled = currentPage >= totalPages;
  document.getElementById('nextPageMobile').disabled = currentPage >= totalPages;
}

function toggleEmptyState(isEmpty) {
  const tableElement = document.querySelector('table');
  const emptyState = document.getElementById('emptyState');

  tableElement.classList.toggle('hidden', isEmpty);
  emptyState.classList.toggle('hidden', !isEmpty);
}

function formatDate(dateString) {
  return new Date(dateString).toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

// Initial load
document.addEventListener('DOMContentLoaded', () => {
  loadReadingHistory();
});