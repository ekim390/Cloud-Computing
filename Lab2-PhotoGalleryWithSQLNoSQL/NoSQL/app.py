#!flask/bin/python
import sys, os
sys.path.append(os.path.abspath(os.path.join('..', 'utils')))
from env import AWS_ACCESS_KEY, AWS_SECRET_ACCESS_KEY, AWS_REGION, PHOTOGALLERY_S3_BUCKET_NAME, DYNAMODB_TABLE
from flask import Flask, jsonify, abort, request, make_response, url_for
from flask import render_template, redirect
import time
import exifread
import json
import uuid
import boto3  
from boto3.dynamodb.conditions import Key, Attr
import pymysql.cursors
from datetime import datetime
import pytz

"""
    INSERT NEW LIBRARIES HERE (IF NEEDED)
"""

from env import USER_TABLE
from itsdangerous import URLSafeTimedSerializer
import bcrypt
from flask import session
from botocore.exceptions import ClientError
from datetime import timedelta

"""
"""

app = Flask(__name__, static_url_path="")

dynamodb = boto3.resource('dynamodb', aws_access_key_id=AWS_ACCESS_KEY,
                            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                            region_name=AWS_REGION)

table = dynamodb.Table(DYNAMODB_TABLE)

UPLOAD_FOLDER = os.path.join(app.root_path,'static','media')
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def getExifData(path_name):
    f = open(path_name, 'rb')
    tags = exifread.process_file(f)
    ExifData={}
    for tag in tags.keys():
        if tag not in ('JPEGThumbnail', 'TIFFThumbnail', 'Filename', 'EXIF MakerNote'):
            key="%s"%(tag)
            val="%s"%(tags[tag])
            ExifData[key]=val
    return ExifData

def s3uploading(filename, filenameWithPath, uploadType="photos"):
    s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY,
                            aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
                       
    bucket = PHOTOGALLERY_S3_BUCKET_NAME
    path_filename = uploadType + "/" + filename

    s3.upload_file(filenameWithPath, bucket, path_filename)  
    s3.put_object_acl(ACL='public-read', Bucket=bucket, Key=path_filename)
    return f'''http://{PHOTOGALLERY_S3_BUCKET_NAME}.s3.amazonaws.com/{path_filename}'''


"""
    INSERT YOUR NEW FUNCTION HERE (IF NEEDED)
"""
app.secret_key = 'ekim390ece4150'

userTable = dynamodb.Table(USER_TABLE)

