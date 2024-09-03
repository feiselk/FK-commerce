from flask import Flask, render_template, jsonify, request, redirect, url_for, session, send_from_directory, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
from werkzeug.utils import secure_filename
from datetime import datetime


app = Flask(name)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///amco.db'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

app.config['ALLOWED_EXTENSIONS_VIDEO'] = {}

db = SQLAlchemy(app)
migrate = Migrate(app, db)
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'uploads')

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

class ActionHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    entity_type = db.Column(db.String(50))
    entity_id = db.Column(db.Integer)
    action = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    details = db.Column(db.Text)

    def init(self, entity_type, entity_id, action, details):
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.action = action
        self.details = details


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    image = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)

    def log_action(self, action, details):
        log_entry = ActionHistory(
            entity_type='Product',
            entity_id=self.id,
            action=action,
            details=details
        )
        db.session.add(log_entry)
        db.session.commit()

    
@app.route('/prod')
def p_page():
    products = Product.query.all()
    return render_template('prod.html', products=products)

app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.route('/login/admin',methods=['GET','POST'])
def admin():
    if 'admin_logged_in' not in session or not session['admin_logged_in']:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
    products = Product.query.all()
    return render_template('admin.html', products=products)



@app.route('/admin/add_product', methods=['GET', 'POST'])
def add_product():
    if 'admin_logged_in' not in session or not session['admin_logged_in']:
        return redirect(url_for('login'))
    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        description = request.form['description']

        if 'image' in request.files:
            image_file = request.files['image']
            if image_file.filename != '':
                filename = secure_filename(image_file.filename)
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                image_file.save(image_path)
            else:
                flash('No image selected.', 'error')
                return redirect(request.url)

        new_product = Product(name=name, price=price, image=filename, description=description)
        db.session.add(new_product)
        db.session.commit()
        
        new_product.log_action('Added', f"Product '{name}' added successfully.")

        flash('Product added successfully.', 'success')
        return redirect(url_for('admin'))
    return render_template('add_product.html')