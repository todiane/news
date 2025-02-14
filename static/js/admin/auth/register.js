document.addEventListener('DOMContentLoaded', function () {
  const form = document.getElementById('register-form');
  const errorContainer = document.getElementById('error-container');
  const errorMessage = document.getElementById('error-message');
  const submitButton = document.getElementById('submit-button');
  const buttonText = document.getElementById('button-text');
  const buttonLoading = document.getElementById('button-loading');

  // Function to show error message
  function showError(message) {
    errorMessage.textContent = message;
    errorContainer.classList.remove('hidden');
    // Ensure screen readers announce the error
    errorContainer.setAttribute('aria-hidden', 'false');
  }

  // Function to hide error message
  function hideError() {
    errorContainer.classList.add('hidden');
    errorMessage.textContent = '';
    errorContainer.setAttribute('aria-hidden', 'true');
  }

  // Function to set loading state
  function setLoading(isLoading) {
    if (isLoading) {
      buttonText.classList.add('hidden');
      buttonLoading.classList.remove('hidden');
      submitButton.disabled = true;
    } else {
      buttonText.classList.remove('hidden');
      buttonLoading.classList.add('hidden');
      submitButton.disabled = false;
    }
  }

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
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
        // Handle different types of errors
        if (data.detail && typeof data.detail === 'object') {
          if (data.detail.code === 'EMAIL_EXISTS') {
            showError('This email is already registered');
          } else if (data.detail.code === 'INVALID_PASSWORD') {
            showError(data.detail.message || 'Password does not meet requirements');
          } else {
            showError(data.detail.message || 'Registration failed');
          }
        } else {
          showError('Registration failed. Please try again.');
        }
        setLoading(false);
        return;
      }

      // Successful registration
      window.location.href = '/auth/verify-email-sent';
    } catch (error) {
      console.error('Registration error:', error);
      showError('An error occurred during registration. Please try again.');
      setLoading(false);
    }
  });

  // Clear error when user starts typing
  form.querySelectorAll('input').forEach(input => {
    input.addEventListener('input', hideError);
  });
});
