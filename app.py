from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message

# Ініціалізація Flask
app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database2.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'
db = SQLAlchemy(app)

mail = Mail(app)

ab = 10000

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    bonus_amount = db.Column(db.Integer, default=10000)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    # Зворотний зв'язок з Feedback та Booking
    feedbacks = db.relationship('Feedback', back_populates='user')
    bookings = db.relationship('Booking', back_populates='user')
    total_bookings = db.Column(db.Integer, default=0)


class Feedback(db.Model):
    __tablename__ = 'feedbacks'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    mark = db.Column(db.String(10), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    # Зворотний зв'язок з User
    user = db.relationship('User', back_populates='feedbacks')


class Booking(db.Model):
    __tablename__ = 'bookings'
    id = db.Column(db.Integer, primary_key=True)  # Унікальний ідентифікатор бронювання
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Зовнішній ключ до користувача
    excursion_id = db.Column(db.Integer, db.ForeignKey('excursions.id'), nullable=False)  # Зовнішній ключ до екскурсії
    status = db.Column(db.String(20), default="Booked")  # Статус бронювання, за замовчуванням "Booked"
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())  # Час створення запису

    # Відношення з User (користувач) і Excursion (екскурсія)
    user = db.relationship('User', back_populates='bookings')  # Користувач, який зробив бронювання
    excursion = db.relationship('Excursion', back_populates='bookings')  # Екскурсія, яку було заброньовано


# Модель Excursion (Екскурсія)
class Excursion(db.Model):
    __tablename__ = 'excursions'
    id = db.Column(db.Integer, primary_key=True)  # Унікальний ідентифікатор екскурсії
    name = db.Column(db.String(100), nullable=False)  # Назва екскурсії
    name1 = db.Column(db.String(50), nullable=False, unique=True)  # Унікальний ідентифікатор (наприклад, "karpatians")
    location = db.Column(db.String(100), nullable=False)  # Місце проведення екскурсії
    price = db.Column(db.Float, nullable=False)  # Ціна екскурсії
    start_date = db.Column(db.Date, nullable=False)  # Дата початку
    end_date = db.Column(db.Date, nullable=False)  # Дата завершення
    image = db.Column(db.String(200))  # Шлях до зображення
    opis = db.Column(db.Text)  # Опис екскурсії

    # Зворотний зв'язок із Booking
    bookings = db.relationship('Booking', back_populates='excursion')  # Усі бронювання для цієї екскурсії
    max_capacity = db.Column(db.Integer, nullable=True)



with app.app_context():
    db.create_all()

def send_notification(user_email, subject, body):
    # Приклад використання Flask-Mail для надсилання email

    msg = Message(subject, recipients=[user_email])
    msg.body = body
    try:
        mail.send(msg)
    except Exception as e:
        print(f"Помилка надсилання email: {e}")



@app.route('/feedback', methods=['POST'])
def feedback():
    # Перевіряємо, чи користувач увійшов у систему
    if 'user_id' not in session:
        return jsonify({'error': 'Користувач не авторизований'}), 403

    # Отримання JSON-запиту
    data = request.get_json()

    # Перевірка, чи всі поля присутні
    required_fields = ['name', 'email', 'mark', 'message']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'Поле "{field}" обов’язкове!'}), 400

    try:
        # Створення нового запису відгуку
        new_feedback = Feedback(
            user_id=session['user_id'],
            name=data['name'],
            email=data['email'],
            mark=data['mark'],
            message=data['message']
        )
        db.session.add(new_feedback)
        db.session.commit()

        return jsonify({'success': 'Ваш відгук успішно збережений!'}), 201
    except Exception as e:
        return jsonify({'error': 'Сталася помилка під час збереження відгуку', 'details': str(e)}), 500

    
@app.route('/feedback_history', methods=['GET'])
def feedback_history():
    feedbacks = Feedback.query.order_by(Feedback.created_at.desc()).all()  # Отримання всіх відгуків
    return render_template('feedback_history.html', feedbacks=feedbacks)

@app.route('/my_feedbacks', methods=['GET'])
def my_feedbacks():
    if 'user_id' not in session:
        flash('Будь ласка, увійдіть у свій акаунт.', 'warning')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    feedbacks = Feedback.query.filter_by(user_id=user_id).order_by(Feedback.created_at.desc()).all()
    
    return render_template('feedbacks.html', feedbacks=feedbacks)


