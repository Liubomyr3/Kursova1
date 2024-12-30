// Прокрутка до секцій при натисканні на навігаційні посилання
document.querySelectorAll('.nav-link').forEach(link => {
  link.addEventListener('click', function (e) {
    e.preventDefault();
    const targetId = this.getAttribute('href').substring(1);
    const targetElement = document.getElementById(targetId);
    if (targetElement) {
      targetElement.scrollIntoView({ behavior: 'smooth' });
    }
  });
});

// Обробка форми контактів
document.querySelector('form').addEventListener('submit', function (e) {
  e.preventDefault();
  alert('Дякуємо за ваше повідомлення! Ми зв’яжемося з вами найближчим часом.');
});

// Обробка форми реєстрації
document.getElementById('signupForm')?.addEventListener('submit', function (e) {
  e.preventDefault(); // Запобігти стандартній поведінці

  const name = document.getElementById('name').value;
  const email = document.getElementById('email').value;
  const password = document.getElementById('password').value;
  const confirmPassword = document.getElementById('confirmPassword').value;

  if (password !== confirmPassword) {
    alert('Паролі не збігаються!');
    return;
  }

  // Відправлення даних на сервер
  fetch('/register', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      name: name,
      email: email,
      password: password,
    }),
  })
    .then(response => {
      if (response.ok) {
        alert('Реєстрація успішна!');
        window.location.href = '/'; // Перехід на головну сторінку
      } else {
        alert('Помилка під час реєстрації.');
      }
    })
    .catch(error => console.error('Error:', error));
});

// Обробка форми авторизації
document.getElementById('loginForm')?.addEventListener('submit', function (e) {
  e.preventDefault();

  const email = document.getElementById('email').value;
  const password = document.getElementById('password').value;

  // Відправлення даних на сервер
  fetch('/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      email: email,
      password: password,
    }),
  })
    .then(response => {
      if (response.ok) {
        alert('Авторизація успішна!');
        window.location.href = '/dashboard'; // Перехід до особистого кабінету
      } else {
        alert('Помилка авторизації.');
      }
    })
    .catch(error => console.error('Error:', error));
});

//відгук
document.addEventListener('DOMContentLoaded', function () {
  const feedbackForm = document.getElementById('feedbackForm');
  const feedbackAlert = document.getElementById('feedbackAlert');

  feedbackForm.addEventListener('submit', async function (event) {
    event.preventDefault(); // Запобігає стандартному надсиланню форми

    // Отримання даних з форми
    const formData = new FormData(feedbackForm);
    const feedbackData = {
      name: formData.get('name'),
      email: formData.get('email'),
      mark: formData.get('mark'),
      message: formData.get('message'),
    };

    try {
      // Надсилання даних на сервер через fetch
      const response = await fetch('/feedback', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(feedbackData),
      });

      if (response.ok) {
        // Очищення форми після успішного надсилання
        feedbackForm.reset();
        showFeedbackAlert('Ваш відгук успішно надіслано!', 'success');
      } else {
        throw new Error('Помилка надсилання. Спробуйте ще раз.');
      }
    } catch (error) {
      showFeedbackAlert(error.message, 'danger');
    }
  });

  // Функція для показу повідомлень
  function showFeedbackAlert(message, type) {
    feedbackAlert.innerHTML = `<div class="alert alert-${type}" role="alert">${message}</div>`;
    setTimeout(() => {
      feedbackAlert.innerHTML = ''; // Видалення повідомлення через 5 секунд
    }, 5000);
  }
});

// all_excursion
$(document).ready(function () {
  // Initialize DataTables with sorting and Ukrainian localization
  $('#excursionsTable').DataTable({
      "language": {
          "url": "//cdn.datatables.net/plug-ins/1.13.4/i18n/uk.json" // Ukrainian localization
      }
  });

  // Add click event to rows to redirect to excursion details
  $('#excursionsTable tbody').on('click', 'tr', function () {
      const link = $(this).find('a').attr('href'); // Extract href from the link in the row
      if (link) {
          window.location.href = link; // Redirect to the details page
      }
  });
});

//excursion
$(document).ready(function () {
  // Handle a "Back to All Excursions" button click
  $('#backToExcursions').on('click', function () {
      window.location.href = '/excursions'; // Redirect to the list of excursions
  });

  // Add smooth scrolling for internal links (if any)
  $('a[href^="#"]').on('click', function (e) {
      e.preventDefault();
      const target = $(this.getAttribute('href'));
      if (target.length) {
          $('html, body').animate({
              scrollTop: target.offset().top
          }, 500); // Smooth scroll to the target section
      }
  });
});

// Функція бронювання екскурсії
async function bookExcursion(excursionId) {
  try {
      const response = await fetch(`/book/${excursionId}`, {
          method: 'POST',
          headers: {
              'Content-Type': 'application/json'
          }
      });

      if (response.ok) {
          alert("Екскурсію успішно заброньовано!");
          window.location.href = "/dashboard"; // Перенаправлення на особистий кабінет
      } else {
          const error = await response.json();
          alert(`Помилка: ${error.message}`);
      }
  } catch (error) {
      console.error('Помилка бронювання:', error);
      alert("Щось пішло не так. Спробуйте ще раз.");
  }
}

// Відображення екскурсій із кнопкою бронювання
function renderTrips(trips) {
  const container = document.getElementById("trips-container");
  container.innerHTML = "";

  trips.forEach(trip => {
      const tripElement = document.createElement("div");
      tripElement.className = "trip";
      tripElement.innerHTML = `
          <h3>${trip.name}</h3>
          <img src="${trip.image}" alt="${trip.name}">
          <p><strong>Локація:</strong> ${trip.location}</p>
          <p><strong>Ціна:</strong> ${trip.price} UAH</p>
          <p><strong>Дати:</strong> ${trip.startDate} - ${trip.endDate}</p>
          <button onclick="bookExcursion(${trip.id})">Забронювати</button>
      `;
      container.appendChild(tripElement);
  });
}

document.getElementById('bookButton').addEventListener('click', async function () {
  const excursionId = 3; // ID Київського туру

  try {
    const response = await fetch(`/book/${excursionId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    });

    if (response.ok) {
      const data = await response.json();
      alert(data.message); // Повідомлення про успіх
      window.location.href = "/dashboard"; // Перенаправлення до особистого кабінету
    } else if (response.status === 401) {
      alert("Ви не авторизовані. Увійдіть у систему, щоб забронювати екскурсію.");
      window.location.href = "/login";
    } else if (response.status === 404) {
      alert("Екскурсія не знайдена. Будь ласка, спробуйте іншу.");
    } else if (response.status === 400) {
      alert("Недостатньо коштів для бронювання.");
    } else {
      alert("Сталася невідома помилка. Спробуйте пізніше.");
    }
  } catch (error) {
    console.error('Помилка бронювання:', error);
    alert("Щось пішло не так. Спробуйте ще раз.");
  }
});

