(function() {
    // Form submission
    const uploadForm = document.getElementById('upload-form');
    if (uploadForm) {
        uploadForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const form = e.target;
            const formData = new FormData(form);
            const fileInput = document.getElementById('file');
            const file = fileInput ? fileInput.files[0] : null;
            const listNameInput = document.getElementById('list_name');
            const listName = listNameInput ? listNameInput.value : '';

            if (!listName) {
                alert('Please enter a list name.');
                return;
            }

            if (!file) {
                alert('Please select a file to upload.');
                return;
            }

            if (!file.name.toLowerCase().endsWith('.csv')) {
                alert('Please upload a valid CSV file.');
                return;
            }

            console.log('Sending file:', file.name, 'for list:', listName);
            try {
                const response = await fetch('/contacts/upload', {
                    method: 'POST',
                    body: formData
                });

                if (!response.ok) {
                    const contentType = response.headers.get('content-type');
                    if (contentType && contentType.includes('application/json')) {
                        const errorResult = await response.json();
                        alert(`Error: ${errorResult.error || 'An unknown server error occurred.'}`);
                    } else {
                        const text = await response.text();
                        console.error('Server response (non-JSON/HTML):', text);
                        alert(`Server error or unauthorized. Please check console for details.`);
                        if (response.redirected) {
                            window.location.href = response.url;
                        }
                    }
                    return;
                }

                const result = await response.json();
                alert(result.message);
                form.reset();
                const createListForm = document.getElementById('create-list-form');
                if (createListForm) createListForm.style.display = 'none';
                const dropText = document.getElementById('drop-text');
                if (dropText) dropText.textContent = 'Drop CSV file here or click to browse';
                window.location.reload();
            } catch (error) {
                console.error('Network or unexpected error:', error);
                alert(`An unexpected error occurred: ${error.message}`);
            }
        });
    }

    // Drag and Drop functionality
    const dropZone = document.getElementById('drop-zone');
    if (dropZone) {
        const fileInput = document.getElementById('file');
        const dropText = document.getElementById('drop-text');

        ['dragover', 'dragenter'].forEach(eventName => {
            dropZone.addEventListener(eventName, (e) => {
                e.preventDefault();
                dropZone.style.backgroundColor = '#e1f5fe';
            });
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, (e) => {
                e.preventDefault();
                dropZone.style.backgroundColor = 'white';
            });
        });

        dropZone.addEventListener('drop', (e) => {
            const files = e.dataTransfer.files;
            if (files.length > 0 && files[0].type === 'text/csv') {
                if (fileInput) fileInput.files = files;
                if (dropText) dropText.textContent = files[0].name;
            } else {
                alert('Please drop a valid CSV file (.csv extension).');
            }
        });

        dropZone.addEventListener('click', () => {
            if (fileInput) fileInput.click();
        });
    }

    // File input change
    const fileInput = document.getElementById('file');
    if (fileInput) {
        fileInput.addEventListener('change', () => {
            const dropText = document.getElementById('drop-text');
            if (fileInput.files.length > 0 && dropText) {
                dropText.textContent = fileInput.files[0].name;
            } else if (dropText) {
                dropText.textContent = 'Drop CSV file here or click to browse';
            }
        });
    }

    // Show/Hide create list form
    const createListBtn = document.getElementById('create-list-btn');
    const cancelListBtn = document.getElementById('cancel-list-btn');
    if (createListBtn) {
        createListBtn.addEventListener('click', () => {
            const createListForm = document.getElementById('create-list-form');
            if (createListForm) createListForm.style.display = 'block';
        });
    }
    if (cancelListBtn) {
        cancelListBtn.addEventListener('click', () => {
            const createListForm = document.getElementById('create-list-form');
            if (createListForm) createListForm.style.display = 'none';
            const uploadForm = document.getElementById('upload-form');
            if (uploadForm) uploadForm.reset();
            const dropText = document.getElementById('drop-text');
            if (dropText) dropText.textContent = 'Drop CSV file here or click to browse';
        });
    }
})();