def sendConfirmationEmail(email, confirmationURL):
    ses = boto3.client('ses',
                    region_name=AWS_REGION,
                    aws_access_key_id=AWS_ACCESS_KEY,
                    aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
    SENDER = 'ekim390@gatech.edu'
    RECEIVER = email
    HTML = render_template('confirmemail.html', confirmationURL=confirmationURL)

    try:
        response = ses.send_email(
            Destination={
                'ToAddresses': [RECEIVER],
            },
            Message={
                'Subject': {
                    'Data': 'Photo Gallery Confirmation Email'
                },
                'Body': {
                    'Html': {
                        'Data': HTML,
                    },
                },
            },
            SourceArn='arn:aws:ses:us-east-1:741315320488:identity/ekim390@gatech.edu',
            Source=SENDER,
        )

    except ClientError as e:
        print(e.response['Error']['Message'])

    else:
        print("Email sent! Message ID:"),
        print(response['MessageId'])


def createToken(userID):
    serializer = URLSafeTimedSerializer('some_secret_key')
    token = serializer.dumps(userID, salt='some-secret-salt-for-confirmation')
    return token

def confirmToken(token, expiration):
    serializer = URLSafeTimedSerializer('some_secret_key')
    try:
        userID = serializer.loads(
            token,
            salt='some-secret-salt-for-confirmation',
            max_age=expiration
        )
    except Exception as e:
        print('expired token')
    return userID



"""
"""

"""
    INSERT YOUR NEW ROUTE HERE (IF NEEDED)
"""

@app.before_request
def before_request_function():
    if 'startTime' in session:
        now = datetime.now()
        delta = now - session['startTime']
        if (delta.seconds > timedelta(minutes=5).seconds):
            session.pop('name', None)
            session.pop('UserID', None)
            session.pop('email', None)
            session.pop('startTime', None)
            message = 'Session Expired. You have been logged out.'
            return render_template('login.html', message=message)

@app.route('/login', methods=['POST', 'GET'])
def login():
    """ Log into Account route.
    """
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        response = userTable.scan(FilterExpression=Attr('email').contains(email))
        results = response['Items']

        if len(results) == 0:
            message = 'Incorrect email. Account does not exist. Try Again.'
            return render_template('login.html', message=message)

        if (len(results) == 1 & bcrypt.checkpw(password.encode('utf-8'), results[0]['password'].value) == True & results[0]['confirmed'] == True):
            name = results[0]['name']
            userID = results[0]['UserID']
            email = results[0]['email']

            session['name'] = name
            session['UserID'] = userID
            session['email'] = email
            session['startTime'] = datetime.now()
            return redirect('/')
        elif results[0]['confirmed'] == False:
            message = 'Email not confirmed. Please confirm email.'
            return render_template('login.html', message=message)
        else:
            message = 'Incorrect password. Try Again.'
            return render_template('login.html', message=message)

    else:
        return render_template('login.html')


@app.route('/signup', methods=['POST', 'GET'])
def signup():
    """ Create new Account route.
    """
    if request.method == 'POST':
        email = request.form['email']
        name = request.form['name']
        password = request.form['password']
        password1 = request.form['password1']
        userID = uuid.uuid4()

        if password == password1:
            password = password.encode('utf-8')
            hashed = bcrypt.hashpw(password, bcrypt.gensalt())
        else:
            message = 'Passwords do not match.'
            return render_template('signup.html', message=message)

        response = userTable.scan(FilterExpression=Attr('email').contains(email))
        results = response['Items']

        if len(results) == 1:
            message = 'Email has already been used.'
            return render_template('signup.html', message=message)
        else:
            token = createToken(str(userID))
            userTable.put_item(
                Item={
                    "UserID": str(userID),
                    "email": email,
                    "name": name,
                    "password": hashed,
                    "confirmed": False,
                    "token": token
                }
            )
            confirmationURL = request.url_root + 'confirm/' + token
            sendConfirmationEmail(email, confirmationURL)
            message = 'Email Confirmation sent.'
            return render_template('signup.html', message=message)

    else:
        return render_template('signup.html')


@app.route('/confirm/<token>', methods=['GET', 'PUT'])
def confirm_email(token):
    """ Confirm Email route.
    """
    try:
        userID = confirmToken(token, 600)
    except:
        response = userTable.scan(FilterExpression=Attr('token').contains(token))
        results = response['Items']
        if results[0]['confirmed'] == True:
            message = 'Account has already been confirmed. Please login.'
            return render_template('login.html', message=message)
        elif len(results) == 1:
            UserID = results[0]['UserID']
            email = results[0]['email']
            userTable.delete_item(
                Key={
                    'UserID': UserID,
                    'email': email 
                }
            )
            message = 'The confirmation link is invalid or has expired. Try signing up again.'
            return render_template('login.html', message=message)
    else:
        response = userTable.scan(FilterExpression=Attr('UserID').contains(userID))
        results = response['Items']
        userTable.update_item(
            Key={
                'UserID': userID,
                'email': results[0]['email']
            },
            UpdateExpression='set confirmed = :confirmed',
            ExpressionAttributeValues={
                ':confirmed': True
            }
        )
        message = 'Account has been confirmed. Please login.'
        return render_template('login.html', message=message)

@app.route('/logout')
def logout():
    """ Logout route.
    """
    session.pop('name', None)
    session.pop('UserID', None)
    session.pop('email', None)
    session.pop('startTime', None)
    message = 'Successfully logged out.'
    return render_template('login.html', message=message)

@app.route('/cancelaccount', methods=['POST', 'GET'])
def cancel_account():
    """ Cancel/delete account route.
    """
    if request.method == 'POST':
        albumResponse = table.scan(FilterExpression=Attr('creator').contains(session['UserID']) & Attr('photoID').contains('thumbnail'))
        albumMeta = albumResponse['Items']

        i = 0
        while i < len(albumMeta):
            table.delete_item(
                Key={
                    'albumID': albumMeta[i]['albumID'],
                    'photoID': 'thumbnail'
                }
            )
            response = table.scan(FilterExpression=Attr('albumID').contains(albumMeta[i]['albumID']))
            results = response['Items']
            j = 0
            while j < len(results):
                table.delete_item(
                Key={
                    'albumID': results[j]['albumID'],
                    'photoID': results[j]['photoID']
                    }
                )
                j = j + 1
            i = i + 1

        userTable.delete_item(
            Key={
                'UserID': session['UserID'],
                'email': session['email']
            }
        )
        session.pop('name', None)
        session.pop('UserID', None)
        session.pop('email', None)
        session.pop('startTime', None)
        return redirect('/login')
    else:
        return render_template('cancelaccount.html', name=session['name'], email=session['email'])

@app.route('/album/<string:albumID>/deletealbum', methods=['GET', 'POST'])
def delete_album(albumID):
    """ Delete album and all pictures contained in album route.
    """
    if request.method == 'POST':
        table.delete_item(
            Key={
                'albumID': str(albumID),
                'photoID': 'thumbnail'
            }
        )
        response = table.scan(FilterExpression=Attr('albumID').contains(str(albumID)))
        results = response['Items']
        i = 0
        while i < len(results):
            table.delete_item(
            Key={
                'albumID': results[i]['albumID'],
                'photoID': results[i]['photoID']
                }
            )
            i = i + 1
        return redirect('/')
    else:
        albumResponse = table.query(KeyConditionExpression=Key('albumID').eq(albumID) & Key('photoID').eq('thumbnail'))
        albumMeta = albumResponse['Items']
        if len(albumMeta) > 0:
            album={}
            album['albumID'] = albumMeta[0]['albumID']
            album['name'] = albumMeta[0]['name']
            album['description'] = albumMeta[0]['description']
            album['thumbnailURL'] = albumMeta[0]['thumbnailURL']
            return render_template('deletealbum.html', album=album, name=session['name'], email=session['email'])
        else:
            return render_template('deletealbum.html', album=album, name=session['name'], email=session['email'])

@app.route('/album/<string:albumID>/<string:photoID>/deletephoto', methods=['GET','POST'])
def delete_photo(albumID, photoID):
    """ Delete photo route.
    """
    if request.method == 'POST':
        table.delete_item(
            Key={
                'albumID': str(albumID),
                'photoID': str(photoID)
            }
        )
        return redirect(f'''/album/{albumID}''')
    else:
        albumResponse = table.query(KeyConditionExpression=Key('albumID').eq(albumID) & Key('photoID').eq('thumbnail'))
        albumMeta = albumResponse['Items']

        response = table.query( KeyConditionExpression=Key('albumID').eq(albumID) & Key('photoID').eq(photoID))
        results = response['Items']

        if len(results) == 1:
            photo={}
            photo['photoID'] = results[0]['photoID']
            photo['title'] = results[0]['title']
            photo['description'] = results[0]['description']
            photo['tags'] = results[0]['tags']
            photo['photoURL'] = results[0]['photoURL']
            
            return render_template('deletephoto.html', photo=photo, albumID=albumID, albumName=albumMeta[0]['name'], photoID=photoID, name=session['name'], email=session['email'])
        else:
            return render_template('deletephoto.html', photo={}, albumID=albumID, albumName="", name=session['name'], email=session['email'])

@app.route('/album/<string:albumID>/<string:photoID>/updatephoto', methods=['GET', 'POST'])
def update_photo(albumID, photoID):
    """ Update photo route.
    """
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        tags = request.form['tags']

        updatedAtlocalTime = datetime.now().astimezone()
        updatedAtUTCTime = updatedAtlocalTime.astimezone(pytz.utc)

        table.update_item(
            Key={
                'albumID': str(albumID),
                'photoID': str(photoID)
            },
            UpdateExpression='set title = :title, description = :description, tags = :tags, updatedAt = :updatedAt',
            ExpressionAttributeValues={
                ':title': title,
                ':description': description,
                ':tags': tags,
                ':updatedAt': updatedAtUTCTime.strftime("%Y-%m-%d %H:%M:%S")
            }
        )

        return redirect(f'''/album/{albumID}''')

    else:
        albumResponse = table.query(KeyConditionExpression=Key('albumID').eq(albumID) & Key('photoID').eq('thumbnail'))
        albumMeta = albumResponse['Items']

        response = table.query( KeyConditionExpression=Key('albumID').eq(albumID) & Key('photoID').eq(photoID))
        results = response['Items']

        if len(results) == 1:
            photo={}
            photo['photoID'] = results[0]['photoID']
            photo['title'] = results[0]['title']
            photo['description'] = results[0]['description']
            photo['tags'] = results[0]['tags']
            photo['photoURL'] = results[0]['photoURL']
            
            return render_template('updatephoto.html', photo=photo, albumID=albumID, albumName=albumMeta[0]['name'], photoID=photoID, name=session['name'], email=session['email'])
        else:
            return render_template('updatephoto.html', photo={}, albumID=albumID, albumName="", name=session['name'], email=session['email'])


"""
"""

"""
    I have added an edit to home_page() and have added name=name and email=email for all routes
    to display the name and email of the current user.
"""

@app.errorhandler(400)
def bad_request(error):
    """ 400 page route.

    get:
        description: Endpoint to return a bad request 400 page.
        responses: Returns 400 object.
    """
    return make_response(jsonify({'error': 'Bad request'}), 400)



@app.errorhandler(404)
def not_found(error):
    """ 404 page route.

    get:
        description: Endpoint to return a not found 404 page.
        responses: Returns 404 object.
    """
    return make_response(jsonify({'error': 'Not found'}), 404)



@app.route('/', methods=['GET'])
def home_page():
    """ Home page route.

    get:
        description: Endpoint to return home page.
        responses: Returns all the albums.
    """
    if 'UserID' in session:
        """Made an edit here to make sure that someone is logged in before accessing the homepage."""
        name = session['name']
        email = session['email']
        response = table.scan(FilterExpression=Attr('photoID').eq("thumbnail"))
        results = response['Items']

        if len(results) > 0:
            for index, value in enumerate(results):
                createdAt = datetime.strptime(str(results[index]['createdAt']), "%Y-%m-%d %H:%M:%S")
                createdAt_UTC = pytz.timezone("UTC").localize(createdAt)
                results[index]['createdAt'] = createdAt_UTC.astimezone(pytz.timezone("US/Eastern")).strftime("%B %d, %Y")

        return render_template('index.html', albums=results, name=name, email=email)

    else:
        return redirect('/login')



@app.route('/createAlbum', methods=['GET', 'POST'])
def add_album():
    """ Create new album route.

    get:
        description: Endpoint to return form to create a new album.
        responses: Returns all the fields needed to store new album.

    post:
        description: Endpoint to send new album.
        responses: Returns user to home page.
    """
    if request.method == 'POST':
        uploadedFileURL=''
        file = request.files['imagefile']
        name = request.form['name']
        description = request.form['description']

        if file and allowed_file(file.filename):
            albumID = uuid.uuid4()
            
            filename = file.filename
            filenameWithPath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filenameWithPath)
            
            uploadedFileURL = s3uploading(str(albumID), filenameWithPath, "thumbnails");

            createdAtlocalTime = datetime.now().astimezone()
            createdAtUTCTime = createdAtlocalTime.astimezone(pytz.utc)

            table.put_item(
                Item={
                    "albumID": str(albumID),
                    "photoID": "thumbnail",
                    "name": name,
                    "description": description,
                    "thumbnailURL": uploadedFileURL,
                    "createdAt": createdAtUTCTime.strftime("%Y-%m-%d %H:%M:%S"),
                    "creator": session['UserID']
                }
            )
        return redirect('/')
    else:
        return render_template('albumForm.html', name=session['name'], email=session['email'])



