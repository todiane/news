document.querySelector('form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const formData = new FormData(e.target);

  try {
    const response = await fetch('/api/v1/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email: formData.get('email'),
        password: formData.get('password'),
        remember_me: formData.get('remember_me') === 'on'
      })
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || 'Login failed');
    }

    // Store the token
    localStorage.setItem('token', data.access_token);

    // Redirect to dashboard/home
    window.location.href = '/';
  } catch (error) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'mb-4 bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded relative';
    errorDiv.textContent = error.message;

    const existingError = document.querySelector('[role="alert"]');
    if (existingError) {
      existingError.remove();
    }

    const form = document.querySelector('form');
    form.insertAdjacentElement('beforebegin', errorDiv);
  }
});
