document.addEventListener('DOMContentLoaded', function () {
    const tourSelect = document.querySelector('#id_tour'); // Select the Tour dropdown
    const fixedDepartureRow = document.querySelector('.form-row.field-fixed_departure_date');
    const fromDateRow = document.querySelector('.form-row.field-from_date');
    const toDateRow = document.querySelector('.form-row.field-to_date');

    // Function to toggle field visibility
    function toggleFields() {
        const selectedTourId = tourSelect ? tourSelect.value : null;

        if (!selectedTourId) {
            // No tour selected, hide all date fields
            fixedDepartureRow.style.display = 'none';
            fromDateRow.style.display = 'none';
            toDateRow.style.display = 'none';
            return;
        }

        // Fetch the tour's details using the Django Admin API
        fetch(`/admin/travel/tour/${selectedTourId}/json/`) // Replace `your_app` with your app's name
            .then((response) => response.json())
            .then((data) => {
                if (data.type.is_fixed_departure) {
                    // Show Fixed Departure and hide Tour Package fields
                    fixedDepartureRow.style.display = 'flex';
                    fromDateRow.style.display = 'none';
                    toDateRow.style.display = 'none';
                } else if (data.type.is_tour_package) {
                    // Show Tour Package fields and hide Fixed Departure
                    fixedDepartureRow.style.display = 'none';
                    fromDateRow.style.display = 'flex';
                    toDateRow.style.display = 'flex';
                } else {
                    // Hide all fields by default
                    fixedDepartureRow.style.display = 'none';
                    fromDateRow.style.display = 'none';
                    toDateRow.style.display = 'none';
                }
            })
            .catch((error) => console.error('Error fetching tour details:', error));
    }

    // Attach change event listener to Tour dropdown
    if (tourSelect) {
        tourSelect.addEventListener('change', toggleFields);
        toggleFields(); // Initialize on page load
    }
});
