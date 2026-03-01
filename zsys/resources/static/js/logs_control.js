
// Обработка формы конфигурации
document.getElementById('config-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const config = {
        memory_limit_mb: formData.get('memory_limit_mb') ? parseFloat(formData.get('memory_limit_mb')) : null,
        log_level: formData.get('log_level'),
        theme: formData.get('theme')
    };

    try {
        const response = await fetch('/logs/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });

        if (response.ok) {
            alert('Configuration updated successfully');
            location.reload();
        } else {
            const error = await response.json();
            alert(`Error: ${error.detail}`);
        }
    } catch (err) {
        alert('Failed to update configuration');
        console.error(err);
    }
});

// Кнопка ручного обновления
document.getElementById('refresh-btn').addEventListener('click', function() {
    this.classList.add('loading');
    location.reload();
});

// Автоматическое обновление логов
{% if auto_refresh %}
function refreshLogs() {
    const params = new URLSearchParams({
        limit: {{ limit }},
        filter_level: '{{ filter_level or "" }}',
        partial: 1
    });

    fetch(`/logs?${params}`)
        .then(response => response.text())
        .then(html => {
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            document.getElementById('logs-container').innerHTML =
                doc.querySelector('#logs-container').innerHTML;
        });
}

setInterval(refreshLogs, 2000);
{% endif %}

// Переключение темы
document.getElementById('theme-selector').addEventListener('change', function() {
    const theme = this.value;
    document.documentElement.setAttribute('data-bs-theme', theme);

    // Сохраняем тему в localStorage
    localStorage.setItem('theme', theme);
});

// При загрузке страницы применяем сохраненную тему
document.addEventListener('DOMContentLoaded', function() {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-bs-theme', savedTheme);
    document.getElementById('theme-selector').value = savedTheme;
});
