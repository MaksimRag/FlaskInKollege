from flask import Flask, render_template, url_for, redirect, request
import psycopg2
import json


app = Flask(__name__, static_folder="", template_folder="html")


### РУТЫ НАВИГАЦИИ###

@app.route("/")
@app.route("/<int:value>")
def main(value = 0):
    query = """ SELECT * FROM "Products" """
    products = request_select(query=query)

    query = f""" SELECT * FROM "Users" 
                 WHERE user_id = {value} """
    user = request_select(query=query)

    role = 0
    if user:
        user = user[0]
        role = user["role_id"]

    if role == 1:
        return render_template("main_admin.html", products=products, user=user)
    elif role == 2:
        return render_template("main_user.html", products=products, user=user)
    elif role == 0:
        return render_template("main.html", products=products)

@app.route("/tape")
@app.route("/tape/<value>")
def tape(value = 0):
    return redirect(url_for("main", value=value))


@app.route("/basket")
@app.route("/basket/<user_id>")
def basket(user_id = 0):
    query = f""" SELECT
                     user_id,
                     product.name,
                     product.cost,
                     basket.quantity,
                     (product.cost * basket.quantity) AS total_price_item,
                     SUM((product.cost * basket.quantity)) OVER () AS all_price_item
                 FROM
                     "Baskets" basket
                     INNER JOIN "Products" product USING(product_id)
                 WHERE user_id = {user_id} """
    get_basket = request_select(query=query)

    query = f""" SELECT * FROM "Users" 
                 WHERE user_id = {user_id} """
    user = request_select(query=query)

    if user:
        if get_basket:
            return render_template("basket_user.html", user=user[0], get_basket=get_basket)
        else:
            return render_template("basket_none.html", user=user[0])

    return render_template("basket.html", user=user)

@app.route("/basket/clear/<user_id>", methods=["POST"])
def order_arrange(user_id):
    query = f""" DELETE FROM "Baskets"
                 WHERE user_id = {user_id} """
    request_update(query=query)

    return redirect(url_for("basket", user_id=user_id))



@app.route("/profile")
@app.route("/profile/<value>")
def profile(value = 0):
    query = f""" SELECT * FROM "Users"
                 WHERE user_id = {value}"""
    user = request_select(query=query)

    role = 0
    if user:
        user = user[0]
        role = user["role_id"]

    if role == 1:
        query = f""" SELECT * FROM "Orders" """
        orders = request_select(query=query)
        return render_template("profile_admin.html", user=user, orders=orders)

    elif role == 2:
        query = f""" SELECT * FROM "Orders"
                     WHERE user_id = {value}"""
        orders = request_select(query=query)
        return render_template("profile_user.html", user=user, orders=orders)

    elif role == 0:
        return redirect(url_for("main"))

@app.route("/exit")
@app.route("/exit/<value>")
def exit_user(value = 0):
    return redirect(url_for("main"))

@app.route("/enter")
def enter():
    return render_template("enter.html")


@app.route("/item/<product_id>/description/<user_id>", methods=["POST"])
def item(product_id, user_id = 0):
    query = f""" SELECT * FROM "Products"
                     WHERE product_id = {product_id} """
    product = request_select(query=query)[0]

    query = f""" SELECT * FROM "Users" 
                     WHERE user_id = {user_id} """
    user = request_select(query=query)

    print(user)
    print(product)

    role = 0
    if user:
        user = user[0]
        role = user["role_id"]

    print(role)
    if role == 1:
        return render_template("item_description_admin.html", user=user, product=product)
    elif role == 2:
        return render_template("item_description_user.html", user=user, product=product)
    elif role == 0:
        return render_template("item_description.html", product=product)

@app.route("/item/<product_id>/insert/<user_id>", methods=["POST"])
def item_insert(product_id, user_id):
    query = f""" SELECT * FROM "Baskets"
                 WHERE product_id = {product_id} and user_id = {user_id} """
    get_basket = request_select(query=query)

    if get_basket:
        query = f""" UPDATE "Baskets"
                     SET quantity = quantity + 1
                     WHERE product_id = {product_id} and user_id = {user_id} """
        request_update(query=query)

    else:
        query = f""" INSERT INTO "Baskets"(user_id, product_id, quantity)
                     VALUES ({user_id}, {product_id}, 1)"""
        request_insert(query=query)

    return redirect(url_for("main", value=user_id))


@app.route("/orders/<user_id>")
def get_orders(user_id = 0):
    query = f""" SELECT * FROM "Users"
                 WHERE user_id = {user_id}"""
    user = request_select(query=query)

    role = 0
    if user:
        user = user[0]
        role = user["role_id"]

    if role == 1:
        query = f""" SELECT * FROM "Orders" """
        orders = request_select(query=query)
        return render_template("orders_admin.html", user=user, orders=orders)

    elif role == 2:
        query = f""" SELECT * FROM "Orders"
                     WHERE user_id = {user_id}"""
        orders = request_select(query=query)
        return render_template("orders_user.html", user=user, orders=orders)

    elif role == 0:
        return redirect(url_for("main"))

