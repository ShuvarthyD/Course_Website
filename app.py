from flask import (Flask, session, redirect,
				   url_for, escape, request,
				   render_template, flash)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text

app=Flask(__name__)
app.secret_key=b'debnath'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
db = SQLAlchemy(app)

# Home Page
@app.route('/',methods=['GET','POST'])
@app.route('/home',methods=['GET','POST'])
def home():
	return render_template('index.html')

# Login Page
@app.route('/login',methods=['GET','POST'])
def login():
	if request.method=='POST':
		# Get user type from form
		session['usertype'] = request.form.get('user-type')
		# If user not logged in
		if not session['usertype']:
			# Set session pop_up to error
			session['pop_up'] = 'error'
			flash('Please Select a User Type')
			return render_template('login.html')
		else:
			# Get table from the usertype database
			sql= """
				SELECT *
				FROM '{}'
				"""
			results = db.engine.execute(text(sql.format(session['usertype'])))
			# Loop through users and verify username and password
			for result in results:
				if result['username']==request.form['username']:
					if result['password']==request.form['password']:
						# Set session name and username
						session['name']=result['name']
						session['username']=request.form['username']
						# Different messages for Student and Instructor Login
						if session['usertype'] == 'Student':
							flash('Welcome ' + session['name'] +
								  '! Click My Account to see your Info and Grades')
						else:
							flash('Welcome ' + session['name'] +
								  '! Click My Account to see your Info and Student Grades')
						# Remove error pop_pop session 
						session.pop('pop_up', None)
						return redirect(url_for('index'))
			session['pop_up'] = 'error'
			flash('Incorrect UserName/Password! Please Try Again')
			return render_template('login.html')
	# If user is already logged in
	elif 'username' in session:
		session['pop_up'] = 'error'
		flash('You Are Already Logged In ' +
			  session['name'] +
			  '! Logout To Sign In As A Different User')
		return redirect(url_for('index'))
	else:
		return render_template('login.html')

# Register Page
@app.route("/register",methods=['GET','POST'])
def register():
	# If user not logged in
	if 'username' not in session:
		if request.method=='POST':
			usertype = request.form.get('user-type')
			name = request.form['name']
			username = request.form['username']
			password = request.form['password']

			# Error check input
			if not usertype:
				session['pop_up'] = 'error'
				flash('Please Select a User Type')
				return render_template('register.html')
			elif username == '' or password == '' or name == '':
				session['pop_up'] = 'error'
				flash('Please Enter a Name/Username/Password')
				return render_template('register.html')
			else:
				# Get table from the usertype database
				sql= """
					SELECT *
					FROM '{}'
					"""
				results = db.engine.execute(text(sql.format(usertype)))

				# Loop through table and see if user already exists
				for result in results:
					if result['username']==username:
						session['pop_up'] = 'error'
						flash('Username ' + username + ' already exists')
						return render_template('register.html')
				# If user doesnt exist add it
				insertSQL= """INSERT INTO '{}' (name, username, password)
							VALUES ('{}', '{}', '{}')""".format(usertype,
																name,
																username,
																password);	
				db.engine.execute(text(insertSQL))

				# If user is a student add user to mark table too
				if usertype == 'Student':
					insertSQL= """INSERT INTO Marks (username)
							VALUES ('{}')""".format(username);	
					db.engine.execute(text(insertSQL))

				session.pop('pop_up', None)
				flash('User ' + username + ' created!')
	else:
		session['pop_up'] = 'error'
		flash('Please Logout To Register For A New Account')
		return redirect(url_for('index'))
	return render_template('register.html')

