document.getElementById('login-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const formData = new FormData(e.target);
    const data = {
        username: formData.get('username'),
        password: formData.get('password')
    };

    try {
        const response = await fetch('/login/check', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();
        const responseMessage = document.getElementById('response-message');

        if (response.ok && result.status) {
            responseMessage.innerHTML = `<div class="alert alert-success">${result.message || 'Успішний вхід'}</div>`;
            
            // Пересилання через 3 секунди
            setTimeout(() => {
                window.location.href = '/logs'; // Замінити '/dashboard' на потрібний шлях
            }, 3000); // 3000 мс = 3 секунди
        } else {
            responseMessage.innerHTML = `<div class="alert alert-danger">${result.message || 'Невідомий статус'}</div>`;
        }
    } catch (error) {
        document.getElementById('response-message').innerHTML = `<div class="alert alert-danger">Помилка при авторизації</div>`;
    }
});

function togglePassword() {
    const passwordField = document.getElementById("password");
    const passwordType = passwordField.type === "password" ? "text" : "password";
    passwordField.type = passwordType;
}