@app.route("/order/edit/", methods=["POST"])
def order_edit():
    order_id = request.form["order_id"]

    query = f""" SELECT * FROM "Orders" 
                 WHERE order_id = {order_id} """
    order = request_select(query=query)

    return order

@app.route("/order/arrange/<user_id>", methods=["POST"])
def order_arr(user_id):
    query = f""" SELECT
                         user_id,
                         product.name,
                         product.cost,
                         basket.quantity,
                         (product.cost * basket.quantity) AS total_price_item,
                         SUM((product.cost * basket.quantity)) OVER () AS all_price_item
                     FROM
                         "Baskets" basket
                         INNER JOIN "Products" product USING(product_id)
                     WHERE user_id = {user_id} """
    get_basket = request_select(query=query)

    query = f""" SELECT * FROM "Users"
                     WHERE user_id = {user_id}"""
    user = request_select(query=query)[0]

    return render_template("order_create.html", user=user, get_basket=get_basket)

@app.route("/order/create/<user_id>", methods=["POST"])
def oreder_create(user_id):
    address = request.form["address"]
    status = "В обработке"

    query = f""" SELECT
                     SUM((product.cost * basket.quantity)) OVER () AS all_price_item
                 FROM
                     "Baskets" basket
                     INNER JOIN "Products" product USING(product_id)
                 WHERE user_id = {user_id} """
    total_price = request_select(query=query)[0]
    total_price = int(total_price["all_price_item"])

    query = f""" SELECT * FROM "Users"
                 WHERE user_id = {user_id} """
    user = request_select(query=query)[0]

    phone = user["user_id"]

    query = f""" INSERT INTO "Orders"(user_id, address, status, total_price, phone)
                 VALUES ({user_id}, '{address}', '{status}', {total_price}, '{phone}') """
    request_insert(query=query)

    print(1)
    return redirect(url_for("get_orders", user_id=user_id))

### РУТЫ ВХОДА И РЕГИСТРАЦИИ ПОЛЬЗОВАТЕЛЯ ###

@app.route("/user/authorization", methods=["POST"])
def user_authorization():
    login = request.form["login"]
    password = request.form["password"]

    query = """ SELECT * FROM "Users" """
    users = request_select(query=query)

    try:
        for user in users:
            if user["login"] == login:
                if user["password"] == password:
                    print(f"Вошёл пользователь: {user["login"]}")
                    return redirect(url_for("main", value=f"{user["user_id"]}"))
                else:
                    print(f"Логин: {user["login"]} - ошибка входа (пароль)")
                    return redirect(url_for("enter"))
        else:
            print("Ошибка входа, логин не зарегистрирован")
            return redirect(url_for("enter"))

    except Exception as error:
        print(f"Произошла ошибка: {error}")
        return redirect(url_for("enter"))

@app.route("/user/registration", methods=["POST"])
def user_registration():
    return render_template("registration.html")

@app.route("/user/registration/error")
def user_registration_error():
    return render_template("registration.html")

@app.route("/user/registration/create", methods=["POST"])
def user_registration_create():
    login = request.form["login"]
    password = request.form["password"]
    password_repid = request.form["password_repid"]
    phone = request.form["phone"]

    query = """ SELECT * FROM "Users" """
    users = request_select(query=query)

    try:
        for user in users:
            if login == user["login"]:
                print("Этот логин уже занят")
                return redirect(url_for("user_registration_error"))
        else:
            if password == password_repid:
                query = f""" INSERT INTO "Users"(role_id, login, password, phone)
                             VALUES (2, '{login}', '{password}', '{phone}'); """
                request_insert(query=query)
                print(f"Зарегистрирован пользователь: {login}")

                query = f""" SELECT user_id FROM "Users"
                             WHERE login = '{login}' """
                user_id = request_select(query=query)[0]
                return redirect(url_for("main", value=f"{user_id["user_id"]}"))
            else:
                print("Пароли не совпадают")
                return redirect(url_for("user_registration_error"))

    except Exception as error:
        print(f"Произошла ошибка: {error}")
        return redirect(url_for("user_registration_error"))


def request_select(query):
    global cursor, connection
    try:
        connection = psycopg2.connect(database="postgres", user="administrator", password="admin", host="localhost", port="5432")
        cursor = connection.cursor()
        cursor.execute(query=query)
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        result = []
        for row in rows:
            result.append(dict(zip(columns, row)))
        query_answer = json.dumps(result, ensure_ascii=False, indent=4)
        query_answer = json.loads(query_answer)
        return query_answer

    except Exception as error:
        print(f"Произошла ошибка: {error}")

    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()

def request_insert(query):
    global cursor, connection
    try:
        connection = psycopg2.connect(database="postgres", user="administrator", password="admin", host="localhost", port="5432")
        cursor = connection.cursor()
        cursor.execute(query=query)
        connection.commit()

    except Exception as error:
        print(f"Произошла ошибка: {error}")

    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()

def request_update(query):
    global cursor, connection
    try:
        connection = psycopg2.connect(database="postgres", user="administrator", password="admin", host="localhost", port="5432")
        cursor = connection.cursor()
        cursor.execute(query=query)
        connection.commit()

    except Exception as error:
        print(f"Произошла ошибка: {error}")

    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()

if __name__ == "__main__":
    app.run(debug=True)