@app.route('/book_trip', methods=['GET', 'POST'])
def book_trip():
    # Перевірка, чи користувач увійшов у систему
    if 'user_id' not in session:
        flash('Будь ласка, увійдіть у свій акаунт, щоб забронювати поїздку.', 'warning')
        return redirect(url_for('login'))  # Перенаправлення на вхід
    
    # Якщо користувач увійшов
    flash('Поїздка успішно заброньована!', 'success')
    return redirect(url_for('dashboard'))  # Перенаправлення в особистий кабінет

@app.route('/excursion/<name>')
def excursion(name):
    try:
        return render_template(f'{name}.html')
    except:
        return render_template('404.html'), 404

@app.route('/excursions')
def all_excursions():
    excursions = [
        {
            "image": "/static/images/Karpatians.jpg",
            "name": "Карпатський тур", 
            "name1": "karpatians",
            "location": "Карпати", 
            "price": 3000, 
            "start_date": "2024-01-10", 
            "end_date": "2024-01-15",
            "opis": "Досліджуйте чарівність Карпатських гір! Унікальні краєвиди, чисте повітря та гостинність чекають на вас."
        },
        {
            "image": "/static/images/Lviv.jpg",
            "name": "Львівські пригоди", 
            "name1": "Lviv",
            "location": "Львів", 
            "price": 2500, 
            "start_date": "2024-02-01", 
            "end_date": "2024-02-03",
            "opis": "Пориньте у казкову атмосферу старовинного Львова, його архітектуру та смаколики!"
        },
        {
            "image": "/static/images/kiev.jpg",
            "name": "Київський тур", 
            "name1": "Kiev",
            "location": "Київ", 
            "price": 2000, 
            "start_date": "2024-03-15", 
            "end_date": "2024-03-17",
            "opis": "Досліджуйте столицю України: Київ. Пориньте у багатство історії та сучасність цього великого міста."
        },
        {
            "image": "/static/images/Odesa.jpg",
            "name": "Одеса - перлина моря", 
            "name1": "Odesa",
            "location": "Одеса", 
            "price": 3500, 
            "start_date": "2024-06-24", 
            "end_date": "2024-07-24",
            "opis": "Відчуйте унікальну атмосферу Одеси з її морським узбережжям, архітектурою та гастрономією!"
        },
        {
            "image": "/static/images/Chornobil.jpg",
            "name": "Чорнобильський тур", 
            "name1": "Chornobil",
            "location": "Прип'ять", 
            "price": 4000, 
            "start_date": "2024-02-23",
            "end_date": "2024-03-03",
            "opis": "Пориньте в історію зони відчуження та дізнайтеся більше про наслідки катастрофи!"
        },
        {
            "image": "/static/images/vinnitsa.jpg",
            "name": "Вінницький фонтан", 
            "name1": "Vinnitsa",
            "location": "Вінниця", 
            "price": 1800, 
            "start_date": "2024-08-15", 
            "end_date": "2024-09-17",
            "opis": "Відвідайте світло-музичний фонтан Roshen, один із найбільших у Європі, який дарує магію та захоплення."
        },
        {
            "image": "/static/images/Буковель.jpg",
            "name": "Зимові розваги в Буковелі", 
            "name1": "bukovel",
            "location": "Буковель", 
            "price": 7000, 
            "start_date": "2024-09-10", 
            "end_date": "2024-09-25",
            "opis": "Відкрийте для себе найкращий зимовий курорт України – Буковель! Катання на лижах, сноуборді та незабутні емоції чекають на вас."
        },
        {
            "image": "/static/images/Kamin.jpg",
            "name": "Кам'янець-Подільський", 
            "name1": "KaminPod",
            "location": "Кам'янець-Подільський", 
            "price": 3000, 
            "start_date": "2024-10-01", 
            "end_date": "2024-11-03",
            "opis": "Відвідайте Кам'янець-Подільський – старовинне місто-фортецю з багатою історією та мальовничими краєвидами."
        },
        {
            "image": "/static/images/Poltava.jpg",
            "name": "Полтавські пригоди", 
            "name1": "poltava",
            "location": "Полтава", 
            "price": 2500, 
            "start_date": "2024-11-15", 
            "end_date": "2024-12-17",
            "opis": "Полтава – серце історії та культури! Відвідайте місця, які зберегли багатство української спадщини."
        }
    ]


    return render_template('all_excursions.html', excursions=excursions)


