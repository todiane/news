// Dashboard-specific JavaScript for the admin panel - dashboard.html
document.addEventListener('DOMContentLoaded', function () {
  // Example: Auto-refresh stats every 5 minutes
  setInterval(function () {
    fetch('/api/v1/admin/stats')
      .then(response => response.json())
      .then(data => {
        // Update stats
      });
  }, 300000);
});
