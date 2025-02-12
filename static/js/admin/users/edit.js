document.addEventListener('DOMContentLoaded', function () {
  const form = document.getElementById('userEditForm');
  const statusToggle = document.getElementById('statusToggle');
  const statusText = document.getElementById('statusText');
  const errorAlert = document.getElementById('errorAlert');
  const errorMessage = document.getElementById('errorMessage');
  const successAlert = document.getElementById('successAlert');

  // Initialize isActive from the button's aria-checked attribute
  let isActive = statusToggle.getAttribute('aria-checked') === 'true';

  // Get user ID from the form's data attribute
  const userId = form.getAttribute('data-user-id');

  // Handle status toggle
  statusToggle.addEventListener('click', function () {
    isActive = !isActive;
    this.setAttribute('aria-checked', isActive);
    this.classList.toggle('bg-green-500');
    this.classList.toggle('bg-gray-200');
    this.querySelector('span:not(.sr-only)').classList.toggle('translate-x-5');
    this.querySelector('span:not(.sr-only)').classList.toggle('translate-x-0');
    statusText.textContent = isActive ? 'Account Active' : 'Account Inactive';
  });

  // Handle form submission
  form.addEventListener('submit', async function (e) {
    e.preventDefault();
    errorAlert.classList.add('hidden');
    successAlert.classList.add('hidden');

    // Validate passwords if provided
    const newPassword = document.getElementById('newPassword').value;
    const confirmPassword = document.getElementById('confirmPassword').value;

    if (newPassword && newPassword !== confirmPassword) {
      errorMessage.textContent = 'Passwords do not match';
      errorAlert.classList.remove('hidden');
      return;
    }

    try {
      const response = await fetch(`/api/v1/admin/users/${userId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: document.getElementById('email').value,
          is_admin: document.getElementById('role').value === 'admin',
          is_active: isActive,
          new_password: newPassword || undefined
        })
      });

      if (response.ok) {
        successAlert.classList.remove('hidden');
        // Clear password fields
        document.getElementById('newPassword').value = '';
        document.getElementById('confirmPassword').value = '';
        // Scroll to top to show success message
        window.scrollTo(0, 0);
      } else {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to update user');
      }
    } catch (error) {
      errorMessage.textContent = error.message;
      errorAlert.classList.remove('hidden');
      // Scroll to top to show error message
      window.scrollTo(0, 0);
    }
  });
});