// Main JavaScript für FiveM Server Website

document.addEventListener('DOMContentLoaded', function() {
    // Fix für Benutzermenü-Dropdown, damit es nicht beim Klicken auf Links darin schließt
    const userDropdownItems = document.querySelectorAll('.dropdown-menu.dropdown-menu-end .dropdown-item');
    userDropdownItems.forEach(item => {
        item.addEventListener('click', function(e) {
            // Verhindert, dass das Dropdown-Menü geschlossen wird
            e.stopPropagation();
        });
    });

    // Bootstrap Dropdown konfigurieren, damit es bei Klicks auf Items nicht schließt
    const dropdownMenu = document.querySelector('.dropdown-menu.dropdown-menu-end');
    if (dropdownMenu) {
        const dropdownInstance = bootstrap.Dropdown.getInstance(
            document.querySelector('#navbarDropdown')
        );
        if (dropdownInstance) {
            dropdownMenu.addEventListener('click', function(e) {
                e.stopPropagation();
            });
        }
    }
    
    // Tooltips initialisieren
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Popovers initialisieren
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Automatisches Schließen von Alerts nach 5 Sekunden
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert.alert-success, .alert.alert-info');
        alerts.forEach(function(alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
    
    // Server-IP Kopieren Funktion (wird in der index.html verwendet)
    window.copyToClipboard = function(text) {
        navigator.clipboard.writeText(text).then(function() {
            // Erfolg-Meldung
            const alertHTML = `
                <div class="alert alert-success alert-dismissible fade show" role="alert">
                    <i class="fas fa-check-circle me-2"></i>Server-IP wurde in die Zwischenablage kopiert!
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                </div>
            `;
            const alertContainer = document.querySelector('.container:first-of-type');
            if (alertContainer) {
                alertContainer.insertAdjacentHTML('afterbegin', alertHTML);
                
                // Nach 3 Sekunden automatisch entfernen
                setTimeout(function() {
                    const newAlert = alertContainer.querySelector('.alert');
                    if (newAlert) {
                        const bsAlert = new bootstrap.Alert(newAlert);
                        bsAlert.close();
                    }
                }, 3000);
            }
        }, function() {
            // Fehler
            alert('Fehler beim Kopieren der Server-IP. Bitte kopieren Sie die IP manuell.');
        });
    };
    
    // Forum-Post Aktionen
    const postActionButtons = document.querySelectorAll('.post-action-btn');
    postActionButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const action = this.dataset.action;
            const postId = this.dataset.postId;
            
            if (action === 'quote') {
                // Implementiere Quote-Funktion
                console.log('Quote post', postId);
            }
        });
    });
    
    // Mobile Navigation Verbesserungen
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    navLinks.forEach(function(link) {
        link.addEventListener('click', function() {
            const navbarCollapse = document.querySelector('.navbar-collapse');
            if (navbarCollapse && navbarCollapse.classList.contains('show')) {
                const bsCollapse = new bootstrap.Collapse(navbarCollapse);
                bsCollapse.hide();
            }
        });
    });
});