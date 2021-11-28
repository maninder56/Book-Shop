from flask import Flask
from markupsafe import escape
from flask import url_for
from flask import render_template
from flask import request
from flask import redirect
from flask import abort
from flask import make_response
from flask import session
from flask import flash
import sqlite3
from flask import g
import functools
import os

app = Flask(__name__)
app.secret_key = 'book_shop'

@app.before_request
def user_logged_in():
    user_id = session.get('user')
    if user_id is None:
        g.user = None
    else:
        g.user = 'set'

def admin_login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        admin = session.get('admin')
        if g.user is None or admin !='1':
            flash("Admin Login required", "info")
            return redirect(url_for('login'))
        return view(**kwargs) 
    return wrapped_view


# home function displays books, user information, total cart itmes and total price 
@app.route('/')
def home():
    conn = sqlite3.connect('book_shop.sqlite3') # connect to the database 
    cur = conn.cursor()# set cursor 
    cur.execute(f"SELECT book_name,book_picture, book_retail_price,\
              book_ISBN FROM stock ;")# SQLite Query to get  all the books 
    book_data = cur.fetchall() # fetch all the data
    conn.commit() # commit SQLite query 
    conn.close() # close SQLite

    if "user" in session: # if user in session 
        user = session["user"] #set a variable to session 
        user_info = "Logged in as: " # set variable to string 
    else: # if user is not in session, set variables empty 
        user_info = "" 
        user = ""

    if "items" in session: # if items in session 
        items = session["items"] # set variable to item in session 
        price = session["price"] # set variabel to price in sesion 
    else: # if not , set them to empty 
        items = ""
        price = ""

    return render_template('home.html', books=book_data,\
         user_info=user_info,user=user,
         total_items=items, total=price ) # Render home.html and pass books data, user, items and price  



@app.route('/login', methods=['GET', 'POST'])
def login():#login function displays login form and checks if user is in session 
    if request.method == 'POST': #if form is submitted
        return do_login(request.form['uname'], request.form['pwd'])# send user info to do_login 
    else:
        if "user" in session: # check if user in session 
            flash("Already logged in", "info")# message if user is already logged in
            return redirect(url_for('home')) # rediret to home page 
        return show_login_form()# if not show login form 

def show_login_form(): # show login form 
    return render_template('login.html', login_form=url_for('login'))



def do_login(username, password):
    conn = sqlite3.connect('book_shop.sqlite3')
    cur = conn.cursor()
    cur.execute(f"SELECT user_password FROM user WHERE user_name = '{username}';")
    password_data = cur.fetchone()
    conn.commit()
    cur.execute(f"SELECT admin FROM user WHERE user_name ='{username}';")
    admin_data = cur.fetchone()
    conn.commit()
    conn.close()

    if password_data is None or admin_data is None: # if password data or admin_data is None 
        #shows message: username or password incorect
        flash("username or password incorrect ", "info")
        return redirect(url_for('login')) # redirect to login function 

    if password == str(password_data[0]): # if given password is equal to password stored in database 
        session['user'] = request.form['uname'] # set user in session 

        if str(admin_data[0]) =='1': # if admin data is True 
            session['admin'] = str(admin_data[0])
            flash("You have been logged in as Admin", "info")
            return redirect(url_for('home'))

        # add message: logged in as ____
        flash("You have been logged in", "info")
        return redirect(url_for('home'))

    #show message: username or password incorect
    flash("username or password incorrect ", "info")
    return redirect(url_for('login'))

#logout
@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('admin', None)
    flash("You have been logged out","info")
    return redirect(url_for('home'))



#stocks should display the books that have been added to stock using the form from
@app.route('/stock_levels')
@admin_login_required
def stock_levels():
    conn = sqlite3.connect('book_shop.sqlite3')
    cur = conn.cursor()
    cur.execute(f"SELECT book_picture, book_name, book_ISBN, book_quantity FROM stock ;")
    book_data = cur.fetchall()
    conn.commit()
    conn.close()
    return render_template('stock_levels.html', books=book_data)