@app.route('/excursions/<name>')
def excursion_detail(name):
    excursions = [
        {
            "image": "/static/images/Karpatians.jpg",
            "name": "Карпатський тур", 
            "name1": "karpatians",
            "location": "Карпати", 
            "price": 3000, 
            "start_date": "2024-01-10", 
            "end_date": "2024-01-15",
            "opis": "Досліджуйте чарівність Карпатських гір! Унікальні краєвиди, чисте повітря та гостинність чекають на вас."
        },
        {
            "image": "/static/images/Lviv.jpg",
            "name": "Львівські пригоди", 
            "name1": "Lviv",
            "location": "Львів", 
            "price": 2500, 
            "start_date": "2024-02-01", 
            "end_date": "2024-02-03",
            "opis": "Пориньте у казкову атмосферу старовинного Львова, його архітектуру та смаколики!"
        },
        {
            "image": "/static/images/kiev.jpg",
            "name": "Київський тур", 
            "name1": "Kiev",
            "location": "Київ", 
            "price": 2000, 
            "start_date": "2024-03-15", 
            "end_date": "2024-03-17",
            "opis": "Досліджуйте столицю України: Київ. Пориньте у багатство історії та сучасність цього великого міста."
        },
        {
            "image": "/static/images/Odesa.jpg",
            "name": "Одеса - перлина моря", 
            "name1": "Odesa",
            "location": "Одеса", 
            "price": 3500, 
            "start_date": "2024-06-24", 
            "end_date": "2024-07-24",
            "opis": "Відчуйте унікальну атмосферу Одеси з її морським узбережжям, архітектурою та гастрономією!"
        },
        {
            "image": "/static/images/Chornobil.jpg",
            "name": "Чорнобильський тур", 
            "name1": "Chornobil",
            "location": "Прип'ять", 
            "price": 4000, 
            "start_date": "2024-02-23",
            "end_date": "2024-03-03",
            "opis": "Пориньте в історію зони відчуження та дізнайтеся більше про наслідки катастрофи!"
        },
        {
            "image": "/static/images/vinnitsa.jpg",
            "name": "Вінницький фонтан", 
            "name1": "Vinnitsa",
            "location": "Вінниця", 
            "price": 1800, 
            "start_date": "2024-08-15", 
            "end_date": "2024-09-17",
            "opis": "Відвідайте світло-музичний фонтан Roshen, один із найбільших у Європі, який дарує магію та захоплення."
        },
        {
            "image": "/static/images/Буковель.jpg",
            "name": "Зимові розваги в Буковелі", 
            "name1": "bukovel",
            "location": "Буковель", 
            "price": 7000, 
            "start_date": "2024-09-10", 
            "end_date": "2024-09-25",
            "opis": "Відкрийте для себе найкращий зимовий курорт України – Буковель! Катання на лижах, сноуборді та незабутні емоції чекають на вас."
        },
        {
            "image": "/static/images/Kamin.jpg",
            "name": "Кам'янець-Подільський", 
            "name1": "KaminPod",
            "location": "Кам'янець-Подільський", 
            "price": 3000, 
            "start_date": "2024-10-01", 
            "end_date": "2024-11-03",
            "opis": "Відвідайте Кам'янець-Подільський – старовинне місто-фортецю з багатою історією та мальовничими краєвидами."
        },
        {
            "image": "/static/images/Poltava.jpg",
            "name": "Полтавські пригоди", 
            "name1": "poltava",
            "location": "Полтава", 
            "price": 2500, 
            "start_date": "2024-11-15", 
            "end_date": "2024-12-17",
            "opis": "Полтава – серце історії та культури! Відвідайте місця, які зберегли багатство української спадщини."
        }
    ]

    excursion = next((exc for exc in excursions if exc["name1"] == name), None)
    if excursion is None:
        return render_template('404.html'), 404

    return render_template('excursion.html', excursion=excursion)

