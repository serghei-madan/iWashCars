// Hide the "add another" and "change" links for vehicle_type field
(function() {
    document.addEventListener('DOMContentLoaded', function() {
        var vehicleTypeField = document.querySelector('.field-vehicle_type');
        if (vehicleTypeField) {
            var links = vehicleTypeField.querySelectorAll('a.related-widget-wrapper-link');
            links.forEach(function(link) {
                link.style.display = 'none';
            });
        }
    });
})();
