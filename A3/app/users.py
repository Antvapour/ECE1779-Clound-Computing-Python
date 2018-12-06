from __future__ import print_function # Python 2/3 compatibility
from flask import render_template, session, redirect, url_for, request, g
from app import webapp
import hashlib
from hmac import compare_digest

import boto3
import json

from boto3.dynamodb.conditions import Key, Attr

from flask import render_template, url_for, redirect, request
from app import webapp


# connect to dynamodb

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
webapp.secret_key = '\x80\xa9s*\x12\xc7x\xa9d\x1f(\x03\xbeHJ:\x9f\xf0!\xb1a\xaa\x0f\xee'

SECRET_KEY = b'pseudo randomly generated secret key'
AUTH_SIZE = 16


def sign(cookie):  # sign(password1)
    h = hashlib.md5()
    h.update(bytes(cookie, 'utf-8'))
    return h.hexdigest().encode('utf-8')


def verify(cookie, sig):
    good_sig = sign(cookie)
    return compare_digest(good_sig, sig)


@webapp.route('/signup', methods=['GET'])
# Display an HTML form that allows users to sign up.
def signup():
    return render_template("users/signup.html", title="New User")


@webapp.route('/signup', methods=['POST'])
# Create a new account and save it in the database.
def signup_save():
    table = dynamodb.Table('a3_ece1779')

    username = request.form.get('username', "")
    email_address = request.form.get('email_address', "")
    password1 = request.form.get('password1', "")
    password2 = request.form.get('password2', "")
    question1 = request.form.get('question1', "")
    question2 = request.form.get('question2', "")

    error = False

    if username == "" or email_address == "" or password1 == "" or password2 == "" \
            or question1 == "" or question2 == "":

        error = True
        error_msg = "Error: All fields are required!"

    elif password1 != password2:
        error = True
        error_msg = "Error: The re-typed password does not match your first entry!"

    else:
        response = table.get_item(
            Key={
                'username': username
            },
            ProjectionExpression="#user",
            ExpressionAttributeNames={"#user": "username"}
        )

        data = {}

        if 'Item' in response:
            item = response['Item']
            data.update(item)

        if data:
            print(data)
            error = True
            error_msg = "Error: User name already exists!"

    if error:
        return render_template("users/signup.html", title="New User", error_msg=error_msg, username=username)

    else:
        response = table.put_item(
            Item={
                'username': username,
                'email_address': email_address,
                'password': sign(password1),
                'question1': question1,
                'question2': question2,
                }
        )

        return render_template("home.html")


@webapp.route('/login_submit', methods=['POST'])
def login_submit():
    username = request.form.get('username', "")
    password = request.form.get('password', "")

    error = False

    if username == "" or password == "":
        error = True
        error_msg = "Error: All fields are required!"

    else:
        table = dynamodb.Table('a3_ece1779')
        response = table.get_item(
            Key={
                'username': username
            }
        )

        data = {}

        if 'Item' in response:
            item = response['Item']
            data.update(item)

        if not data:
            error = True
            error_msg = "Error: User Does not exist!"

        elif not verify(password, (data['password']).value):
            error = True
            error_msg = "Error: password does not match!"

    if error:
        return render_template("home.html", title="Log in", error_msg=error_msg, username=username)

    session['authenticated'] = True
    session['username'] = data['username']

    return redirect(url_for('user_home'))


@webapp.route('/forgot_password', methods=['GET'])
# Display an HTML form that allows users to sign up.
def forgot_password():
    return render_template("users/forgot_password.html", title="New User")


@webapp.route('/forgot_password', methods=['POST'])
def forgot_password_save():
    username = request.form.get('username', "")
    email_address = request.form.get('email_address', "")
    question1 = request.form.get('question1', "")
    question2 = request.form.get('question2', "")
    password1 = request.form.get('password1', "")
    password2 = request.form.get('password2', "")

    error = False

    if username == "" or email_address == "" or question1 == "" or question2 == ""\
            or password1 == "" or password2 == "" or question1 == "" or question2 == "":

        error = True
        error_msg = "Error: All fields are required!"

    else:
        table = dynamodb.Table('a3_ece1779')

        response = table.get_item(
            Key={
                'username': username
            }
        )

        data = {}

        if 'Item' in response:
            item = response['Item']
            data.update(item)

        if not data:
            error = True
            error_msg = "Error: User Does not exist!"

        elif email_address != data['email_address'] or question1 != data['question1'] or question2 != data['question2']:
            error = True
            error_msg = "Error: Information is not correct!"

    if error:
        return render_template("users/forgot_password.html", title="Forgot Password",
                               error_msg=error_msg, username=username)

    table = dynamodb.Table('a3_ece1779')

    response = table.update_item(
        Key={
            'username': username
        },
        UpdateExpression="SET password = :p",
        ExpressionAttributeValues={
            ':p': sign(password1)
        }

    )

    return redirect(url_for('main'))


@webapp.route('/home', methods=['GET'])
def user_home():
    if 'authenticated' not in session:
        return redirect(url_for('login'))

    # get the account username
    account_user_name = session.get('username')

    table = dynamodb.Table('a3_ece1779')
    response = table.get_item(
        Key={
            'username': account_user_name
        }
    )

    data = {}

    if 'Item' in response:
        item = response['Item']
        data.update(item)

    file_key_name = str(account_user_name) + '/' + 'thumbnail'
    s3 = boto3.client('s3')

    url_thumbnail = s3.generate_presigned_url(
        'get_object',
        Params={'Bucket': 'imagesece1779', 'Key': file_key_name})

    url_total = []
    file_name = []
    file_type = []
    i = 0
    s3 = boto3.client('s3')

    if 'file_content' in data.keys():
        for file in data['file_content']:
            i = i+1
            index = file.rfind('.')

            file_1 = file[:index]
            file_2 = file[index+1:]

            file_type.append(file_2)
            file_name.append(file_1)

            url = s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': 'imagesece1779', 'Key': str(account_user_name) + '/' + file_1})
            url_total.append(url)

    zipped_data = zip(url_total, file_name, file_type)

    return render_template("users/userhome.html", title="User Home", zipped_data=zipped_data, data=data, i=i,
                           url_thumbnail=url_thumbnail)


@webapp.route('/logout', methods=['POST'])
# Clear the session when users want to log out.
def logout():
    session.clear()
    return redirect(url_for('main'))
