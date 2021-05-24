# accessing modules required to run the app
import os
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env

# instance of the the Flask class
app = Flask(__name__)

# set the config Key & values of the flask app
app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

# connects the flask app to the MongoDB server
mongo = PyMongo(app)


# binds the get_tasks function to the default routing / url view of the app
@app.route("/")
@app.route("/get_tasks")
def get_tasks():
    # finds a collection of tasks from db and returns a python list
    tasks = list(mongo.db.tasks.find())
    # render_template("tasks.html", tasks=task) renders the tasks.html template, from
    #  the templates folder, along with the "tasks" keyword variable
    return render_template("tasks.html", tasks=tasks)


# binds the "/search" url route to the search function, 
# with access to GET and POST HTTP methods for form submission
@app.route("/search", methods=["GET", "POST"])
def search():
    # gets user's input value from the "query" input 
    query = request.form.get("query")
    # finds the data that matches query search from the task collection database
    # and returns a python list
    tasks = list(mongo.db.tasks.find({"$text": {"$search": query}}))
    return render_template("tasks.html", tasks=tasks)


# binds the "/register" url route to the register function
@app.route("/register", methods=["GET", "POST"])
def register():
    # runs validation on HTTP POST request
    if request.method == "POST":
        # check if username already exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            # user flash feedback message  if username exist in database
            flash("Username already exists")
            # redirects user back to the 'register' function URL route
            return redirect(url_for("register"))

        # get new user's registration info from the register template
        register = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password"))
        }
        # add new user to the db
        mongo.db.users.insert_one(register)

        # put the new user into 'session' cookie
        session["user"] = request.form.get("username").lower()
        flash("Registration Successful!")
        # redirect user to the profile function url route, with keyword variable for username
        return redirect(url_for("profile", username=session["user"]))
    
    # renders the register.html template
    return render_template("register.html")


# binds the "/login" url route to the login function
@app.route("/login", methods=["GET", "POST"])
def login():
    # runs validation for POST request method
    if request.method == "POST":
        # check if username exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            # ensure hashed password matches user input
            if check_password_hash(
                    existing_user["password"], request.form.get("password")):

                        # put the user's name into 'session' cookie
                        session["user"] = request.form.get("username").lower()
                        # "flash" feedback message for user using String .format() Method
                        flash("Welcome, {}".format(
                            request.form.get("username")))
                        # redirects user to profile url route with the username
                        return redirect(url_for(
                            "profile", username=session["user"]))
            else:
                # invalid password match
                flash("Incorrect Username and/or Password")
                # redirect back to login route
                return redirect(url_for("login"))

        else:
            # username doesn't exist
            flash("Incorrect Username and/or Password")
            # redirects user back to login url route / view
            return redirect(url_for("login"))
    
    # renders the login.html template
    return render_template("login.html")


# binds the "/profile/<username>" url route to the profile(username) function
@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    # grab the session user's username from db
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]

    # renders the profile.html template if user logged in successfully 
    # with session["user"] cookie for confirmation
    if session["user"]:
        return render_template("profile.html", username=username)

    # redirects user to login function view if session["user"] has no user value
    return redirect(url_for("login"))


# binds the "/logout" url route to the logout() function
@app.route("/logout")
def logout():
    # remove user from session cookie
    flash("You have been logged out")
    session.pop("user")
    return redirect(url_for("login"))


# binds the /add_task url route to the dd_task() function
@app.route("/add_task", methods=["GET", "POST"])
def add_task():
    # executes functions when user sends a POST
    if request.method == "POST":
        # allows user to update urgency of task
        is_urgent = "on" if request.form.get("is_urgent") else "off"
        # gets user's requested POST data
        task = {
            "category_name": request.form.get("category_name"),
            "task_name": request.form.get("task_name"),
            "task_description": request.form.get("task_description"),
            "is_urgent": is_urgent,
            "due_date": request.form.get("due_date"),
            "created_by": session["user"]
        }
        # adds task data to the db
        mongo.db.tasks.insert_one(task)
        # flash message feedback for user
        flash("Task Successfully Added")
        # redirects user back to get_tasks function url route / view
        return redirect(url_for("get_tasks"))

    # gets the list of categories and sort them ascending by category name
    categories = mongo.db.categories.find().sort("category_name", 1)
    # renders the "add_task.html" with list of categories
    return render_template("add_task.html", categories=categories)


