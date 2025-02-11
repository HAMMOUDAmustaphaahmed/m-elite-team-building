// Modal Activation
document.addEventListener('DOMContentLoaded', function() {
    var modal = document.getElementById('qrModal');
    var closeModal = document.querySelector('.close-modal');
    var modalQR = document.getElementById('modalQR');

    const modalOpenButtons = document.querySelectorAll('.qr-cell');
    modalOpenButtons.forEach(button => {
        button.onclick = function() {
            const src = this.src;
            modalQR.src = src;
            modal.style.display = 'block';
        };
    });

    closeModal.onclick = function() {
        modal.style.display = 'none';
    };

    window.onclick = function(event) {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    };
});

// Validation des formulaires
document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', event => {
        const telephone = form.querySelector('input[type="tel"]');
        const email = form.querySelector('input[type="email"]');

        if (!isValidEmail(email.value)) {
            showAlert('Email invalide', 'error');
            event.preventDefault();
        }

        if (!isValidPhone(telephone.value)) {
            showAlert('Numéro de téléphone invalide', 'error');
            event.preventDefault();
        }
    });
});

function isValidEmail(email) {
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return regex.test(email);
}

function isValidPhone(phone) {
    const regex = /^[\+]?[(]?[0-9]{3}[)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4,6}$/;
    return regex.test(phone);
}

function showAlert(message, type = 'error') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert ${type}`;
    alertDiv.textContent = message;
    document.body.appendChild(alertDiv);

    setTimeout(() => {
        alertDiv.remove();
    }, 3000);
}