@app.route('/album/<string:albumID>', methods=['GET'])
def view_photos(albumID):
    """ Album page route.

    get:
        description: Endpoint to return an album.
        responses: Returns all the photos of a particular album.
    """
    albumResponse = table.query(KeyConditionExpression=Key('albumID').eq(albumID) & Key('photoID').eq('thumbnail'))
    albumMeta = albumResponse['Items']

    response = table.scan(FilterExpression=Attr('albumID').eq(albumID) & Attr('photoID').ne('thumbnail'))
    items = response['Items']

    return render_template('viewphotos.html', photos=items, albumID=albumID, albumName=albumMeta[0]['name'], name=session['name'], email=session['email'])



@app.route('/album/<string:albumID>/addPhoto', methods=['GET', 'POST'])
def add_photo(albumID):
    """ Create new photo under album route.

    get:
        description: Endpoint to return form to create a new photo.
        responses: Returns all the fields needed to store a new photo.

    post:
        description: Endpoint to send new photo.
        responses: Returns user to album page.
    """
    if request.method == 'POST':    
        uploadedFileURL=''
        file = request.files['imagefile']
        title = request.form['title']
        description = request.form['description']
        tags = request.form['tags']

        if file and allowed_file(file.filename):
            photoID = uuid.uuid4()
            filename = file.filename
            filenameWithPath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filenameWithPath)            
            
            uploadedFileURL = s3uploading(filename, filenameWithPath);
            
            ExifData=getExifData(filenameWithPath)
            ExifDataStr = json.dumps(ExifData)

            createdAtlocalTime = datetime.now().astimezone()
            updatedAtlocalTime = datetime.now().astimezone()

            createdAtUTCTime = createdAtlocalTime.astimezone(pytz.utc)
            updatedAtUTCTime = updatedAtlocalTime.astimezone(pytz.utc)

            table.put_item(
                Item={
                    "albumID": str(albumID),
                    "photoID": str(photoID),
                    "title": title,
                    "description": description,
                    "tags": tags,
                    "photoURL": uploadedFileURL,
                    "EXIF": ExifDataStr,
                    "createdAt": createdAtUTCTime.strftime("%Y-%m-%d %H:%M:%S"),
                    "updatedAt": updatedAtUTCTime.strftime("%Y-%m-%d %H:%M:%S")
                }
            )

        return redirect(f'''/album/{albumID}''')

    else:

        albumResponse = table.query(KeyConditionExpression=Key('albumID').eq(albumID) & Key('photoID').eq('thumbnail'))
        albumMeta = albumResponse['Items']

        return render_template('photoForm.html', albumID=albumID, albumName=albumMeta[0]['name'], name=session['name'], email=session['email'])