# binds the "/edit_task/<task_id>" url route to the edit_task(task_id) function
@app.route("/edit_task/<task_id>", methods=["GET", "POST"])
def edit_task(task_id):
    # executes functions when user sends a POST
    if request.method == "POST":
        # allows user to update urgency of task
        is_urgent = "on" if request.form.get("is_urgent") else "off"
        # gets user's update data for the task
        submit = {
            "category_name": request.form.get("category_name"),
            "task_name": request.form.get("task_name"),
            "task_description": request.form.get("task_description"),
            "is_urgent": is_urgent,
            "due_date": request.form.get("due_date"),
            "created_by": session["user"]
        }
        # updates the task in the db with new data and BSON ObjectID
        mongo.db.tasks.update({"_id": ObjectId(task_id)}, submit)
        # flash message feedback for the user
        flash("Task Successfully Updated")

    # gets task to be edited using BSON Object_ID
    task = mongo.db.tasks.find_one({"_id": ObjectId(task_id)})
    # gets the list of categories and sort them ascending by category name
    categories = mongo.db.categories.find().sort("category_name", 1)
    # renders the "edit_task.html" template with task and categories variables
    return render_template("edit_task.html", task=task, categories=categories)


# binds the "/delete_task/<task_id>" url route to the delete_task(task_id) function
@app.route("/delete_task/<task_id>")
def delete_task(task_id):
    # deletes the task for the selected ObjectId
    mongo.db.tasks.remove({"_id": ObjectId(task_id)})
    # user flash message feedback
    flash("Task Successfully Deleted")
    # redirects user to the "get_tasks" function url route / view
    return redirect(url_for("get_tasks"))


# binds the "/get_categories" url route to the get_categories() function
@app.route("/get_categories")
def get_categories():
    # gets all the categories ,sorted by category name, and returns python list element
    categories = list(mongo.db.categories.find().sort("category_name", 1))
    # renders the categories.html template along with the values for categories
    return render_template("categories.html", categories=categories)

# binds the "/add_category" url route to the add_category() function
@app.route("/add_category", methods=["GET", "POST"])
def add_category():
    if request.method == "POST":
        # grabs the category_name value when user submits request
        category = {
            "category_name": request.form.get("category_name")
        }
        # adds new category to db
        mongo.db.categories.insert_one(category)
        # flash message feedback for user
        flash("New Category Added")
        # redirects user to the get_categories function url route / view
        return redirect(url_for("get_categories"))
    
    # renders the "add_category.html" template
    return render_template("add_category.html")


# binds the "/edit_category/<category_id>" url route to the edit_category(category_id) function
@app.route("/edit_category/<category_id>", methods=["GET", "POST"])
def edit_category(category_id):
    if request.method == "POST":
        # grabs category name object submitted by user
        submit = {
            "category_name": request.form.get("category_name")
        }
        # updates the category for the selected id
        mongo.db.categories.update({"_id": ObjectId(category_id)}, submit)
        # flash message feedback for user
        flash("Category Successfully Updated")
        # redirects user to the "get_categories" function url route / view
        return redirect(url_for("get_categories"))

    # gets the selected category from the db
    category = mongo.db.categories.find_one({"_id": ObjectId(category_id)})
    # renders the "edit_category.html" template along with category keyword argument
    return render_template("edit_category.html", category=category)

# binds the "/delete_category/<category_id>" url route to the delete_category(category_id) function
@app.route("/delete_category/<category_id>")
def delete_category(category_id):
    # deletes selected category
    mongo.db.categories.remove({"_id": ObjectId(category_id)})
    #  user flash message feedback
    flash("Category Successfully Deleted")
    # redirect user to the "get_categories" function url route / view
    return redirect(url_for("get_categories"))

# runs the flask application as the main module
if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)