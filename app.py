from flask import Flask, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Change this to a strong secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# Load user session
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# User model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

# Login Form
class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=4, max=25)])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")

@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.password == form.password.data:  # Simple password check (use hashing in production)
            login_user(user)
            flash("Login successful!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password", "danger")
    return render_template("login.html", form=form)

@app.route("/dashboard")
@login_required
def dashboard():
    return "Welcome to your dashboard!"

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out", "info")
    return redirect(url_for("login"))

if __name__ == "__main__":
    db.create_all()
    app.run(debug=True)
