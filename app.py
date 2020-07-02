from flask import Flask, jsonify, request, send_file
import os
from flask_cors import CORS
from werkzeug.utils import secure_filename
import pytesseract
import cv2
import matplotlib.pyplot as plt
import numpy as np
from flask_sqlalchemy import SQLAlchemy
import re
import base64

pytesseract.pytesseract.tesseract_cmd = '/app/.apt/usr/bin/tesseract'
app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'

db = SQLAlchemy(app)

# Class that reprsents a Table
class User(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	lymphocytes = db.Column(db.Float)
	monocytes = db.Column(db.Float)
	rbc_count = db.Column(db.Float)

medical_terms = ["hemoglobin", "rbc count", "mcv", "mch", "mchc", 
                 "red cell distribution width (row)", "total leukocyte count (tlc)",
                 "differential leucocyte count (dlc)","packed cell volume (pcv)",
                 "segmented neutrophils","lymphocytes","monocytes","eosinophils","basophils"
                 ,"neutrophils","lymphocytes","monocytes","platelet","cholesterol total","triglycerides"
                 ,"hdl cholesterol","ldl cholesterol","vldl cholesterol","non-hdl cholesterol",
                 "glucose fasting","glucose (pp)","platelet","ast-:alt ratio","ggtp","alkaline phosphatase (alp)"]
                 

def checkNumber(s):
    return s.replace('.','',1).isdigit()

def get_digital(file_path):
	img=cv2.imread(file_path, cv2.IMREAD_GRAYSCALE) # Open the image in Grayscale mode
	text = pytesseract.image_to_string(img).lower()
	text = re.sub('[_?!@#$|]', '', text)
	textWords = text.split()
	user_dict = {}
	for i in range(len(textWords)):
	    curr_term = ''
	    for j in range(5):  # Check by also combining next 5 elements
	        if i+j+1 >= len(textWords):
	            break
	        curr_term += textWords[i+j]
	        if curr_term in medical_terms:
	        	if checkNumber(textWords[i+j+1]):
		            user_dict[curr_term] = textWords[i+j+1]
	        curr_term += ' '
	return user_dict

def save_db(user_dict):
	user = User()
	if 'lymphocytes' in user_dict:
		user.lymphocytes = float(user_dict['lymphocytes'])

	if 'monocytes' in user_dict:
		user.monocytes = float(user_dict['monocytes'])

	if 'rbc count' in user_dict:
		user.rbc_count = float(user_dict['rbc count'])

	db.session.add(user)
	db.session.commit()

def save_graph(arr):
	x=np.arange(0,5*(len(arr)+2),5)
	y1=x-x+5.6
	y2=x-x+4.2
	arr2=[ 5*(i+1) for i in range(len(arr))]
	plt.rcParams["figure.figsize"] = [15, 8]
	plt.plot(arr2,arr,marker = 'o')
	plt.plot(x,y1,"b--",linewidth=2)
	plt.plot(x,y2,"b--",linewidth=2)
	plt.grid()
	saved_file_path = 'testplot.png'
	plt.savefig(saved_file_path)  # Save the graph
	plt.close()
	return saved_file_path

@app.route('/')
def index():
    return "Hello From app.py"

@app.route('/getdigital', methods=['GET', 'POST'])
def getdigital():
	if request.method == 'POST':
		# Get the file from the POST request
		currFile = request.files['file']
		# Save the file to the specified path
		file_name = secure_filename(currFile.filename)
		file_path = os.path.join('./uploads', file_name)
		currFile.save(file_path)	

		user_dict = get_digital(file_path)
		# save to DB
		save_db(user_dict)
		return jsonify(user_dict),200

	return "Hello from /getdigital"


@app.route('/getrbc')
def getgraph():
	rbc_counts = [user.rbc_count for user in User.query.all()] # Create an array using the values in database
	res = [i for i in rbc_counts if i] 
	rbc_graph_url = save_graph(res) # Save Graph using the array created from the database
	with open(rbc_graph_url, "rb") as imageFile:
		strr = base64.b64encode(imageFile.read()) # Convert image to base64
		strr = strr.decode('utf-8') # Convert that base 64 from 'bytes' type to 'str'
		return jsonify({'image': strr}),200  # Send the string of base64 image representation as JSON

@app.route('/getlymphocytes')
def getlymphocytes():
	lymphocytes_counts = [user.lymphocytes for user in User.query.all()] # Create an array using the values in database
	res = [i for i in lymphocytes_counts if i] 
	lymphocytes_counts_url = save_graph(res) # Save Graph using the array created from the database
	with open(lymphocytes_counts_url, "rb") as imageFile:
		strr = base64.b64encode(imageFile.read()) # Convert image to base64
		strr = strr.decode('utf-8') # Convert that base 64 from 'bytes' type to 'str'
		return jsonify({'image': strr}),200  # Send the string of base64 image representation as JSON

@app.route('/getmonocytes')
def getmonocytes():
	monocytes_counts = [user.monocytes for user in User.query.all()] # Create an array using the values in database
	res = [i for i in monocytes_counts if i]
	monocytes_counts_url = save_graph(res) # Save Graph using the array created from the database
	with open(monocytes_counts_url, "rb") as imageFile:
		strr = base64.b64encode(imageFile.read()) # Convert image to base64
		strr = strr.decode('utf-8') # Convert that base 64 from 'bytes' type to 'str'
		return jsonify({'image': strr}),200  # Send the string of base64 image representation as JSON

@app.route('/clear')
def clear_all():
	db.session.query(User).delete()
	db.session.commit()
	return 'cleared'

if __name__ == "__main__":
	app.run(debug=False, threaded=False)