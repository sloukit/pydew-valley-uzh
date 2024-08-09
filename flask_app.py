"""
I made a simple flask app that creates a SQLAlchemy database that stores simple information like the email, password and token.

To make it work locally you have to install quite some modules.
http://127.0.0.1:5000/

The database is now filed with two user testcases, what you can do is delete the site.db from the data / database directory to test the user creation for yourself

You can adapt the code to use another database to store the user information in.
"""

import os
from flask import Flask, request, render_template
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity,
)
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import UserMixin
from flask_migrate import Migrate
import hashlib

app = Flask(__name__)

# this finds the route to store the database to the data / database directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '.'))

db_dir = os.path.join(project_root, 'data', 'database')

if not os.path.exists(db_dir):
    os.makedirs(db_dir)

app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(db_dir, 'site.db')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Configuration
app.config["SECRET_KEY"] = "your_strong_secret_key"
app.config["JWT_SECRET_KEY"] = "your_jwt_secret_key"
app.config["JWT_TOKEN_LOCATION"] = ["headers"]

# Database Initialization
db = SQLAlchemy(app)
migrate = Migrate(app, db)
bcrypt = Bcrypt(app)

# JWT Initialization
jwt = JWTManager(app)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    token = db.Column(db.String(80), nullable=True)
    is_active = db.Column(
        db.Boolean, default=True
    )  # i made this variable that we can enable or disable tokens in the future if people abuse the system

    def __repr__(self):
        return f"<User {self.email}>"


def generate_token(email, password):
    token_string = email + password
    return hashlib.sha256(token_string.encode()).hexdigest()


@app.route("/get_name", methods=["GET"])
@jwt_required()
def get_name():
    """Extract the user id from the JWT"""
    user_id = get_jwt_identity()
    user = User.query.filter_by(id=user_id).first()

    # check if user exists
    if user:
        return render_template("result.html", message="User found", email=user.email)
    else:
        return render_template("result.html", message="User not found"), 404


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        token = generate_token(email, password)

        user = User.query.filter_by(email=email).first()

        if user and user.token == token:
            access_token = create_access_token(identity=user.id)
            return render_template(
                "result.html", message="Login Success", access_token=access_token
            )
        else:
            return render_template("result.html", message="Login Failed")
    return render_template("login.html")


@app.route("/generate_token", methods=["POST"])
def generate_new_token():
    email = request.form["email"]
    password = request.form["password"]
    user = User.query.filter_by(email=email).first()

    if user:
        new_token = generate_token(email, password)
        user.token = new_token
        db.session.commit()
        return render_template(
            "result.html",
            message="Token generated successfully",
            email=email,
            token=new_token,
        )
    else:
        return render_template("result.html", message="User not found")


@app.route("/create_user", methods=["POST"])
def create_user():
    email = request.form["email"]
    password = request.form["password"]
    token = generate_token(email, password)
    hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
    new_user = User(email=email, password=hashed_password, token=token)

    db.session.add(new_user)
    db.session.commit()

    return render_template(
        "result.html", message="User created successfully", email=email, token=token
    )


@app.route("/")
def home():
    return render_template("login.html")


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