# Account Page
@app.route("/account",methods=['GET','POST'])
def account():
	if 'username' in session:
		if session['usertype']=='Student':
			sql= """
				SELECT *
				FROM Marks
				"""
			results = db.engine.execute(text(sql))
			for result in results:
				if result['username']==session['username']:
					session['assignemnt1'] = result['assignemnt1']
					session['assignemnt2'] = result['assignemnt2']
					session['assignemnt3'] = result['assignemnt3']
					session['quiz1'] = result['quiz1']
					session['quiz2'] = result['quiz2']
					session['quiz3'] = result['quiz3']
					session['midterm'] = result['midterm']
					session['final'] = result['final']

			# If Student posts a remark
			if request.method=='POST':
				remark_desc = request.form['remark-desc']
				if request.form['remark-desc']:
					insertSQL= """INSERT INTO Remark (username,assessment,request)
								VALUES ('{}', '{}', '{}')""".format(session['username'],
																	request.form['remark-type'],
																	remark_desc)
					db.engine.execute(text(insertSQL))
					session.pop('pop_up', None)
					flash('Remark Request Sent!')
				else:
					session['pop_up'] = 'error'
					flash('Please Enter A Reason For Remark')
		# Instructor Login
		else:
			# Get Student and Marks Join Table so we can access the student names 
			sql= """
				SELECT *
				FROM Student
				LEFT JOIN Marks
				ON Student.username = Marks.username
				"""
			# Create a student info dict session
			session['student_info'] = {}
			results = db.engine.execute(text(sql))
			# Create var to check if its a odd row on table
			odd_row = True
			odd_row_num = 1
			for result in results:
				if odd_row_num % 2 == 0:
					odd_row = False
				else:
					odd_row = True
				# Add to dict student username as the key and every other info as values for key
				session['student_info'][result['username']] = [odd_row, result['name'],
															   {'assignemnt1': result['assignemnt1']},
															   {'assignemnt2': result['assignemnt2']},
															   {'assignemnt3': result['assignemnt3']},
															   {'quiz1': result['quiz1']},
															   {'quiz2': result['quiz2']},
															   {'quiz3': result['quiz3']},
															   {'midterm': result['midterm']},
															   {'final': result['final']}]
				odd_row_num += 1

			# Get Student Remark Info and store it in dict
			sql= """
				SELECT *
				FROM Remark
				LEFT JOIN Student
				ON Remark.username = Student.username
				"""
			session['student_remark'] = {}
			results = db.engine.execute(text(sql))
			odd_row = True
			odd_row_num = 1
			remark_num = 0
			for result in results:
				if odd_row_num % 2 == 0:
					odd_row = False
				else:
					odd_row = True
				session['student_remark'][remark_num] = [odd_row, result['username'],
														 result['name'],
														 result['assessment'],
														 result['request']]
				remark_num += 1
				odd_row_num += 1

			# Check if instructor wants to post a updated mark
			if request.method =='POST':
				# Check if its a valid input
				if request.form['instructor-mark-val'].replace('.','',1).isdigit() and float(request.form['instructor-mark-val']) <= 100:
					# Get what assessment its for and its value from post and update mark
					mark_type = request.form['instructor-mark-type'].split()[1]
					username = request.form['instructor-mark-type'].split()[0]
					updateSQL="""UPDATE Marks
										   SET '{}' = '{}'  
										   WHERE username = '{}'""".format(mark_type,
										   								   request.form['instructor-mark-val'],
										   								   username);
					db.engine.execute(text(updateSQL))
					session.pop('pop_up', None)
					flash('Mark Updated!')
					return redirect(url_for('account'))
				else:
					session['pop_up'] = 'error'
					flash('Please Enter A Valid Mark')

		return render_template('account.html')
	else:
		session['pop_up'] = 'error'
		flash('Please Login To View The Page')
		return  redirect(url_for('login'))

# Home Page
@app.route("/home")
@app.route("/index")
def index():
	if 'username' in session:
		return render_template('index.html')
	else:
		session['pop_up'] = 'error'
		flash('Please Login To View The Page')
		return redirect(url_for('login'))

# Send Feedback Page
@app.route("/send_feedback",methods=['GET','POST'])
def send_feedback():
	# Check if Student is accessing this page
	if 'username' in session:
		if session['usertype']=='Student':
			# Create Instructor table and get store name and username values in session 
			sql= """
				SELECT *
				FROM Instructor
				"""
			session['instructor_info'] = {}
			results = db.engine.execute(text(sql))
			for result in results:
				session['instructor_info'][result['name']] = result['username']

			# Check if student posted feedback and 
			if request.method=='POST':
				instructor = request.form.get('instructor')
				teaching_liking = request.form['teaching_liking']
				teaching_improve = request.form['teaching_improve']
				lab_liking = request.form['lab_liking']
				lab_improve = request.form['lab_improve']
				# If user selected a instructor
				if instructor:
					# Get instructor info and insert feedback into table
					name = instructor.split('|')[0]
					username = instructor.split('|')[1].strip()
					# Check if user entered every field
					if teaching_liking and teaching_improve and lab_liking and lab_improve:
						insertSQL= """INSERT INTO Feedback (username,name,teaching_liking,
															teaching_improve,lab_liking,
															lab_improve)
									VALUES ('{}', '{}','{}', '{}', '{}', '{}')""".format(username,
																						 name,
																						 teaching_liking,
																						 teaching_improve,
																						 lab_liking,
																						 lab_improve);
						db.engine.execute(text(insertSQL))
						session.pop('pop_up', None)
						flash('Feedback Sent!')
					else:
						session['pop_up'] = 'error'
						flash('Please Enter On All The Feilds')
				else:
					session['pop_up'] = 'error'
					flash('Please Select A Instructor')
			return render_template('send_feedback.html')
		else:
			session['pop_up'] = 'error'
			flash('Only Students Can View This Page')
			return redirect(url_for('index'))
	else:
		session['pop_up'] = 'error'
		flash('Please Login To View The Page')
		return redirect(url_for('login'))

# Instructor Feedback View Page
@app.route("/my_feedback")
def my_feedback():
	# Check if Instructor is on page
	if 'username' in session:
		if session['usertype']=='Instructor':
			# Get Feedback table data and store it in a session
			sql= """
			SELECT *
			FROM Feedback
			"""
			session['instructor_feedback'] = {}
			results = db.engine.execute(text(sql))
			feedback_num = 0
			for result in results:
				if result['username']== session['username']:
					session['instructor_feedback'][feedback_num] = [result['teaching_liking'],
																		  result['teaching_improve'],
																		  result['lab_liking'],
																		  result['lab_improve']]
				feedback_num += 1

			return render_template('my_feedback.html')
		else:
			session['pop_up'] = 'error'
			flash('Only Instructors Can View This Page')
			return redirect(url_for('index'))
	else:
		session['pop_up'] = 'error'
		flash('Please Login To View The Page')
		return redirect(url_for('login'))

# Credits Page
@app.route("/credits")
def credits():
	return render_template('credits.html')


# Logout Page
@app.route("/logout")
def logout():
	session.clear()
	flash('You have been logged out')
	return redirect(url_for('home'))

if __name__ == '__main__':
	app.run()
