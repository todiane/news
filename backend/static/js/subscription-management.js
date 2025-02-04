// static/js/subscription-management.js

function subscriptionManagement() {
  return {
    subscriptions: [],
    view: 'all',
    loading: true,
    error: null,
    categories: [],

    async init() {
      await this.loadSubscriptions();
    },

    get filteredSubscriptions() {
      switch (this.view) {
        case 'favorites':
          return this.subscriptions.filter(s => s.is_favorite);
        case 'unread':
          return this.subscriptions.filter(s => this.getUnreadCount(s) > 0);
        case 'bookmarks':
          return this.subscriptions.filter(s => this.getBookmarkCount(s) > 0);
        default:
          return this.subscriptions;
      }
    },

    async loadSubscriptions() {
      try {
        this.loading = true;
        const response = await fetch('/api/v1/subscriptions/preferences');
        if (response.ok) {
          this.subscriptions = await response.json();
        } else {
          throw new Error('Failed to load subscriptions');
        }
      } catch (error) {
        this.error = error.message;
        console.error('Error loading subscriptions:', error);
      } finally {
        this.loading = false;
      }
    },

    async toggleFavorite(subscription) {
      try {
        const response = await fetch(`/api/v1/subscriptions/preferences/${subscription.feed_id}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            is_favorite: !subscription.is_favorite,
            notification_enabled: subscription.notification_enabled,
            update_frequency: subscription.update_frequency,
            categories: subscription.categories
          })
        });

        if (response.ok) {
          subscription.is_favorite = !subscription.is_favorite;
          this.showNotification(
            subscription.is_favorite ? 'Added to favorites' : 'Removed from favorites',
            'success'
          );
        } else {
          throw new Error('Failed to update favorite status');
        }
      } catch (error) {
        this.showNotification('Error updating favorite status', 'error');
        console.error('Error:', error);
      }
    },

    async toggleNotifications(subscription) {
      try {
        const response = await fetch(`/api/v1/subscriptions/preferences/${subscription.feed_id}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            notification_enabled: !subscription.notification_enabled,
            is_favorite: subscription.is_favorite,
            update_frequency: subscription.update_frequency,
            categories: subscription.categories
          })
        });

        if (response.ok) {
          subscription.notification_enabled = !subscription.notification_enabled;
          this.showNotification(
            subscription.notification_enabled ? 'Notifications enabled' : 'Notifications disabled',
            'success'
          );
        } else {
          throw new Error('Failed to update notification settings');
        }
      } catch (error) {
        this.showNotification('Error updating notification settings', 'error');
        console.error('Error:', error);
      }
    },

    async updateFrequency(subscription) {
      try {
        const response = await fetch(`/api/v1/subscriptions/preferences/${subscription.feed_id}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            update_frequency: subscription.update_frequency,
            notification_enabled: subscription.notification_enabled,
            is_favorite: subscription.is_favorite,
            categories: subscription.categories
          })
        });

        if (response.ok) {
          this.showNotification('Update frequency saved', 'success');
        } else {
          throw new Error('Failed to update frequency');
        }
      } catch (error) {
        this.showNotification('Error updating frequency', 'error');
        console.error('Error:', error);
      }
    },

    async addCategory(subscription) {
      const category = prompt('Enter new category:');
      if (!category) return;

      try {
        const updatedCategories = [...(subscription.categories || []), category];
        const response = await fetch(`/api/v1/subscriptions/preferences/${subscription.feed_id}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            categories: updatedCategories,
            notification_enabled: subscription.notification_enabled,
            is_favorite: subscription.is_favorite,
            update_frequency: subscription.update_frequency
          })
        });

        if (response.ok) {
          subscription.categories = updatedCategories;
          this.showNotification('Category added', 'success');
        } else {
          throw new Error('Failed to add category');
        }
      } catch (error) {
        this.showNotification('Error adding category', 'error');
        console.error('Error:', error);
      }
    },

    async removeCategory(subscription, categoryToRemove) {
      try {
        const updatedCategories = subscription.categories.filter(c => c !== categoryToRemove);
        const response = await fetch(`/api/v1/subscriptions/preferences/${subscription.feed_id}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            categories: updatedCategories,
            notification_enabled: subscription.notification_enabled,
            is_favorite: subscription.is_favorite,
            update_frequency: subscription.update_frequency
          })
        });

        if (response.ok) {
          subscription.categories = updatedCategories;
          this.showNotification('Category removed', 'success');
        } else {
          throw new Error('Failed to remove category');
        }
      } catch (error) {
        this.showNotification('Error removing category', 'error');
        console.error('Error:', error);
      }
    },

    getUnreadCount(subscription) {
      const totalArticles = subscription.feed?.article_count || 0;
      const readCount = Object.keys(subscription.read_items || {}).length;
      return totalArticles - readCount;
    },

    getBookmarkCount(subscription) {
      return Object.keys(subscription.bookmarked_items || {}).length;
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

    showNotification(message, type = 'info') {
      const event = new CustomEvent('show-notification', {
        detail: { message, type }
      });
      window.dispatchEvent(event);
    }
  };
}
