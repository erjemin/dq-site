// bg-generator.js:
// - Генерирует уникальный градиентный фон на основе текстового содержимого
// - Реализует плавное появление и исчезновение при навигации
// - Авто-редирект через 15 секунд для создания "медитативного" слайд-шоу эффекта
// - Обрабатывает принятие Cookie

document.addEventListener("DOMContentLoaded", function() {
    // 1. Получаем текст для хеширования (из скрытого span в base.html)
    const rawSpan = document.getElementById('dq-content-raw');
    let text = rawSpan ? rawSpan.innerText.trim() : "";

    if (!text) {
        text = "DictumAndQuotesDefault" + Math.random(); // Случайный вариант, если текста нет
    }

    // 2. Хеш-функция (DJB2)
    let hash = 5381;
    for (let i = 0; i < text.length; i++) {
        // Принудительная 32-битная целочисленная арифметика
        hash = ((hash << 5) + hash) + text.charCodeAt(i);
        hash = hash & hash; // Преобразование в 32-битное целое
    }

    // 3. Детерминированная генерация 6 цветовых компонентов из хеша
    // Нам нужно 6 чисел от 0 до 255.
    // Используем генератор псевдослучайных чисел с затравкой из хеша

    function Mulberry32(a) {
        return function() {
          var t = a += 0x6D2B79F5;
          t = Math.imul(t ^ (t >>> 15), t | 1);
          t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
          return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
        }
    }

    const rand = Mulberry32(hash); // Генератор случайных чисел с seed

    // Генерация 6 цветовых компонентов в темном диапазоне для "медитативного" ощущения
    let colors = [];
    for(let i=0; i<6; i++) {
        // Генерируем число от 10 до 80 (темные цвета)
        colors.push(Math.floor(rand() * 70) + 10);
    }

    // Немного перетасовываем на основе случайности, чтобы позволить вариации при обновлении (опционально)
    colors.sort(() => Math.random() - 0.5);

    const rgb1 = `rgb(${colors[0]}, ${colors[1]}, ${colors[2]})`;
    const rgb2 = `rgb(${colors[3]}, ${colors[4]}, ${colors[5]})`;

    console.log("DQ BG Generator:", text.substring(0, 20) + "...", hash, rgb1, rgb2);

    // 4. Применяем к body.
    // Используем линейный градиент вправо со стандартным синтаксисом
    const bgString = `linear-gradient(90deg, ${rgb1} 0%, ${rgb2} 100%)`;
    document.body.style.background = bgString;

    // 5. Применяем к контейнеру фона изображения (если он есть на главной странице)
    const imgBgContainer = document.querySelector('.image-col center > div');
    if (imgBgContainer) {
         // Используем первый цвет градиента с прозрачностью 0.7
         imgBgContainer.style.background = `rgba(${colors[0]}, ${colors[1]}, ${colors[2]}, 0.7)`;
    }

    // 6. Показываем контент (эффект плавного появления - Fade In)
    setTimeout(() => {
        document.body.style.opacity = 1;
    }, 50);

    // 7. Обработка плавного исчезновения (Fade Out) при клике по ссылкам
    document.body.addEventListener('click', function(e) {
        // Ищем, была ли нажата ссылка (всплытие)
        const link = e.target.closest('a');
        if (link && link.href && link.target !== '_blank') {
            const hrefAttr = link.getAttribute('href');
            if (hrefAttr && !hrefAttr.startsWith('#') && !link.href.includes('javascript:')) {
                // Проверяем, является ли ссылка внутренней (тот же домен)
                if (new URL(link.href).origin === window.location.origin) {
                    e.preventDefault(); // Останавливаем немедленный переход
                    document.body.style.opacity = 0; // Запускаем Fade Out

                    // Ждем завершения перехода (соответствует времени CSS transition 0.9s (было 1.5s))
                    setTimeout(() => {
                        window.location.href = link.href;
                    }, 900);
                }
            }
        }
    });

    // 8. Авто-редирект ("медитативное" слайд-шоу)
    // Ищем ссылку "ДАЛЕЕ" и симулируем клик по ней через 15 секунд
    const nextLink = document.querySelector('#next a');
    if (nextLink) {
        setTimeout(() => {
            // Вызываем событие клика по ссылке, чтобы наш обработчик выше (шаг 7) поймал его
            // и выполнил анимацию плавного исчезновения.
            nextLink.click();
        }, 15000);
    }

    // 9. Логика принятия Cookie
    const cookieBanner = document.querySelector('footer');
    if (cookieBanner) {
        const acceptButton = cookieBanner.querySelector('button');
        if (acceptButton) {
            acceptButton.addEventListener('click', function() {
                const date = new Date();
                date.setTime(date.getTime() + (92 * 24 * 60 * 60 * 1000)); // ~3 месяца (7948800000ms)
                document.cookie = "cookie_accept=1; expires=" + date.toUTCString() + "; path=/; SameSite=Lax";
                cookieBanner.remove();
            });
        }
    }
});
