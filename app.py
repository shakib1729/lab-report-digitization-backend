from flask import Flask, jsonify, request, send_file
import os
from flask_cors import CORS
from werkzeug.utils import secure_filename
import pytesseract
from PIL import Image
import cv2
from flask_sqlalchemy import SQLAlchemy
import re
import base64

pytesseract.pytesseract.tesseract_cmd = '/app/.apt/usr/bin/tesseract'

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'

db = SQLAlchemy(app)


# from selenium import webdriver
# driver=webdriver.Chrome(executable_path='C:\Program Files (x86)\Google\Chrome\chromedriver')
# driver

# driver.get('https://www.meditec.com/resourcestools/medical-reference-links/normal-lab-values/')
# driver.maximize_window()

# def isfloat(value):
#   try:
#     float(value)
#     return True
#   except ValueError:
#     return False

# from bs4 import BeautifulSoup
# import re
# ans = []
# lis = driver.find_elements_by_xpath('//div[@id = "ValuesWrapper"]/ul')
# for i in lis:
#     data = i
#     data = BeautifulSoup(data.get_attribute('innerHTML'),'html.parser')
#     l = data.find_all('li')
#     for t in l:
#         temp = []
#         try:
#             j = t.string.split()
#             print(j)
#             if(isfloat(j[1])):
#                 temp.append(j[0].lower())
#                 temp.append(float(re.findall(r"[-+]?\d*\.\d+|\d+",j[1])[0]))
#                 temp.append(float(re.findall(r"[-+]?\d*\.\d+|\d+",j[3])[0]))
#             else:
#                 temp.append(j[0].lower()+" " + j[1].lower())
#                 temp.append(float(re.findall(r"[-+]?\d*\.\d+|\d+",j[2])[0]))
#                 temp.append(float(re.findall(r"[-+]?\d*\.\d+|\d+",j[4])[0]))
#             ans.append(temp)
#         except IndexError:
#             continue
# ans


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
	img=cv2.imread(file_path)
	text = pytesseract.image_to_string(img).lower()
	text = re.sub('[_?!@#$|]', '', text)
	textWords = text.split()
	# print(textWords)
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

	# if 'lymphocytes' and 'monocytes' in user_dict:
	# 	user = User(
	# 				rbc_count = float(user_dict['rbc count']),
	# 				lymphocytes = float(user_dict['lymphocytes']),
	# 				monocytes = float(user_dict['monocytes'])
	# 				)
	# elif 'monocytes' in user_dict:
	# 	user = User(
	# 				rbc_count = float(user_dict['rbc count']),
	# 				monocytes = float(user_dict['monocytes'])
	# 				)
	# elif 'lymphocytes' in user_dict:
	# 	user = User(
	# 				rbc_count = float(user_dict['rbc count']),
	# 				lymphocytes = float(user_dict['lymphocytes'])
	# 				)
	# else:
	# 	user = User(
	# 				rbc_count = float(user_dict['rbc count'])
	# 				)
	db.session.add(user)
	db.session.commit()

import matplotlib.pyplot as plt
import numpy as np
def save_graph(s2):
	x=np.arange(0,5*(len(s2)+2),5)
	y1=x-x+5.6
	y2=x-x+4.2
	s1=[ 5*(i+1) for i in range(len(s2))]
	plt.rcParams["figure.figsize"] = [15, 8]
	plt.plot(s1,s2,marker = 'o')
	plt.plot(x,y1,"b--",linewidth=2)
	plt.plot(x,y2,"b--",linewidth=2)
	# for i in range(len(s2)):
	#     if s2[i]<5.6 and s2[i]>4.2:
	#         plt.plot(s1[i],s2[i],marker='o', markersize=5,color="g")
	#     else:
	#         plt.plot(s1[i],s2[i],marker='o', markersize=5,color="r")
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
		currFile = request.files['file']
		file_name = secure_filename(currFile.filename)
		# file_path = os.path.join('./uploads', file_name)##
		# print(file_path)
		# currFile.save(file_path)###
		currFile.save(file_name)
		user_dict = get_digital(file_name)
		# user_dict = get_digital(file_path)##
		print(user_dict)
		# save to DB
		save_db(user_dict)###
		# print(rbc_counts)
		# user_dict['rbc_array'] = rbc_counts
		
		# user = [('user_data', user_dict), ('rbc_graph_url', rbc_graph_url)]
		# user[rbc_graph_url] = rbc_graph_url
		# print(user_dict)
		# return "doneeee"
		return jsonify(user_dict),200##

	return "Hello from /getdigital"


@app.route('/getrbc')
def getgraph():
	rbc_counts = [user.rbc_count for user in User.query.all()] # Create an array using the values in database
	print(rbc_counts)
	rbc_graph_url = save_graph(rbc_counts) # Save Graph using of the array created from the database
	with open(rbc_graph_url, "rb") as imageFile:
		strr = base64.b64encode(imageFile.read()) # Convert image to base64
		# print (type(strr))
		strr = strr.decode('utf-8') # Convert that base 64 from 'bytes' type to 'str'
		# print (type(strr))
		# print(strr)
		return jsonify({'image': strr}),200  # Send the string of base64 image representation as JSON

@app.route('/getlymphocytes')
def getlymphocytes():
	lymphocytes_counts = [user.lymphocytes for user in User.query.all()] # Create an array using the values in database
	res = [i for i in lymphocytes_counts if i] 
	print(res)
	lymphocytes_counts_url = save_graph(res) # Save Graph using of the array created from the database
	with open(lymphocytes_counts_url, "rb") as imageFile:
		strr = base64.b64encode(imageFile.read()) # Convert image to base64
		# print (type(strr))
		strr = strr.decode('utf-8') # Convert that base 64 from 'bytes' type to 'str'
		# print (type(strr))
		# print(strr)
		return jsonify({'image': strr}),200  # Send the string of base64 image representation as JSON

@app.route('/getmonocytes')
def getmonocytes():
	monocytes_counts = [user.monocytes for user in User.query.all()] # Create an array using the values in database
	res = [i for i in monocytes_counts if i]
	print(res)
	monocytes_counts_url = save_graph(res) # Save Graph using of the array created from the database
	with open(monocytes_counts_url, "rb") as imageFile:
		strr = base64.b64encode(imageFile.read()) # Convert image to base64
		# print (type(strr))
		strr = strr.decode('utf-8') # Convert that base 64 from 'bytes' type to 'str'
		# print (type(strr))
		# print(strr)
		return jsonify({'image': strr}),200  # Send the string of base64 image representation as JSON

@app.route('/clear')
def clear_all():
	db.session.query(User).delete()
	db.session.commit()
	return 'cleared'

if __name__ == "__main__":
	app.run(debug=False, threaded=False)