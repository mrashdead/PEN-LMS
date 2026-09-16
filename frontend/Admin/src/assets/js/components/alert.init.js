document.getElementById('liveAlertBtn').addEventListener('click', function () {
	const alertPlaceholder = document.getElementById('liveAlert');

	if (!alertPlaceholder.querySelector('.alert')) {
		const alert = document.createElement('div');
		alert.className = 'alert alert-primary alert-dismissible alert-live-backdrop fade show';
		alert.role = 'alert';
		alert.innerHTML = 'شما با موفقیت این کار را انجام دادید! ' +
			'<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>';

		alertPlaceholder.appendChild(alert);
	}
});