@app.route('/excursion/<int:excursion_id>', methods=['GET', 'POST'])
def excursion_details(excursion_id):
    # Отримання екскурсії з бази даних
    excursion = Excursion.query.get_or_404(excursion_id)
    is_booked = False

    # Перевірка, чи користувач увійшов у систему
    if 'user_id' in session:
        user_id = session['user_id']
        # Перевірка, чи вже є бронювання
        is_booked = Booking.query.filter_by(user_id=user_id, excursion_id=excursion_id).first() is not None

    if request.method == 'POST':
        # Якщо користувач не увійшов
        if 'user_id' not in session:
            flash("Будь ласка, увійдіть, щоб забронювати екскурсію.", "danger")
            return redirect(url_for('login'))

        user = User.query.get(session['user_id'])

        # Якщо вже заброньовано
        if is_booked:
            flash("Ви вже забронювали цю екскурсію.", "info")
            return redirect(url_for('excursion_details', excursion_id=excursion_id))

        # Перевірка балансу
        if user.balance < excursion.price:
            flash("Недостатньо коштів для бронювання.", "danger")
            return redirect(url_for('excursion_details', excursion_id=excursion_id))

        # Створення бронювання
        booking = Booking(user_id=user.id, excursion_id=excursion.id)
        user.balance -= excursion.price
        db.session.add(booking)
        db.session.commit()

        flash(f"Ви успішно забронювали екскурсію: {excursion.name}.", "success")
        return redirect(url_for('excursion_details', excursion_id=excursion_id))

    return render_template('excursion.html', excursion=excursion, is_booked=is_booked)

class TransactionLog(db.Model):
    __tablename__ = 'transaction_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())




@app.route('/book/<int:excursion_id>', methods=['POST'])
def book_excursion(excursion_id):
    if 'user_id' not in session:
        return jsonify({"message": "Будь ласка, увійдіть, щоб забронювати екскурсію."}), 401

    user_id = session['user_id']
    user = User.query.get(user_id)
    excursion = Excursion.query.get(excursion_id)

    # Перевірка, чи екскурсія існує
    if not excursion:
        return jsonify({"message": "Екскурсію не знайдено."}), 404

    # Перевірка, чи екскурсія вже заброньована цим користувачем
    existing_booking = Booking.query.filter_by(user_id=user_id, excursion_id=excursion_id).first()
    if existing_booking:
        return jsonify({"message": "Ви вже забронювали цю екскурсію."}), 400

    # Перевірка доступності місць
    max_capacity = excursion.max_capacity if hasattr(excursion, 'max_capacity') else None
    current_bookings = Booking.query.filter_by(excursion_id=excursion_id).count()

    if max_capacity and current_bookings >= max_capacity:
        return jsonify({"message": "Немає доступних місць для цієї екскурсії."}), 400

    # Перевірка балансу користувача
    if user.bonus_amount < excursion.price:
        return jsonify({"message": "Недостатньо коштів для бронювання."}), 400

    # Створення бронювання
    booking = Booking(user_id=user.id, excursion_id=excursion.id, status="Booked")
    db.session.add(booking)

    # Оновлення балансу користувача
    user.bonus_amount -= excursion.price

    # Логування транзакції (опціонально)
    transaction_log = TransactionLog(
        user_id=user.id,
        amount=excursion.price,
        description=f"Бронювання екскурсії: {excursion.name}"
    )
    db.session.add(transaction_log)

    # Оновлення статистики (наприклад, кількість заброньованих екскурсій користувача)
    user.total_bookings = user.total_bookings + 1 if hasattr(user, 'total_bookings') else 1

    # Надсилання сповіщення користувачу (опціонально, через email або інші сервіси)
    send_notification(
        user_email=user.email,
        subject="Бронювання успішне!",
        body=f"Ви успішно забронювали екскурсію: {excursion.name}. Очікуємо вас!"
    )

    # Збереження змін у базі даних
    db.session.commit()

    return jsonify({"message": f"Екскурсію '{excursion.name}' успішно заброньовано!"}), 200


@app.route('/api/user/bookings', methods=['GET'])
def get_user_bookings():
    if 'user_id' not in session:
        return jsonify({"message": "Будь ласка, увійдіть у систему."}), 401

    user_id = session['user_id']
    bookings = Booking.query.filter_by(user_id=user_id).all()
    result = []

    for booking in bookings:
        excursion = Excursion.query.get(booking.excursion_id)
        if excursion:
            result.append({
                "id": excursion.id,
                "name": excursion.name,
                "location": excursion.location,
                "price": excursion.price,
                "startDate": excursion.start_date.strftime('%Y-%m-%d'),
                "endDate": excursion.end_date.strftime('%Y-%m-%d'),
                "image": excursion.image,  # Додано поле для URL зображення
                "status": booking.status
            })

    return jsonify(result), 200


