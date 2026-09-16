const buttons = document.querySelectorAll('.toggle-button');
buttons.forEach(button => {
	const activeText = button.querySelector('.active-text');
	const unactiveText = button.querySelector('.unactive-text');
	const loadingSpinner = button.querySelector('.loading-spinner');

	let isActive = false;
	let loadingButton = false;

	button.addEventListener('click', function () {
		loadingButton = true;
		loadingSpinner.style.display = 'inline-block';
		activeText.style.display = 'none';
		unactiveText.style.display = 'inline-block';

		setTimeout(() => {
			loadingButton = false;
			loadingSpinner.style.display = 'none';

			isActive = !isActive;

			if (isActive) {
				activeText.style.display = 'none';
				unactiveText.style.display = 'inline-block';
			} else {
				activeText.style.display = 'inline-block';
				unactiveText.style.display = 'none';
			}
		}, 2000);
	});
});