from flask import Flask,render_template, flash,redirect, url_for ,session,logging,request
from functools import wraps

from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import  sha256_crypt


app=Flask(__name__)

#Config Mysql
app.config["MYSQL_HOST"]="localhost"
app.config["MYSQL_USER"]="root"
app.config["MYSQL_PASSWORD"]="password123"
app.config["MYSQL_DB"]="myflaskapp"
app.config["MYSQL_CURSORCLASS"]="DictCursor"
#init MYSQL
mysql=MySQL(app)


#Articles=Articles() #funzione che ho importato da data.py

@app.route("/home")
def profile():
    return render_template("home.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/articles")
def articles():
    # create cursor
    cur = mysql.connection.cursor()

    # get articles
    result = cur.execute("select * from articles")

    articles = cur.fetchall()

    if result > 0:
        return render_template("articles.html", articles=articles)
    else:
        msg = "no articles found"
        return render_template("articles.html", msg=msg)

    # close connection
    cur.close()


#single article
@app.route("/article/<string:id>")
def article(id):
    # create cursor
    cur = mysql.connection.cursor()

    # get article
    result = cur.execute("select * from articles where id=%s",(id))

    article = cur.fetchone()


    return render_template("article.html",article=article)




class RegisterForm(Form):
    name=StringField("Name",[validators.Length(min=1,max=50)])
    username=StringField("Username",[validators.Length(min=4,max=25)])
    email=StringField("Email",[validators.Length(min=6,max=50)])
    password=PasswordField("Passsword",[
        validators.data_required(),
        validators.equal_to("confirm",message="password do not match")])
    confirm=PasswordField("Confirm Password")


#user register
@app.route("/register",methods=["GET","POST"])
def register():
    form =RegisterForm(request.form)
    if request.method=="POST" and form.validate():
        name=form.name.data
        email=form.email.data
        username=form.username.data
        password=sha256_crypt.encrypt(str(form.password.data))

        #create a cursor
        cur=mysql.connection.cursor()

        #execute query
        cur.execute("INSERT INTO users(name,email,username,password) VALUES(%s,%s,%s,%s)",(name,email,username,password))

        #Commit to DB
        mysql.connection.commit()

        #Colse connection
        cur.close()

        flash("you are now registered and can log in","success")

        return redirect(url_for("profile"))


    return render_template("register.html",form=form)


#user login
@app.route("/login",methods=["GET","POST"])
def login():
    if request.method=="POST":
        #get form fields

        username=request.form["username"]
        password_candidate=request.form["password"]

        #create cursor
        cur=mysql.connection.cursor()

        #get user by username
        result=cur.execute("SELECT * from users where username= %s",[username])

        if result > 0:
            #get stored hash
            data=cur.fetchone()
            password=data["password"]

            #compare passwords
            if sha256_crypt.verify(password_candidate,password):
                #Passed
                session["logged_in"]=True
                session["username"]=username

                flash("your are now loggegd in","success")
                return redirect(url_for("dashboard"))

            else:
                error = "invalid login"
                return render_template("login.html",error=error)

            #closeconnection
            cur.close()

        else:
            error="username not found"
            return render_template("login.html",error=error)


    return render_template("login.html")




#check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args,**kwargs):
        if"logged_in" in session:
            return f(*args,**kwargs)
        else:
            flash("unauthorized,Please log in","danger")
            return redirect(url_for("login"))
    return wrap



#logout
@app.route("/logout")
@is_logged_in
def logout():
    session.clear()
    flash("you are now logged out","success")
    return redirect(url_for("login"))



#dashbopard
@app.route("/dashboard")
@is_logged_in
def dashboard():
    #create cursor
    cur = mysql.connection.cursor()

    #get articles
    result=cur.execute("select * from articles")

    articles=cur.fetchall()

    if result > 0:
        return render_template("dashboard.html",articles=articles)
    else:
        msg="no articles found"
        return render_template("dashboard.html",msg=msg)

    #close connection
    cur.close()




#Article form class
class ArticleForm(Form):
    title=StringField("Title",[validators.Length(min=1,max=200)])
    body=TextAreaField("Body",[validators.Length(min=30)])


#add article
@app.route("/add_article",methods=["GET","POST"])
@is_logged_in
def add_article():
    form=ArticleForm(request.form)
    if request.method=="POST" and form.validate():
        title=form.title.data
        body=form.body.data

        #create cursor
        cur =mysql.connection.cursor()

        #execute
        cur.execute("insert into articles(title,body,author) values(%s,%s,%s)",(title,body,session['username']))

        #commit
        mysql.connection.commit()

        #close connection
        cur.close()

        flash=("article created","success")

        return redirect(url_for("dashboard"))

    return render_template("add_article.html",form=form)





#edit article
@app.route("/edit_article/<string:id>",methods=["GET","POST"])
@is_logged_in
def edit_article(id):
    #create cursor
    cur=mysql.connection.cursor()

    #get article by id
    result =cur.execute("select * from articles where id=%s",(id))

    article=cur.fetchone()

    #get form
    form=ArticleForm(request.form)

    #populate articles form fields
    form.title.data=article["title"]
    form.body.data = article["body"]

    if request.method=="POST" and form.validate():
        title=request.form["title"]
        body=request.form["body"]


        #create cursor
        cur =mysql.connection.cursor()
        app.logger.info(title)

        #execute
        cur.execute("update articles set title=%s,body=%s where id =%s",(title,body,id))

        #commit
        mysql.connection.commit()

        #close connection
        cur.close()

        flash=("article updated","success")

        return redirect(url_for("dashboard"))

    return render_template("add_article.html",form=form)

#delete article
@app.route("/delete_article/<string:id>",methods=["POST"])
@is_logged_in
def delete_article(id):

    #create cursor
    cur=mysql.connection.cursor()

    #execute
    cur.execute("delete from articles where id=%s",(id))

    #commit
    mysql.connection.commit()


    cur.close()

    flash("article deleted","success")


    return redirect(url_for("dashboard"))







if __name__=="__main__":
    app.secret_key="secret123"
    app.run(debug=True)