@app.route('/api/excursions', methods=['GET'])
def get_excursions():
    excursions = Excursion.query.all()
    user_bookings = []

    if 'user_id' in session:
        user_id = session['user_id']
        user_bookings = [b.excursion_id for b in Booking.query.filter_by(user_id=user_id).all()]

    result = []
    for excursion in excursions:
        status = "Booked" if excursion.id in user_bookings else "Available"
        result.append({
            "id": excursion.id,
            "name": excursion.name,
            "location": excursion.location,
            "price": excursion.price,
            "startDate": excursion.start_date.strftime('%Y-%m-%d'),
            "endDate": excursion.end_date.strftime('%Y-%m-%d'),
            "image": excursion.image,
            "description": excursion.opis,
            "status": status
        })
    return jsonify(result)

@app.route('/api/check_booking/<int:excursion_id>', methods=['GET'])
def check_booking(excursion_id):
    if 'user_id' not in session:
        return jsonify({"isBooked": False}), 401

    user_id = session['user_id']
    booking = Booking.query.filter_by(user_id=user_id, excursion_id=excursion_id).first()

    if booking:
        return jsonify({"isBooked": True}), 200
    else:
        return jsonify({"isBooked": False}), 200



# Функція входу
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Перевірка користувача
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['user_name'] = user.name
            flash('Успішний вхід!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Неправильний email або пароль.', 'danger')
    
    return render_template('Login.html')

