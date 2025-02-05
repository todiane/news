// Create user form javascript file
document.addEventListener('DOMContentLoaded', function () {
  const form = document.getElementById('userCreateForm');
  const statusToggle = document.getElementById('statusToggle');
  const statusText = document.getElementById('statusText');
  const errorAlert = document.getElementById('errorAlert');
  const errorMessage = document.getElementById('errorMessage');
  let isActive = true;

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

    // Validate passwords match
    const password = document.getElementById('password').value;
    const confirmPassword = document.getElementById('confirmPassword').value;

    if (password !== confirmPassword) {
      errorMessage.textContent = 'Passwords do not match';
      errorAlert.classList.remove('hidden');
      return;
    }

    try {
      const response = await fetch('/api/v1/admin/users', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: document.getElementById('email').value,
          password: password,
          is_admin: document.getElementById('role').value === 'admin',
          is_active: isActive
        })
      });

      if (response.ok) {
        // Redirect to user list on success
        window.location.href = '/admin/users';
      } else {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to create user');
      }
    } catch (error) {
      errorMessage.textContent = error.message;
      errorAlert.classList.remove('hidden');
      // Scroll to top to show error message
      window.scrollTo(0, 0);
    }
  });
});
