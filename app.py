from flask import Flask
from flask import render_template, url_for, session, request, json, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import send_from_directory, send_file
import os

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///data.db"
app.add_url_rule("/uploads/<name>", endpoint="download_file", build_only=True)
app.secret_key = "th45u4=fdgj-*'eferet"
app.config[
    "UPLOAD_FOLDER"
] = "C:\\Users\\path\\to\\static\\uploaded_files"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.add_url_rule("/download_file/<name>", endpoint="download_file", build_only=True)
db = SQLAlchemy(app)
ALLOWED_EXTENSIONS = {
    "txt",
    "pdf",
    "png",
    "jpg",
    "jpeg",
    "gif",
    "docx",
    "zip",
    "rar",
    "exe",
    "mp4",
    "mp3",
}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# Make data base columns
class Contact(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    phone = db.Column(db.String, nullable=False)
    message = db.Column(db.String(500), nullable=False)

    def __repr__(self):

        return f"{self.sno} - {self.name}"


class Files(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    file_name = db.Column(db.String(800), nullable=False)

    def __repr__(self):
        return f"{self.sno} - {self.file_name}"

# Create the database
with app.app_context():
    db.create_all()

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if "file" not in request.files:
            flash("No file part")
            return redirect(request.url)
        file = request.files["file"]
        file.filename = file.filename.replace(" ", "-")
        if file.filename == "":
            flash("Please select atleast one file", "danger")
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            flash("Uploaded Successfully", "success")
            files = Files(file_name=file.filename)
            db.session.add(files)
            db.session.commit()
    return render_template("index.html")


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name")
        phone = request.form.get("phone")
        message = request.form.get("message")
        contact = Contact(name=name, phone=phone, message=message)
        db.session.add(contact)
        db.session.commit()
        flash("Message sent successfully", "success")
        return redirect("/")
    return render_template("contact.html")


@app.route("/signin", methods=["GET", "POST"])
def signin():
    contacts = Contact.query.all()
    if "user" in session and session["user"] == "admin":
        return render_template("admin_portal.html", contacts=contacts)
    if request.method == "POST":
        uname = request.form.get("username")
        upass = request.form.get("password")
        if uname == "admin" and upass == "admin":
            session["user"] = uname
            return render_template("admin_portal.html", contacts=contacts)
        else:
            return redirect("/signin")
    return render_template("signin.html")


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/")


@app.route("/delete/<int:sno>")
def delete(sno):
    contact = Contact.query.filter_by(sno=sno).first()
    db.session.delete(contact)
    db.session.commit()
    return redirect("/signin")


@app.route("/update/<int:sno>", methods=["GET", "POST"])
def update(sno, methods=["GET", "POST"]):
    if "user" in session and session["user"] == "admin":
        if request.method == "POST":
            name = request.form.get("name")
            phone = request.form.get("phone")
            message = request.form.get("message")
            updated_msg = Contact.query.filter_by(sno=sno).first()
            updated_msg.name = name
            updated_msg.phone = phone
            updated_msg.message = message
            db.session.add(updated_msg)
            db.session.commit()
            return redirect("/signin")
    updated_msg = Contact.query.filter_by(sno=sno).first()
    return render_template("update.html", updated_msg=updated_msg)


@app.route("/files")
def files():
    newfile = Files.query.all()
    if "user" in session and session["user"] == "admin":
        return render_template("uploaded_files.html", newfile=newfile)
    return redirect("/signin")


@app.route("/deletefile/<int:sno>")
def deletefile(sno):
    file = Files.query.filter_by(sno=sno).first()
    db.session.delete(file)
    db.session.commit()
    return redirect("/files")


@app.route("/download_file/<name>")
def download_file(name):
    file = Files.query.filter_by(file_name=name).first()
    return send_from_directory(app.config["UPLOAD_FOLDER"], name)


@app.errorhandler(404)
def page_not_found(e):
    return "BAD REQUEST", 404


if __name__ == "__main__":
    app.run(debug=True)
