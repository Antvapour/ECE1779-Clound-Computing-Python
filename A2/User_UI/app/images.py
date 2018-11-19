from flask import render_template, session, redirect, url_for, request, g, send_from_directory
from app import webapp

from app.users import sign, verify

import mysql.connector

from app.config import db_config

import os
from io import BytesIO


import urllib.request

from wand.image import Image

from flask import render_template, redirect, url_for, request
from app import webapp

import boto3


def connect_to_database():
    return mysql.connector.connect(user=db_config['user'],
                                   password=db_config['password'],
                                   host=db_config['host'],
                                   database=db_config['database'])


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = connect_to_database()
    return db


@webapp.teardown_appcontext
def teardown_db(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


@webapp.route('/images/upload', methods=['POST'])
# Upload new images and their transformations to an existing bucket and save their filenames in the databases
def s3_upload():
    users_id = session.get('username')

    cnx = get_db()
    cursor = cnx.cursor()

    # check if the post request has the file part
    if 'file' not in request.files:
        return redirect(url_for('user_home'))

    # upload files to the s3 bucket and store information in the database
    for upload in request.files.getlist("file"):

        # delete back syntax
        filename_full = upload.filename
        index = filename_full.rfind('.')
        filename = filename_full[:index]

        if upload.filename == '':
            return redirect(url_for('user_home'))

        # Get the service client and upload to the s3 bucket
        s3 = boto3.client('s3')
        file_key_name = str(users_id) + '/' + filename
        print(file_key_name)
        s3.upload_fileobj(upload, 'imagesece1779', file_key_name, ExtraArgs={"ContentType": "image/jpeg"})

        # store information into the database
        query = ''' INSERT INTO images (users_id,filename)
                                       VALUES (%s,%s)'''
        cursor.execute(query, (users_id, filename))

        # get the url of the upload image
        url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': 'imagesece1779', 'Key': file_key_name})

        # create transformations of images and save them in the s3 bucket
        with Image(file=urllib.request.urlopen(url)) as img:

            # create thumbnails
            with img.clone() as thumb:
                size = thumb.width if thumb.width < thumb.height else thumb.height
                thumb.crop(width=size, height=size, gravity='center')
                thumb.resize(128, 128)
                bytes_io_file = BytesIO(thumb.make_blob('JPEG'))
                s3 = boto3.client('s3')
                file_key_name_thumb = str(users_id) + '/' + (filename + '_thumbnail')
                s3.upload_fileobj(bytes_io_file, 'imagesece1779', file_key_name_thumb,
                                  ExtraArgs={"ContentType": "image/jpeg"})

            # create rotated transformation
            with img.clone() as rotated:
                rotated.rotate(135)
                bytes_io_file = BytesIO(rotated.make_blob('JPEG'))
                s3 = boto3.client('s3')
                file_key_name_rotated = str(users_id) + '/' + (filename + '_rotated')
                s3.upload_fileobj(bytes_io_file, 'imagesece1779', file_key_name_rotated,
                                  ExtraArgs={"ContentType": "image/jpeg"})

            # create flopped transformations
            with img.clone() as flopped:
                flopped.flop()
                bytes_io_file = BytesIO(flopped.make_blob('JPEG'))
                s3 = boto3.client('s3')
                file_key_name_flopped = str(users_id) + '/' + (filename + '_flopped')
                s3.upload_fileobj(bytes_io_file, 'imagesece1779', file_key_name_flopped,
                                  ExtraArgs={"ContentType": "image/jpeg"})

            # created gray-scale transformations path
            with img.clone() as gray:
                gray.type = 'grayscale'
                bytes_io_file = BytesIO(gray.make_blob('JPEG'))
                s3 = boto3.client('s3')
                file_key_name_gray = str(users_id) + '/' + (filename + '_gray')
                s3.upload_fileobj(bytes_io_file, 'imagesece1779', file_key_name_gray,
                                  ExtraArgs={"ContentType": "image/jpeg"})

        cnx.commit()

    return redirect(url_for('user_home'))


@webapp.route('/images/trans/<filename>', methods=['GET'])
# show the transformations of a specific image.
def images_trans(filename):
    if 'authenticated' not in session:
        return redirect(url_for('login'))

    users_id = session.get('username')
    filename_folder = str(users_id) + '/'
    print(filename_folder)

    url_trans_list = []
    filename_trans_list = []
    s3 = boto3.client('s3')

    for i in ['', '_flopped', '_rotated', '_gray']:
        filename_trans = filename_folder + (filename + i)
        print(filename_trans)

        url = s3.generate_presigned_url('get_object', Params={'Bucket': 'imagesece1779', 'Key': filename_trans})

        print(url)

        url_trans_list.append(url)

        filename_trans_list.append(filename_trans)

        zipped_trans_data = zip(url_trans_list, filename_trans_list )

    return render_template("images/trans.html", title="Transformations", zipped_trans_data=zipped_trans_data)


@webapp.route('/test/FileUpload', methods=['GET'])
# display an HTML form that allows TAs to upload pictures using script
def script():
    return render_template("script_new.html", title="uploadForm")


@webapp.route('/test/FileUpload', methods=['POST'])
# let TAs to automatically upload photos to populate their account
def script_upload():
    username = request.form.get('userID', "")
    password = request.form.get('password', "")

    error = False
    error_msg = ""

    if username == "" or password == "":
        error = True
        error_msg = "Error: All fields are required!"

    else :
        cnx = get_db()
        cursor = cnx.cursor()

        query = '''SELECT id, password FROM users
                          WHERE username = %s'''
        cursor.execute(query, (username,))
        row = cursor.fetchone()

        if row is None:
            error = True
            error_msg = "Error: User Does not exist!"

        elif not verify(password, bytes(row[1], 'utf-8')) :
            error = True
            error_msg = "Error: password does not match!"

    if error:
        return render_template("script_new.html", title="uploadForm", error_msg=error_msg, username=username)

    users_id = row[0]
    print(users_id)

    cnx = get_db()
    cursor = cnx.cursor()

    # upload files to the s3 bucket and store information in the database
    for upload in request.files.getlist("uploadedfile"):

        # delete back syntax
        filename_full = upload.filename
        index = filename_full.rfind('.')
        filename = filename_full[:index]
        print(filename)

        if upload.filename == '':
            return redirect(url_for('user_home'))

        # Get the service client and upload to the s3 bucket
        s3 = boto3.client('s3')
        file_key_name = str(users_id) + '/' + filename
        print(file_key_name)
        s3.upload_fileobj(upload, 'imagesece1779', file_key_name, ExtraArgs={"ContentType": "image/jpeg"})

        # store information into the database
        query = ''' INSERT INTO images (users_id,filename)
                                           VALUES (%s,%s)'''
        cursor.execute(query, (users_id, filename))

        # get the url of the upload image
        url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': 'imagesece1779', 'Key': file_key_name})

        # create transformations of images and save them in the s3 bucket
        with Image(file=urllib.request.urlopen(url)) as img:

            # create thumbnails
            with img.clone() as thumb:
                size = thumb.width if thumb.width < thumb.height else thumb.height
                thumb.crop(width=size, height=size, gravity='center')
                thumb.resize(128, 128)
                bytes_io_file = BytesIO(thumb.make_blob('JPEG'))
                s3 = boto3.client('s3')
                file_key_name_thumb = str(users_id) + '/' + (filename + '_thumbnail')
                s3.upload_fileobj(bytes_io_file, 'imagesece1779', file_key_name_thumb,
                                  ExtraArgs={"ContentType": "image/jpeg"})

            # create rotated transformation
            with img.clone() as rotated:
                rotated.rotate(135)
                bytes_io_file = BytesIO(rotated.make_blob('JPEG'))
                s3 = boto3.client('s3')
                file_key_name_rotated = str(users_id) + '/' + (filename + '_rotated')
                s3.upload_fileobj(bytes_io_file, 'imagesece1779', file_key_name_rotated,
                                  ExtraArgs={"ContentType": "image/jpeg"})

            # create flopped transformations
            with img.clone() as flopped:
                flopped.flop()
                bytes_io_file = BytesIO(flopped.make_blob('JPEG'))
                s3 = boto3.client('s3')
                file_key_name_flopped = str(users_id) + '/' + (filename + '_flopped')
                s3.upload_fileobj(bytes_io_file, 'imagesece1779', file_key_name_flopped,
                                  ExtraArgs={"ContentType": "image/jpeg"})

            # created gray-scale transformations path
            with img.clone() as gray:
                gray.type = 'grayscale'
                bytes_io_file = BytesIO(gray.make_blob('JPEG'))
                s3 = boto3.client('s3')
                file_key_name_gray = str(users_id) + '/' + (filename + '_gray')
                s3.upload_fileobj(bytes_io_file, 'imagesece1779', file_key_name_gray,
                                  ExtraArgs={"ContentType": "image/jpeg"})

        cnx.commit()

    msg = 'Upload completed!'

    return render_template("script_new.html", title="uploadForm", msg=msg, username=username, password=password)

