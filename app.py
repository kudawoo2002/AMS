from flask import Flask, request, render_template, url_for, redirect, flash, session, send_file
from datetime import datetime
from werkzeug import secure_filename
from functools import wraps
import sqlalchemy
import pandas
import MySQLdb


app = Flask(__name__)
app.config["SECRET_KEY"]="MYSECRET"
conn = MySQLdb.connect(host="localhost", user="sitou", password='1q2w3e', db='ams_db')
engine = sqlalchemy.create_engine("mysql://sitou:1q2w3e@localhost/ams_db")

def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            return redirect(url_for("login"))
    return wrap


@app.route("/logout/")
@login_required
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/",methods=['GET','POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        pwd = request.form['pwd']
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE name=%s AND password=%s",(username, pwd))
        data = cur.fetchone()
        if data:
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for("home"))
        else:
            error = 'Invalid Credentials. Please try again.'
            return render_template("index.html", error=error)

    return render_template("index.html", title="Sign Up")

@app.route("/home/")
@login_required
def home():
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM asserts WHERE assert_type='computer'")
    comp = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM asserts WHERE assert_type='car'")
    car = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM asserts WHERE assert_type='furniture'")
    fur = cur.fetchone()[0]
    cur.execute("SELECT * FROM asserts ORDER BY assert_id DESC LIMIT 3")
    data = cur.fetchall()
    return render_template("home.html",comp=comp, car=car,fur=fur,data=data)


@app.route("/add_assert/", methods=['GET','POST'])
@login_required
def add_assert():
    error = None
    if request.method == "POST":
        name = request.form["assert_name"].upper()
        code = request.form["code"].upper()
        type = request.form["assert_type"].upper()
        department = request.form["department"].upper()
        price = request.form["price_of_assert"]
        purchase_date = request.form["purchase_date"]
        d = datetime.strptime(purchase_date, "%Y-%m-%d")
        vendor = request.form["vendor"].upper()
        contact = request.form["contact"]
        try:
            cur = conn.cursor()
            cur.execute("INSERT INTO asserts(name, code, assert_type, department, price_of_assert, purchase_date, vendor, contact) "
            "VALUES(%s,%s,%s,%s,%s,%s,%s,%s)",(name, code, type, department, price, d, vendor, contact))
            conn.commit()

        except:
            error = "Please enter an ammount at (price of assert field) and (mobile at contact field)"
            return render_template("add_assert.html", error=error)
        flash("You have successfully insert the item !!!", "success")
    return render_template("add_assert.html")


@app.route("/view_assert/", methods=['GET','POST'])
@login_required
def view_assert():
    if request.method == "POST":
        search = request.form["search"].upper()
        cur = conn.cursor()
        cur.execute("SELECT * FROM asserts WHERE assert_type=%s",[search])
        data_table = cur.fetchall()
        return render_template("view_assert.html", data_table=data_table)
    else:
        cur = conn.cursor()
        cur.execute("SELECT * FROM asserts")
        data_table = cur.fetchall()
        return render_template("view_assert.html", data_table=data_table, btn="export.html")
    return render_template("view_assert.html", data_table=data_table)


@app.route("/upload", methods=["GET","POST"])
def upload():
        if request.method == "POST":
            cur = conn.cursor()
            file = request.files["inputfile"]
            df = pandas.read_csv(file)
            df.to_sql(name='asserts',con=engine, index=False, if_exists='append')
            return redirect(url_for("view_assert"))
        return render_template("import.html")


@app.route("/export")
def export():
    cur = conn.cursor()
    df = pandas.read_sql(("SELECT * FROM asserts"), con=conn)
    df.to_csv("data.csv")
    return send_file("data.csv", attachment_filename="data.csv", as_attachment=True)


@app.route("/edit_assert/<int:id>", methods=["GET", "POST"])
@login_required
def edit_assert(id):
    cur = conn.cursor()
    cur.execute("SELECT name, code, assert_type, department, price_of_assert, purchase_date, vendor, contact FROM asserts WHERE assert_id=%s",[id])
    data = cur.fetchone()
    if request.method == "GET":
        return render_template("edit_assert.html", id=id,data=data)
    if request.method == "POST":
        error = None
        name = request.form["assert_name"].upper()
        code = request.form["code"].upper()
        type = request.form["assert_type"].upper()
        department = request.form["department"].upper()
        price = request.form["price_of_assert"]
        purchase_date = request.form["purchase_date"]
        d = datetime.strptime(purchase_date, "%Y-%m-%d")
        vendor = request.form["vendor"].upper()
        contact = request.form["contact"]
        try:
            cur = conn.cursor()
            cur.execute("UPDATE asserts SET name=%s, code=%s, assert_type=%s, department=%s, price_of_assert=%s, purchase_date=%s, vendor=%s, contact=%s WHERE assert_id=%s",(name, code, type, department, price, d, vendor, contact, id))
            conn.commit()
        except:
            error = "Please enter an ammount at (price of assert field) and (mobile at contact field)"
            return render_template("edit_assert.html", error=error,id=id,data=data)
        return redirect(url_for("home")), flash("Upade was successful!!", "success")

    return render_template("edit_assert.html")

if __name__ == "__main__":
    app.run(debug=True)