app.config["picture_path"]= 'C:/Users/User/Google Drive/Uni/Year_2/Semester_1/Software Engineering/Code/Practice/Website/static/images/product_images'

#a form where they can add new books to the system
@app.route('/add_stock', methods=['GET', 'POST'])
@admin_login_required
def add_stock():
    if request.method == 'POST':
        book_name = request.form['book_name']
        book_author = request.form['book_author']
        book_date = request.form['book_date']
        book_ISBN = request.form['book_ISBN']
        book_description = request.form['book_description']
        book_picture = request.files['book_picture']
        book_trade_price = request.form['book_trade_price']
        book_retail_price = request.form['book_retail_price']
        book_quantity = request.form['book_quantity']

        try:
            # add function to automatically add book_id
            conn = sqlite3.connect('book_shop.sqlite3')
            cur = conn.cursor()

            cur.execute(f"SELECT book_quantity FROM stock WHERE book_ISBN ='{book_ISBN}' ;")
            quantity_data = cur.fetchone()

            if quantity_data is None:
                # for testing sql will replace data
                cur.execute(f"INSERT OR REPLACE INTO stock VALUES ('{book_name}','{book_author}','{book_date}','{book_ISBN}','{book_description}','{str(book_picture.filename)}',{book_trade_price},{book_retail_price},{book_quantity});")
                conn.commit()
                conn.close()

                if book_picture.filename != '':
                    book_picture.save(os.path.join(app.config['picture_path'], book_picture.filename))
                    print(book_picture)
                    flash("Book has been added to stock", "info")  # message about book has been saved
                    return add_book_form()

            else:
                # update book quantity if ISBN number is same
                new_quantity_data = quantity_data[0] + int(book_quantity)
                cur.execute(f"UPDATE stock SET book_quantity = {new_quantity_data} WHERE book_ISBN = '{book_ISBN}' ;")
                conn.commit()
                flash("Book has been added to stock", "info")  # message about book has been saved
                return add_book_form()


        # add message about book has been saved successfully
        except Exception as error:
            flash("Error", "info")
            print(error)
            return add_book_form()
    else:
        return add_book_form()

def add_book_form():
    return render_template('add_stock.html', add_book_form=url_for('add_stock'))




order_list = []

@app.route('/cart', methods=['GET', 'POST'])
def cart():
    cart_list = {}
    for item in order_list:
        quantity= 0
        for book in order_list:
            if book == item:
                quantity += 1
        cart_list[item] = quantity
    

    cart_book = []
    for books in cart_list.keys():
        cart_book.append(books)
   
    book_data = []
    for book in cart_book:
        conn = sqlite3.connect('book_shop.sqlite3')
        cur = conn.cursor()
        cur.execute(f"SELECT book_name, book_picture, book_retail_price FROM stock WHERE  book_ISBN = {book} ;")
        book_list = cur.fetchone()
        book_data.append(book_list)


    return render_template('cart.html', cart_=cart_list, cart_books = book_data)



@app.route('/empty_cart', methods=['GET', 'POST'])
def empty_cart():
    order_list.clear()
    session.pop('items', None)
    session.pop('price', None)
    flash("Your cart has been Cleared")
    return redirect(url_for('home'))




@app.route('/add_to_cart', methods=['GET', 'POST'])
def add_to_cart():
    #make data base for products
    if request.method == 'POST':
        conn = sqlite3.connect('book_shop.sqlite3')
        cur = conn.cursor()
        item = request.form['item']
        int_item = int(item)
        order_list.append(int_item)
        total_price = 0
        for list in order_list:
            cur.execute(f"SELECT book_retail_price FROM stock where book_ISBN = '{list}';")
            book_data = cur.fetchone()
            book_data = book_data[0]
            total_price = total_price + book_data

        conn.commit()
        conn.close()
        session['items'] = len(order_list)
        session['price'] = round(total_price, 2)
        return redirect(url_for('home'))



if __name__ == "__main__":
    app.run(debug=True)