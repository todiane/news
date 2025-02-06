// Handle success/error messages timing
document.addEventListener('DOMContentLoaded', () => {
  // Handle success messages
  const successAlert = document.querySelector('.bg-green-50');
  if (successAlert) {
    setTimeout(() => {
      successAlert.remove();
    }, 5000);
  }

  // Handle error messages
  const errorAlert = document.querySelector('.bg-red-50');
  if (errorAlert) {
    setTimeout(() => {
      errorAlert.remove();
    }, 5000);
  }
});
