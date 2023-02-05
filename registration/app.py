from flask import Flask, request, redirect, render_template, url_for,send_file,Response
import boto3


app = Flask(__name__)

boto3.setup_default_session(region_name='us-east-2')

session = boto3.Session(
    aws_access_key_id='YOUR_ACCESS_ID',
    aws_secret_access_key='YOUR_SECRET_ID',
    region_name='us-east-2'

)

dynamodb = session.resource('dynamodb')

s3 = session.client('s3')

table = dynamodb.Table("registration")

@app.route("/")
def register():
    return render_template("register.html")

@app.route("/register", methods=["POST"])
def save_register():
    username = request.form["username"]
    password = request.form["password"]
    first_name = request.form["first_name"]
    last_name = request.form["last_name"]
    email = request.form["email"]

    table.put_item(
        Item={
            "username": username,
            "password": password,
            "first_name": first_name,
            "last_name": last_name,
            "email": email
        }
    )

    file = request.files["file"]
    s3.upload_fileobj(file, "registerfiles", username + "/" + file.filename)

    return redirect("/success")

@app.route("/success")
def success():
    return  render_template("success.html")

@app.route("/loginPage")
def login():
     return render_template("login.html")

@app.route('/login', methods=['POST'])
def checkLoginDetails():
    username = request.form['username']
    password = request.form['password']

    response = table.get_item(Key={'username': username})

    if 'Item' in response and response['Item']['password'] == password:
        return redirect(url_for('welcome', username=username))

    return redirect(url_for('index'))

@app.route('/welcome/<username>')
def welcome(username):
    response = table.get_item(Key={'username': username})
    item = response['Item']

    files = []

    objects = s3.list_objects(Bucket='registerfiles', Prefix=username + "/")

    file = objects["Contents"][0]["Key"]
    s3.download_file('registerfiles', file, "temp_file")
    with open("temp_file", "r", encoding = "UTF-8") as f:
    	content = f.read()
    	word_count = len(content.split())
    print("Word count of the file: ", word_count)


    result = s3.list_objects(Bucket="registerfiles", Prefix=username)
    if "Contents" in result and len(result["Contents"]) > 0:
       file_key = result["Contents"][0]["Key"]
    else:
       file_key = None
    
    prefix, file_name = file_key.rsplit("/", 1) 
    return render_template('welcome.html', username=item['username'], first_name=item['first_name'], 
                             last_name=item['last_name'], email=item['email'], word_count=word_count,
			     prefix=prefix, file_name=file_name)


@app.route("/download/<prefix>/<file_name>")
def download_file(prefix,file_name):
    bucket_name = "registerfiles"

    file_key = prefix+ "/" + file_name
    file = s3.get_object(Bucket="registerfiles", Key = file_key)
    file_content = file["Body"].read()
    response = Response(file_content)
    response.headers["Content-Disposition"] = f"attachment; filename={file_name}"

    return response

if __name__ == "__main__":
    app.run()



