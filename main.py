from sre_constants import SUCCESS
from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import CreatePostForm, RegisterForm, LoginForm
from flask_gravatar import Gravatar
from functools import wraps
from sqlalchemy import Table, Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import lxml.html
import lxml.html.clean
import os


# git commit check omg

app = Flask(__name__)
app.config['SECRET_KEY'] = "SuperSecretKey"
    # os.environ.get("SECRET_KEY")
ckeditor = CKEditor(app)
Bootstrap(app)

##CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///test.db"
    # os.environ.get("DATABASE_URL1")
SQLALCHEMY_BINDS = {
    'users': 'sqlite:///users.db'
}
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)


## --------------------------- TABLES CREATION AND DECLARETION ----------------------------

class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String(250), nullable=False)
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)

    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    author = relationship("User", back_populates="posts")
    comments = relationship("Comment", back_populates="parent_post")

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(250), nullable=False)

    posts = relationship("BlogPost", back_populates="author")
    comments = relationship("Comment", back_populates="comment_author")

class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(50), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey("blog_posts.id"))

    parent_post = relationship("BlogPost", back_populates="comments")

    text = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    comment_author = relationship("User", back_populates="comments")

# enable if needed -----------
# db.create_all()
# ----------------------------

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # If id is not 1 then return abort with 403 error
        if current_user.id != 1:
            return abort(403)
        # Otherwise continue with the route function
        return f(*args, **kwargs)

    return decorated_function


@app.route('/')
def get_all_posts():
    posts = BlogPost.query.all()
    for i in posts:
        print(i.author.password)
    try:
        admin = current_user.id
        return render_template("index.html", all_posts=posts,
                               is_active=current_user.is_active,
                               is_admin=admin)
    except:
        return render_template("index.html", all_posts=posts,
                               is_active=current_user.is_active,
                               is_admin='0')


@app.route('/register', methods=['POST', 'GET'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        user_data = request.form.to_dict()
        print(user_data['email'])

        if user_data['email'] == User.query.filter_by(email=user_data['email']).first():
            flash('email already exist try to login')
            return redirect(url_for('login'))

        hashed_password = generate_password_hash(request.form.get('password'),
                                                 method='pbkdf2:sha256',
                                                 salt_length=8)

        data_to_database = User(name=request.form.get('name'), email=request.form.get('email'),
                                password=hashed_password)
        db.session.add(data_to_database)
        db.session.commit()
        return redirect(url_for('get_all_posts'))

    return render_template("register.html", form=form, is_active=current_user.is_active)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user_data = request.form.to_dict()

        try:
            user_database = User.query.filter_by(email=user_data['email']).first()
            if check_password_hash(user_database.password, password=user_data['password']):
                login_user(user_database)
                return redirect(url_for('get_all_posts'))
            else:
                flash('password incorrect')
                return redirect(url_for('login'))
        except:
            flash('incorrect email address')
            return redirect(url_for('login'))
    return render_template("login.html", form=form, is_active=current_user.is_active)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route("/post/<int:post_id>", methods=['GET', 'POST'])
def show_post(post_id):
    try:
        if current_user.id == 1:

            if request.method == 'POST':

                body_data = request.form.to_dict()
                doc = lxml.html.fromstring(body_data['ckeditor'])
                cleaner = lxml.html.clean.Cleaner(style=True)
                doc = cleaner.clean_html(doc)
                text = doc.text_content()

                comment_to_db = Comment(text=text, author_id=current_user.name, post_id=post_id)
                db.session.add(comment_to_db)
                db.session.commit()

            comments_to_display = Comment.query.all()


            requested_post = BlogPost.query.get(post_id)
            for i in comments_to_display:
                print(requested_post.id)
                print(i.post_id)
                if i.post_id == requested_post.id:
                    print( i.author_id)
                    print(requested_post.id)
            return render_template("post.html",
                                   post=requested_post,
                                   is_active=current_user.is_active,
                                   admin=1,
                                   comments=comments_to_display)
    except:
        comments_to_display = Comment.query.all()

        requested_post = BlogPost.query.get(post_id)
        return render_template("post.html",
                               post=requested_post,
                               is_active=current_user.is_active,
                               admin=0,
                               comments=comments_to_display)
    else:
        if request.method == 'POST':
            body_data = request.form.to_dict()
            doc = lxml.html.fromstring(body_data['ckeditor'])
            cleaner = lxml.html.clean.Cleaner(style=True)
            doc = cleaner.clean_html(doc)
            text = doc.text_content()

            comment_to_db = Comment(text=text, author_id=current_user.name, post_id=post_id)
            db.session.add(comment_to_db)
            db.session.commit()
        comments_to_display = Comment.query.all()

        requested_post = BlogPost.query.get(post_id)
        return render_template("post.html",
                               post=requested_post,
                               is_active=current_user.is_active,
                               admin=0,
                               comments=comments_to_display)


@app.route("/about")
def about():
    return render_template("about.html", is_active=current_user.is_active)


@app.route("/contact")
def contact():
    return render_template("contact.html", is_active=current_user.is_active)


@app.route("/new-post", methods=['GET', 'POST'])
@admin_only
def add_new_post():
    form = CreatePostForm()
    if request.method == 'POST':
        user_data = User.query.filter_by(id=current_user.id).first()

        print(current_user.name)
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form, is_active=current_user.is_active)


@app.route("/edit-post/<int:post_id>")
@admin_only
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.author = edit_form.author.data
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))

    return render_template("make-post.html", form=edit_form, is_active=current_user.is_active)


@app.route("/delete/<int:post_id>")
@login_required
@admin_only
def delete_post(post_id):
    try:
        post_to_delete = BlogPost.query.get(post_id)
        db.session.delete(post_to_delete)
        db.session.commit()
        return redirect(url_for('get_all_posts'))
    except:
        return redirect(url_for('login'))


@app.route('/comment_del/<int:comment_id>/<int:post_id>')
@login_required
@admin_only
def comment_delete(comment_id,post_id):
        comment_to_delete = Comment.query.get(comment_id)
        db.session.delete(comment_to_delete)
        db.session.commit()
        return redirect(url_for('show_post', post_id=post_id ))
    
   

        
if __name__ == "__main__":
    app.run()
