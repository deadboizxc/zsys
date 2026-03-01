document.getElementById('registration-form').addEventListener('submit', async (e) => {
    e.preventDefault(); // Запобігаємо перезавантаженню сторінки при сабміті форми

    const formData = new FormData(e.target); // Отримуємо дані форми
    const data = {
        username: formData.get('username'),
        email: formData.get('email'),
        password: formData.get('password')
    };

    try {
        // Відправка запиту на сервер для перевірки реєстрації
        const response = await fetch('/register/check', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();
        const responseMessage = document.getElementById('response-message');
        
        console.log('Response:', response);
        console.log('Result:', result);
        
        if (response.ok && result.status) {
            responseMessage.innerHTML = `<div class="alert alert-success">${result.message || 'Успішна реєстрація'}</div>`;
            
            // Пересилання через 3 секунди
            setTimeout(() => {
                window.location.href = '/logs'; // Перенаправлення на сторінку входу, змінити на потрібну
            }, 3000); // 3000 мс = 3 секунди
        } else {
            responseMessage.innerHTML = `<div class="alert alert-danger">${result.message || 'Помилка реєстрації'}</div>`;
        }
    } catch (error) {
        document.getElementById('response-message').innerHTML = `<div class="alert alert-danger">Не вдалося зареєструватися. Спробуйте пізніше.</div>`;
        console.error('Error during registration:', error);
    }
});

function togglePassword() {
    const passwordField = document.getElementById("password");
    passwordField.type = passwordField.type === "password" ? "text" : "password";
}