# Функція реєстрації
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('Паролі не збігаються!', 'danger')
            return render_template('Register.html')

        # Перевірка чи користувач існує
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email вже зареєстровано.', 'danger')
            return render_template('Register.html')

        hashed_password = generate_password_hash(password)
        new_user = User(name=name, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Реєстрація успішна! Увійдіть у свій акаунт.', 'success')
        return redirect(url_for('login'))

    return render_template('Register.html')


# Функція для особистого кабінету
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Будь ласка, увійдіть у свій акаунт.', 'warning')
        return redirect(url_for('login'))
    
    # Замість User.query.get(session['user_id']):
    user = db.session.get(User, session['user_id'])

    if not user:
        flash('Користувач не знайдений.', 'danger')
        return redirect(url_for('login'))

    return render_template('Dashboard.html', user=user)



# Функція для виходу
@app.route('/logout')
def logout():
    # Очищення сесії
    session.clear()
    flash('Ви успішно вийшли з акаунту.', 'success')
    return redirect(url_for('login'))



@app.route('/')
def index():
    excursions = Excursion.query.all()
    user_bookings = []
    if 'user_id' in session:
        user_bookings = [b.excursion_id for b in Booking.query.filter_by(user_id=session['user_id']).all()]
    return render_template('index.html', excursions=excursions, user_bookings=user_bookings)


# Обробка помилок 404
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


if __name__ == '__main__':
    app.run(debug=True)


'''
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy

# Ініціалізація Flask
app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now())

# Головна сторінка
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/excursion/<name>')
def excursion(name):
    try:
        return render_template(f'{name}.html')
    except:
        return render_template('404.html'), 404

# Реєстрація
@app.route('/register', methods=['GET', 'POST'])
def register():
    error_message = None
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            error_message = 'Паролі не збігаються!'
            return render_template('Register.html', error_message=error_message)

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Користувач із таким email вже існує!', 'danger')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(name=name, email=email, password=hashed_password)

        db.session.add(new_user)
        db.session.commit()
        flash('Реєстрація успішна! Тепер увійдіть.', 'success')
        return redirect(url_for('login'))

    return render_template('Register.html', error_message=error_message)

# Авторизація
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Перевірка користувача в базі
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            # Збереження в сесії
            session['user_id'] = user.id
            flash('Вхід успішний!', 'success')
            return redirect(url_for('dashboard'))  # Перенаправлення до Dashboard
        else:
            flash('Невірний email або пароль!', 'danger')

    return render_template('Login.html')


@app.route('/dashboard')
def dashboard():
    user_id = session.get('user_id')
    if not user_id:
        flash('Будь ласка, увійдіть у систему.', 'warning')
        return redirect(url_for('login'))  # Якщо не увійшов, перенаправляємо до login

    # Отримання даних користувача
    user = User.query.get(user_id)
    if not user:
        flash('Користувач не знайдений!', 'danger')
        return redirect(url_for('login'))

    return render_template('Dashboard.html', user=user)


#вихід
@app.route('/logout')
def logout():
    session.pop('user_id', None)  # Видаляємо ID із сесії
    flash('Ви вийшли з акаунта.', 'success')
    return redirect(url_for('login'))


# Обробка помилок 404
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)'''
'''from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
#from data import db, User

# Ініціалізація Flask
app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///C:/Users/Користувач/OneDrive/Desktop/Kursova/Kursova/database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'
db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now())

    def __repr__(self):
        return f'<User {self.name}>'

# Підключення бази даних
#db.init_app(app)

# Створення бази даних
with app.app_context():
    db.create_all()

# Головна сторінка
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/excursion/<name>')
def excursion(name):
    try:
        return render_template(f'{name}.html')
    except:
        return render_template('404.html'), 404

# Сторінка авторизації
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Перевірка користувача
        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password, password):
            flash('Невірний email або пароль!', 'danger')
            return redirect(url_for('login'))

        flash(f'Вітаємо, {user.name}!', 'success')
        return redirect(url_for('index'))

    return render_template('Login.html')

# Сторінка реєстрації
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Перевірка паролів
        if password != confirm_password:
            flash('Паролі не збігаються!', 'danger')
            return redirect(url_for('register'))

        # Перевірка, чи email вже існує
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email вже зареєстровано!', 'danger')
            return redirect(url_for('register'))

        # Хешування паролю
        hashed_password = generate_password_hash(password, method='sha256')

        # Додавання користувача
        new_user = User(name=name, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash('Реєстрація успішна!', 'success')
        return redirect(url_for('login'))

    return render_template('Register.html')

@app.route('/dashboard')
def dashboard():
    return render_template('Dashboard.html')

# Обробка помилок 404
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run(debug=True)'''
'''from flask import *
from data import db
db.create_all()
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now())


app = Flask(__name__, static_folder='static', template_folder='templates')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/excursion/<name>')
def excursion(name):
    try:
        return render_template(f'{name}.html')
    except:
        return render_template('404.html'), 404


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Перевірка чи користувач існує
        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password, password):
            flash('Невірний email або пароль!', 'danger')
            return redirect(url_for('login'))

        flash(f'Вітаємо, {user.name}!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('Login.html')



@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirmPassword']

        # Перевірка паролів
        if password != confirm_password:
            flash('Паролі не збігаються!', 'danger')
            return redirect(url_for('register'))

        # Перевірка чи email вже існує
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email вже зареєстровано!', 'danger')
            return redirect(url_for('register'))

        # Захешований пароль
        hashed_password = generate_password_hash(password, method='sha256')

        # Додавання нового користувача
        new_user = User(name=name, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash('Реєстрація успішна!', 'success')
        return redirect(url_for('login'))

    return render_template('Register.html')


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run(debug=True)
'''
'''
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your_secret_key'

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now())

# Головна сторінка
@app.route('/')
def index():
    return render_template('index.html')

# Маршрут для реєстрації
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('Паролі не збігаються!', 'danger')
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash('Email уже зареєстровано!', 'danger')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password, method='sha256')
        new_user = User(name=name, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Реєстрація успішна!', 'success')
        return redirect(url_for('login'))

    return render_template('Register.html')

# Маршрут для авторизації
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if not user or not check_password_hash(user.password, password):
            flash('Невірний email або пароль!', 'danger')
            return redirect(url_for('login'))

        flash(f'Вітаємо, {user.name}!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('Login.html')

# Особистий кабінет
@app.route('/dashboard')
def dashboard():
    return render_template('Dashboard.html')

# Обробник помилок 404
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)'''
'''
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

# Ініціалізація Flask та SQLAlchemy
app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'
db = SQLAlchemy(app)

# Модель користувача
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

# Головна сторінка
@app.route('/')
def index():
    return render_template('index.html')

# Сторінка авторизації
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Перевірка користувача
        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password, password):
            flash('Невірний email або пароль!', 'danger')
            return redirect(url_for('login'))

        flash(f'Вітаємо, {user.name}!', 'success')
        return redirect(url_for('index'))

    return render_template('Login.html')

# Сторінка реєстрації
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Перевірка паролів
        if password != confirm_password:
            flash('Паролі не збігаються!', 'danger')
            return redirect(url_for('register'))

        # Перевірка, чи email вже існує
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email вже зареєстровано!', 'danger')
            return redirect(url_for('register'))

        # Хешування паролю
        hashed_password = generate_password_hash(password, method='sha256')

        # Додавання користувача
        new_user = User(name=name, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash('Реєстрація успішна!', 'success')
        return redirect(url_for('login'))

    return render_template('Register.html')

# Обробка помилок 404
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run(debug=True)
'''
