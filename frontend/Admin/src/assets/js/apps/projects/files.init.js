document.addEventListener('DOMContentLoaded', function () {
    // Get the file count element (we'll create one if it doesn't exist)
    let fileCountElement = document.querySelector('#fileCount');

    // Count initial files
    updateFileCount();

    // Set up file upload functionality
    const uploadInput = document.querySelector('input[type="file"]');
    const uploadLabel = uploadInput.closest('label');

    uploadInput.addEventListener('change', function (e) {
        if (e.target.files.length > 0) {
            // Create a new file card for each uploaded file
            Array.from(e.target.files).forEach(file => {
                addFileCard(file);
            });

            // Reset the input
            uploadInput.value = '';

            // Update the file count
            updateFileCount();
        }
    });

    function addFileCard(file) {
        const filesContainer = document.querySelector('#filesContainer');
        const fileSizeMB = (file.size / (1024 * 1024)).toFixed(2); // Convert to MB

        // Determine icon based on file type
        let iconClass = 'ri-file-text-line'; // default
        const fileType = file.type.split('/')[0];
        const fileExtension = file.name.split('.').pop().toLowerCase();

        if (fileType === 'image') {
            iconClass = 'ri-file-image-line';
        } else if (fileExtension === 'pdf') {
            iconClass = 'ri-file-pdf-2-line';
        } else if (['zip', 'rar', '7z', 'tar', 'gz'].includes(fileExtension)) {
            iconClass = 'ri-file-zip-line';
        }

        // Create new file card
        const fileCard = document.createElement('div');
        fileCard.className = 'col';
        fileCard.innerHTML = `
        <div class="card text-center">
          <div class="card-body">
            <i class="${iconClass} fs-2"></i>
            <h6 class="mt-3 mb-1">
              <a href="#!" class="text-reset stretched-link">${file.name}</a>
            </h6>
            <p class="text-muted">${fileSizeMB} MB</p>
          </div>
        </div>
      `;

        // Insert before the upload button
        filesContainer.insertBefore(fileCard, uploadLabel.parentElement);
    }

    function updateFileCount() {
        const fileCards = document.querySelectorAll('.col .card:not(.card-h-100)');
        const count = fileCards.length;

        if (fileCountElement) {
            fileCountElement.textContent = `فایل‌ها (${count})`;
        } else {
            // Create the count element if it doesn't exist
            fileCountElement = document.createElement('h5');
            fileCountElement.className = 'mb-5';
            fileCountElement.textContent = `فایل‌ها (${count})`;

            // Insert it before the files container
            const filesContainer = document.querySelector('#filesContainer');
            filesContainer.parentNode.insertBefore(fileCountElement, filesContainer);
        }
    }
});