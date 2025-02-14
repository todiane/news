form.addEventListener('submit', async (e) => {
  e.preventDefault(); // Prevent form from submitting normally
  hideError();

  const formData = new FormData(form);
  const password = formData.get('password');
  const confirmPassword = formData.get('confirm_password');

  // Client-side password validation
  if (password !== confirmPassword) {
    showError('Passwords do not match');
    return;
  }

  // Basic password strength check
  if (password.length < 8) {
    showError('Password must be at least 8 characters long');
    return;
  }

  setLoading(true);

  try {
    const response = await fetch('/api/v1/auth/register', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email: formData.get('email'),
        password: password
      })
    });

    const data = await response.json();

    if (!response.ok) {
      if (data.detail && typeof data.detail === 'object') {
        showError(data.detail.message || 'Registration failed');
      } else {
        showError(data.detail || 'Registration failed');
      }
      setLoading(false);
      return;
    }

    // Success - redirect to email verification page
    window.location.href = '/auth/verify-email-sent';
  } catch (error) {
    console.error('Registration error:', error);
    showError('An error occurred during registration. Please try again.');
    setLoading(false);
  }
});

// Update showError function to ensure errors are visible
function showError(message) {
  const errorContainer = document.getElementById('error-container');
  const errorMessage = document.getElementById('error-message');

  errorMessage.textContent = message;
  errorContainer.classList.remove('hidden');
  errorContainer.scrollIntoView({ behavior: 'smooth', block: 'center' });

  // Announce error for screen readers
  errorContainer.setAttribute('aria-hidden', 'false');
}