@app.route('/album/<string:albumID>/photo/<string:photoID>', methods=['GET'])
def view_photo(albumID, photoID):
    """ photo page route.

    get:
        description: Endpoint to return a photo.
        responses: Returns a photo from a particular album.
    """ 
    albumResponse = table.query(KeyConditionExpression=Key('albumID').eq(albumID) & Key('photoID').eq('thumbnail'))
    albumMeta = albumResponse['Items']

    response = table.query( KeyConditionExpression=Key('albumID').eq(albumID) & Key('photoID').eq(photoID))
    results = response['Items']

    if len(results) > 0:
        photo={}
        photo['photoID'] = results[0]['photoID']
        photo['title'] = results[0]['title']
        photo['description'] = results[0]['description']
        photo['tags'] = results[0]['tags']
        photo['photoURL'] = results[0]['photoURL']
        photo['EXIF']=json.loads(results[0]['EXIF'])

        createdAt = datetime.strptime(str(results[0]['createdAt']), "%Y-%m-%d %H:%M:%S")
        updatedAt = datetime.strptime(str(results[0]['updatedAt']), "%Y-%m-%d %H:%M:%S")

        createdAt_UTC = pytz.timezone("UTC").localize(createdAt)
        updatedAt_UTC = pytz.timezone("UTC").localize(updatedAt)

        photo['createdAt']=createdAt_UTC.astimezone(pytz.timezone("US/Eastern")).strftime("%B %d, %Y at %-I:%M:%S %p")
        photo['updatedAt']=updatedAt_UTC.astimezone(pytz.timezone("US/Eastern")).strftime("%B %d, %Y at %-I:%M:%S %p")
        
        tags=photo['tags'].split(',')
        exifdata=photo['EXIF']
        
        return render_template('photodetail.html', photo=photo, tags=tags, exifdata=exifdata, albumID=albumID, albumName=albumMeta[0]['name'], photoID=photoID, name=session['name'], email=session['email'])
    else:
        return render_template('photodetail.html', photo={}, tags=[], exifdata={}, albumID=albumID, albumName="", name=session['name'], email=session['email'])



