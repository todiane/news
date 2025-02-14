function feedManagement() {
  return {
    feeds: [],
    categories: ['tech', 'dev', 'ai', 'news'],
    currentCategory: 'all',
    showModal: false,
    showDeleteModal: false,
    editingFeed: null,
    feedToDelete: null,
    feedForm: {
      name: '',
      url: '',
      category: 'tech'
    },
    errors: {},
    feedMetadata: null,
    refreshingFeeds: new Set(),
    feedStats: null,
    notifications: [],

    get filteredFeeds() {
      if (this.currentCategory === 'all') {
        return this.feeds;
      }
      return this.feeds.filter(feed => feed.category === this.currentCategory);
    },

    async loadFeeds() {
      try {
        const response = await fetch('/api/v1/feeds');
        if (response.ok) {
          this.feeds = await response.json();
        } else {
          console.error('Error loading feeds:', await response.text());
        }
      } catch (error) {
        console.error('Error:', error);
      }
    },

    openAddModal() {
      this.editingFeed = null;
      this.feedForm = {
        name: '',
        url: '',
        category: 'tech'
      };
      this.errors = {};
      this.showModal = true;
    },

    editFeed(feed) {
      this.editingFeed = feed;
      this.feedForm = {
        name: feed.name,
        url: feed.url,
        category: feed.category
      };
      this.errors = {};
      this.showModal = true;
    },

    async validateFeedUrl() {
      if (!this.feedForm.url) return;

      try {
        const response = await fetch(`/api/v1/feeds/validate?url=${encodeURIComponent(this.feedForm.url)}`);
        const data = await response.json();

        if (data.is_valid) {
          // Auto-fill feed name if not already set
          if (!this.feedForm.name && data.metadata.title) {
            this.feedForm.name = data.metadata.title;
          }
          this.errors = {};
          this.feedMetadata = data.metadata;
        } else {
          this.errors = { url: data.errors.error || 'Invalid feed URL' };
          this.feedMetadata = null;
        }
      } catch (error) {
        console.error('Error validating feed:', error);
        this.errors = { url: 'Error validating feed URL' };
        this.feedMetadata = null;
      }
    },

    async saveFeed() {
      try {
        // Validate feed first
        await this.validateFeedUrl();
        if (Object.keys(this.errors).length > 0) {
          return; // Don't proceed if there are validation errors
        }

        const url = this.editingFeed
          ? `/api/v1/feeds/${this.editingFeed.id}`
          : '/api/v1/feeds';

        const method = this.editingFeed ? 'PUT' : 'POST';

        const response = await fetch(url, {
          method: method,
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(this.feedForm)
        });

        if (response.ok) {
          await this.loadFeeds();
          this.closeModal();
          // Show success message
          this.showNotification('Feed saved successfully', 'success');
        } else {
          const error = await response.json();
          this.errors = error.details || { general: error.message };
          this.showNotification('Error saving feed', 'error');
        }
      } catch (error) {
        console.error('Error saving feed:', error);
        this.errors = { general: 'An unexpected error occurred' };
        this.showNotification('Error saving feed', 'error');
      }
    },

    confirmDeleteFeed(feed) {
      this.feedToDelete = feed;
      this.showDeleteModal = true;
    },

    async deleteFeed() {
      if (!this.feedToDelete) return;

      try {
        const response = await fetch(`/api/v1/feeds/${this.feedToDelete.id}`, {
          method: 'DELETE'
        });

        if (response.ok) {
          await this.loadFeeds();
          this.showDeleteModal = false;
          this.feedToDelete = null;
        } else {
          console.error('Error deleting feed:', await response.text());
        }
      } catch (error) {
        console.error('Error:', error);
      }
    },

    closeModal() {
      this.showModal = false;
      this.editingFeed = null;
      this.feedForm = {
        name: '',
        url: '',
        category: 'tech'
      };
      this.errors = {};
    },

    formatDate(dateString) {
      if (!dateString) return 'Never';
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    },

    async refreshFeed(feedId) {
      if (this.refreshingFeeds.has(feedId)) return;

      this.refreshingFeeds.add(feedId);
      try {
        const response = await fetch(`/api/v1/feeds/${feedId}/refresh`, {
          method: 'POST'
        });

        if (response.ok) {
          const result = await response.json();
          await this.loadFeeds();
          this.showNotification('Feed refreshed successfully', 'success');
        } else {
          const error = await response.json();
          this.showNotification(error.detail?.message || 'Error refreshing feed', 'error');
        }
      } catch (error) {
        console.error('Error refreshing feed:', error);
        this.showNotification('Error refreshing feed', 'error');
      } finally {
        this.refreshingFeeds.delete(feedId);
      }
    },

    async loadFeedStats() {
      try {
        const response = await fetch('/api/v1/feeds/stats');
        if (response.ok) {
          this.feedStats = await response.json();
        } else {
          console.error('Error loading feed stats:', await response.text());
        }
      } catch (error) {
        console.error('Error:', error);
      }
    },

    async discoverFeed() {
      if (!this.feedForm.url) return;

      try {
        const response = await fetch(`/api/v1/feeds/discover?website_url=${encodeURIComponent(this.feedForm.url)}`);
        const data = await response.json();

        if (response.ok) {
          this.feedForm.url = data.feed_url;
          if (!this.feedForm.name && data.metadata.title) {
            this.feedForm.name = data.metadata.title;
          }
          this.feedMetadata = data.metadata;
          this.errors = {};
          this.showNotification('Feed discovered successfully', 'success');
        } else {
          this.errors = { url: data.detail || 'No feed found at this URL' };
          this.feedMetadata = null;
        }
      } catch (error) {
        console.error('Error discovering feed:', error);
        this.errors = { url: 'Error discovering feed' };
        this.feedMetadata = null;
      }
    },

    showNotification(message, type = 'info') {
      const id = Date.now();
      this.notifications.push({ id, message, type });
      setTimeout(() => {
        this.notifications = this.notifications.filter(n => n.id !== id);
      }, 5000);
    },

    init() {
      this.loadFeeds();
      this.loadFeedStats();
    }
  }
}


