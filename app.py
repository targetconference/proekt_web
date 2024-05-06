from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, url_for, redirect, flash, request
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FloatField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
import json
from wtforms import SelectField


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///base.db'
app.config['SECRET_KEY'] = 'dvvrevf87fdvkey'
db = SQLAlchemy(app)
admin = Admin(app, template_mode='bootstrap4')
migrate = Migrate(app, db)
bcrypt = Bcrypt(app)


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Registerform(FlaskForm):
	"""Регистрация пользоватля """
	username = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Логин"})
	password = PasswordField(validators=[InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Пароль"})

	submit = SubmitField('Зарегистрироваться')

	def validate_username(self,username):
		existing_user_username = User.query.filter_by(username=username.data).first()
		if existing_user_username:
			raise ValidationError('Это имя пользователя уже существует. Пожалуйста, выберите другой вариант.')


class Loginform(FlaskForm):
	"""Вход пользователя """
	username = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Логин"})
	password = PasswordField(validators=[InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Пароль"})
	submit = SubmitField('Войти')


class AdminView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin()

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login'))


# Модель для продуктов в базе данных
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(20), nullable=True) 
    username = db.Column(db.String(30), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)
	
    def is_admin(self):
        return self.role == 'admin'


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(200), nullable=True)
    price = db.Column(db.Float, nullable=False)
    image = db.Column(db.String(200), nullable=True)
    category = db.Column(db.String(80), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)


class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    payment = db.Column(db.String(20), nullable=False)
    card_name = db.Column(db.String(255), nullable=False)
    card_number = db.Column(db.String(16), nullable=False)
    expiration = db.Column(db.String(7), nullable=False)
    cvv = db.Column(db.String(4), nullable=False)
    product_info = db.Column(db.String(500), nullable=True)


class AddProductForm(FlaskForm):
    name = StringField('Название', validators=[InputRequired()])
    description = StringField('Описание')
    price = FloatField('Цена', validators=[InputRequired()])
    image = StringField('Изображение')
    category = SelectField('Категория', choices=[
        ('Лекарства', 'Лекарства'),
        ('Витамины', 'Витамины'),
        ('Красота', 'Красота'),
        ('Гигиена', 'Гигиена'),
        ('Медтовары', 'Медтовары')
    ], validators=[InputRequired()])


class PriceAdminView(ModelView):
    column_list = ['name', 'description', 'price', 'category']
    create_form = AddProductForm 


admin.add_view(PriceAdminView(Product, db.session))
admin.add_view(AdminView(User, db.session))
admin.add_view(AdminView(CartItem, db.session))
admin.add_view(AdminView(Order, db.session))


@app.route('/login', methods=['GET', 'POST'])
def login():
	form = Loginform()
	if form.validate_on_submit():
		user = User.query.filter_by(username=form.username.data, password=form.password.data).first()
		if user:
			login_user(user)
			return redirect(url_for('index'))
	return render_template('login.html', form=form)


@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
	logout_user()
	return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
	form = Registerform()
	"""Кеширует пароль"""
	if form.validate_on_submit():
		new_user = User(username=form.username.data, password=form.password.data) 
		db.session.add(new_user)
		db.session.commit()

		return redirect(url_for('login'))

	return render_template('register.html', form=form)


@app.route('/')
def index():
    if current_user.is_authenticated:
        cart_item_count = get_cart_item_count()
        products = Product.query.all()[:3]
        return render_template('index.html', products=products, cart_item_count=cart_item_count)
    else:
        products = Product.query.all()[:3]
        return render_template('index.html', products=products) 


@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('product_detail.html', product=product)


@app.route('/shop', strict_slashes=False)
def shop():
    if current_user.is_authenticated:
        cart_item_count = get_cart_item_count()
        products = Product.query.all() 
        return render_template('shop.html', products=products, cart_item_count=cart_item_count)
    else:
        products = Product.query.all() 
        return render_template('shop.html', products=products)


@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    user = current_user
    cart_item = CartItem.query.filter_by(user_id=user.id, product_id=product_id).first()
    if cart_item:
        cart_item.quantity += 1
    else:
        cart_item = CartItem(user_id=user.id, product_id=product_id, quantity=1)
    db.session.add(cart_item)
    db.session.commit()

    flash('success', 'Продукт успешно добавлен в корзину')
    return redirect(url_for('shop'))


@app.route('/cart')
@login_required
def cart():
    user = current_user
    cart_items = CartItem.query.filter_by(user_id=user.id).all()

    cart_products = []
    total_amount = 0 
    for item in cart_items:
        product = Product.query.get(item.product_id)
        if product:
            cart_products.append({'product': product, 'quantity': item.quantity})
            total_amount += product.price * item.quantity 

    return render_template('cart.html', cart_products=cart_products, total_amount=total_amount)


@app.route('/orders')
@login_required
def admin_orders():
    if not current_user.is_admin():
        return render_template('login.html') 

    orders = Order.query.all()
    orders_info = []

    for order in orders:
        try:
            products_info = json.loads(order.product_info) if order.product_info else []
        except json.JSONDecodeError:
            flash('Ошибка при разборе информации о продуктах для заказа №{}'.format(order.id), 'error')
            continue

        order_info = {
            'order_id': order.id,
            'name': order.name,
            'email': order.email,
            'phone': order.phone,
            'total': sum(item['price'] * item['quantity'] for item in products_info['products']),
            'products': products_info['products'],
        }
        orders_info.append(order_info)

    return render_template('admin_orders.html', orders=orders_info)


@app.route('/my_orders')
@login_required
def my_orders():
    user = current_user
    orders = Order.query.filter_by(user_id=user.id).all()
    orders_info = []

    for order in orders:
        try:
            products_info = json.loads(order.product_info) if order.product_info else []
        except json.JSONDecodeError:
            flash('Ошибка при разборе информации о продуктах для заказа №{}'.format(order.id), 'error')
            continue

        order_info = {
            'order_id': order.id,
            'name': order.name,
            'email': order.email,
            'phone': order.phone,
            'total': sum(item['price'] * item['quantity'] for item in products_info['products']),
            'products': products_info['products'],
        }
        orders_info.append(order_info)

    return render_template('my_orders.html', orders=orders_info)


@app.route('/remove_from_cart/<int:product_id>', methods=['POST'])
@login_required
def remove_from_cart(product_id):
    user = current_user
    cart_item = CartItem.query.filter_by(user_id=user.id, product_id=product_id).first()
    if cart_item:
        db.session.delete(cart_item)
        db.session.commit()

    flash('success', 'Продукт успешно удален с корзины')
    return redirect(url_for('cart'))


@app.route('/place_order', methods=['POST'])
def place_order():
    if request.method == 'POST':
        name = request.form.get('name')
        address = request.form.get('address')
        email = request.form.get('email')
        phone = request.form.get('phone')
        payment = request.form.get('payment')
        card_name = request.form.get('card_name')
        card_number = request.form.get('card_number')
        expiration = request.form.get('expiration')
        cvv = request.form.get('cvv')

        order = Order(name=name, address=address, email=email, phone=phone, payment=payment, card_name=card_name, card_number=card_number, expiration=expiration, cvv=cvv)
        
        user = current_user
        cart_items = CartItem.query.filter_by(user_id=user.id).all()
        products_info = []
        
        total_price = 0
        for item in cart_items:
            product = Product.query.get(item.product_id)
            if product:
                product_info = {
                    'id': product.id,
                    'name': product.name,
                    'price': product.price,
                    'quantity': item.quantity,
                    'image': product.image
                }
                products_info.append(product_info)
                total_price += product.price * item.quantity

        order_info = {
            'products': products_info,
            'total_price': total_price
        }

        order = Order(
            user_id=user.id, 
            name=name,
            address=address,
            email=email,
            phone=phone,
            payment=payment,
            card_name=card_name,
            card_number=card_number,
            expiration=expiration,
            cvv=cvv,
            product_info=json.dumps(order_info, ensure_ascii=False)
        )
        
        db.session.add(order)
        db.session.commit()

        CartItem.query.filter_by(user_id=user.id).delete()
        db.session.commit()

        return redirect(url_for('order_confirmation'))

    return redirect(url_for('cart'))


def get_cart_item_count():
    user = current_user
    cart_item_count = CartItem.query.filter_by(user_id=user.id).count()
    return cart_item_count


@app.route('/about')
def service():
    if current_user.is_authenticated:
        cart_item_count = get_cart_item_count()
        return render_template('about.html', cart_item_count=cart_item_count)
    else:
        return render_template('about.html') 


@app.route('/order_confirmation')
def order_confirmation():
    order = Order.query.all()
    return render_template('order_confirmation.html', order=order)


@app.route('/orders_user')
@login_required
def orders_user():
    user = current_user
    cart_item_orders = Order.query.filter_by(id=user.id)
    return render_template('orders_user.html', cart_item_orders=cart_item_orders)


if __name__ == '__main__':
    app.run(debug=True)