@app.route('/album/search', methods=['GET'])
def search_album_page():
    """ search album page route.

    get:
        description: Endpoint to return all the matching albums.
        responses: Returns all the albums based on a particular query.
    """ 
    query = request.args.get('query', None)    

    response = table.scan(FilterExpression=Attr('name').contains(query) | Attr('description').contains(query))
    results = response['Items']

    items=[]
    for item in results:
        if item['photoID'] == 'thumbnail':
            album={}
            album['albumID'] = item['albumID']
            album['name'] = item['name']
            album['description'] = item['description']
            album['thumbnailURL'] = item['thumbnailURL']
            items.append(album)

    return render_template('searchAlbum.html', albums=items, searchquery=query, name=session['name'], email=session['email'])



@app.route('/album/<string:albumID>/search', methods=['GET'])
def search_photo_page(albumID):
    """ search photo page route.

    get:
        description: Endpoint to return all the matching photos.
        responses: Returns all the photos from an album based on a particular query.
    """ 
    query = request.args.get('query', None)    

    response = table.scan(FilterExpression=Attr('title').contains(query) | Attr('description').contains(query) | Attr('tags').contains(query) | Attr('EXIF').contains(query))
    results = response['Items']

    items=[]
    for item in results:
        if item['photoID'] != 'thumbnail' and item['albumID'] == albumID:
            photo={}
            photo['photoID'] = item['photoID']
            photo['albumID'] = item['albumID']
            photo['title'] = item['title']
            photo['description'] = item['description']
            photo['photoURL'] = item['photoURL']
            items.append(photo)

    return render_template('searchPhoto.html', photos=items, searchquery=query, albumID=albumID, name=session['name'], email=session['email'])



if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)
