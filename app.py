from flask import (Flask, session, redirect,
				   url_for, escape, request,
				   render_template, flash)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text
from matplotlib.ticker import MaxNLocator
import os
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
plt.switch_backend('agg')

app=Flask(__name__)
app.secret_key= os.urandom(12).hex()
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
db = SQLAlchemy(app)

# Home Page
@app.route('/',methods=['GET','POST'])
@app.route('/index',methods=['GET','POST'])
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
						return redirect(url_for('home'))
			session['pop_up'] = 'error'
			flash('Incorrect UserName/Password! Please Try Again')
			return render_template('login.html')
	# If user is already logged in
	elif 'username' in session:
		session['pop_up'] = 'error'
		flash('You Are Already Logged In ' +
			  session['name'] +
			  '! Logout To Sign In As A Different User')
		return redirect(url_for('home'))
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
				return redirect(url_for('login'))
	else:
		session['pop_up'] = 'error'
		flash('Please Logout To Register For A New Account')
		return redirect(url_for('home'))
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
			# Store the assassment name and mark in a dict
			session['marks'] = {}
			for result in results:
				if result['username']==session['username']:
					session['marks']["Assignment 1"] = [result['assignemnt1'],"A1"]
					session['marks']["Assignment 2"] = [result['assignemnt2'],"A2"]
					session['marks']["Assignment 3"] = [result['assignemnt3'],"A3"]
					session['marks']["Quiz 1"] = [result['quiz1'],'Q1']
					session['marks']["Quiz 2"] = [result['quiz2'],'Q1']
					session['marks']["Quiz 3"] = [result['quiz3'],'Q3']
					session['marks']["Midterm"] = [result['midterm'],'Midterm']
					session['marks']["Final"] = [result['final'],'Final']

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
			return redirect(url_for('home'))
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
			return redirect(url_for('home'))
	else:
		session['pop_up'] = 'error'
		flash('Please Login To View The Page')
		return redirect(url_for('login'))

# Instructor Grade Summary Page
@app.route("/summary")
def summary():
	# Check if Instructor is on page
	if 'username' in session:
		# Join Student and Marks table and store info into dict.
		sql= """
			SELECT *
			FROM Student
			LEFT JOIN Marks
			ON Student.username = Marks.username
			"""
		# Create dict for the grades and store all grades and student info in it
		session['grades'] = {'A1': [], 'A2': [], 'A3': [], 'Q1': [], 'Q2': [], 'Q3': [], 'Midterm': [], 'Final': [], 'Name': [], 'User': []}
		results = db.engine.execute(text(sql))
		for result in results:
			session['grades']['A1'].append(result['assignemnt1'])
			session['grades']['A2'].append(result['assignemnt2'])
			session['grades']['A3'].append(result['assignemnt3'])
			session['grades']['Q1'].append(result['quiz1'])
			session['grades']['Q2'].append(result['quiz2'])
			session['grades']['Q3'].append(result['quiz3'])
			session['grades']['Midterm'].append(result['midterm'])
			session['grades']['Final'].append(result['final'])
			session['grades']['Name'].append(result['name'])
			session['grades']['User'].append(result['username'])
		# Check usertype
		if session['usertype']=='Instructor':
			df = pd.DataFrame(session['grades'])
			df['A_avg'] = df[['A1','A2','A3']].mean(axis=1)
			df['Q_avg'] = df[['Q1','Q2','Q3']].mean(axis=1)
			df['Name_Id'] = df["Name"] + "\n(" + df["User"] + ")"
			bin_labels_pct = ['0-10', '11-20', '21-30', '31-40', '41-50', '51-60', '61-70', '71-80', '81-90', '91-100']
			bin_labels_letr = ['F\n(0-49)', 'D\n(50-59)', 'C\n(60-69)', 'B\n(70-79)', 'A\n(80-100)']
			bin_labels_letr2 = ['F', 'D-','D','D+', 'C-','C','C+', 'B-','B','B+', 'A-','A','A+']
			sns.set_color_codes("pastel")
			pass_col = sns.color_palette("Blues_d",n_colors=3)
			fail_col = sns.color_palette("Reds_d",n_colors=1)
			l_palette = fail_col + pass_col*4
	
			for key, grades in df.items():
				if key not in ['A_avg', 'Q_avg', 'Name', 'User', "Name_Id"]:
					# Grade distribution plot (%)
					df[key + '_range'] = pd.cut(df[key], [0, 11, 21, 31, 41, 51, 61, 71, 81, 91, 101], labels=bin_labels_pct, right=False)
					grade_counts = df[key + '_range'].value_counts().sort_index()
					sns.barplot(x=grade_counts.index, y=grade_counts.values,zorder = 3)
					plt.title(f"Grade Distribution of {key}")
					plt.suptitle(f"Students: {df.shape[0] - df[key].isna().sum()} Mean: {df[key].mean()} Median: {df[key].median()} Std. Dev: {round(df[key].std(),1)}")
					plt.xticks(rotation=45)
					plt.gca().get_yaxis().set_major_locator(plt.MaxNLocator(integer=True))
					plt.grid(axis = 'y', linestyle = '--', linewidth = 0.5,zorder = 0)
					plt.xlabel("Grade (%)")
					plt.ylabel("Number of Students")
					plt.tight_layout()
					plt.savefig(f"static\img\graphs\{key}.png",transparent=True)
					plt.clf()
					# Grade distribution plot (letter)
					df['A1_range'] = pd.cut(df[key], bins=[0, 50, 60, 70, 80, 101], labels=bin_labels_letr, right=False)
					df['bins_2'] = pd.cut(df[key], bins=[0, 50,53,57,60,63,67,70,73,77,80,85,90,101],labels=bin_labels_letr2,right=False)
					grade_counts = df.groupby(['A1_range', 'bins_2']).size().unstack(fill_value=0)
					grade_counts.plot(kind='bar', stacked=True, zorder=3, color = l_palette)
					plt.title(f"Grade Distribution of {key}")
					plt.suptitle(f"Students: {df.shape[0] - df[key].isna().sum()} Mean: {df[key].mean()} Median: {df[key].median()} Std. Dev: {round(df[key].std(),1)}")
					plt.gca().get_yaxis().set_major_locator(plt.MaxNLocator(integer=True))
					plt.grid(axis = 'y', linestyle = '--', linewidth = 0.5,zorder = 0)
					plt.xticks(rotation=0)
					plt.legend(['Fail','Letter -','Letter','Letter +'])
					plt.xlabel("Grade (Letter)")
					plt.ylabel("Number of Students")
					plt.tight_layout()
					plt.savefig(f"static\img\graphs\{key}_letter.png",transparent=True)
					plt.clf()
					# Top Students for each assessment
					top = df[[key,'Name_Id']].sort_values(by=key, ascending=False).head(5)
					palette=sns.color_palette("Greens_d",n_colors=5)
					palette.reverse()
					ax = sns.barplot(x=key, y='Name_Id', data=top, orient='h',palette=palette)
					ax.bar_label(ax.containers[0])
					plt.title(f"Top 5 Students for {key}")
					plt.gca().get_yaxis().set_major_locator(plt.MaxNLocator(integer=True))
					plt.xlabel("Grade (%)")
					plt.ylabel("Student Name + UserID")
					for container in ax.containers:
						ax.bar_label(container)
					plt.tight_layout()
					plt.savefig(f"static\img\graphs\{key}_Top.png",transparent=True)
					plt.clf()

			# Assessment grade throughout course
			val = df[['Q1','A1','Q2','A2','Midterm','Q3','A3','Final']].mean()
			assessment_df = pd.DataFrame({'Assessment': val.index, 'Average': val.values})
			plt.axhline(y=assessment_df['Average'].mean(), color='gray', linestyle='--', label=f"Course Average : {round(assessment_df['Average'].mean(),2)}")
			plt.plot(assessment_df['Assessment'], assessment_df['Average'], marker='o', linestyle='-')
			plt.title("Average Assessment Grades Throughout Course")
			for x, y in zip(assessment_df['Assessment'], assessment_df['Average']):
				plt.annotate(str(y), xy=(x,y), xytext=(5,6), textcoords='offset points')
			plt.xlabel("Assessment")
			plt.ylabel("Grade Avg. (%)")
			plt.legend()
			plt.tight_layout()
			plt.savefig(f"static\img\graphs\Course_avg.png",transparent=True)
			plt.clf()			
			# Corellation heatmap between avg quiz and asignment grades and the mifterm and final grades
			corr = df[["Midterm", "Final", "A_avg", "Q_avg"]].corr()
			sns.heatmap(corr,annot=True,fmt=".2f", linewidth=.5)
			plt.title("Correlation Between Assessment Grades")
			plt.tight_layout()
			plt.savefig("static\img\graphs\corr.png",transparent=True)
			plt.clf()
		elif session['usertype']=='Student':
			sql= """
				SELECT *
				FROM Marks
				"""
			results = db.engine.execute(text(sql))
			# Store the assassment name and mark in a dict
			session['my_grades'] = {}
			for result in results:
				if result['username']==session['username']:
					session['my_grades']["A1"] = result['assignemnt1']
					session['my_grades']["A2"] = result['assignemnt2']
					session['my_grades']["A3"] = result['assignemnt3']
					session['my_grades']["Q1"] = result['quiz1']
					session['my_grades']["Q2"] = result['quiz2']
					session['my_grades']["Q3"] = result['quiz3']
					session['my_grades']["Midterm"] = result['midterm']
					session['my_grades']["Final"] = result['final']
			# Course Assessment Info
			df_course = pd.DataFrame(session['grades'])
			val = df_course[['Q1','A1','Q2','A2','Midterm','Q3','A3','Final']].mean()
			assessment_df = pd.DataFrame({'Assessment': val.index, 'Average': val.values})
			plt.plot(assessment_df['Assessment'], assessment_df['Average'], marker='o', color = 'orange', linestyle='-', label = 'Course Avg. Grades')
			plt.axhline(y=assessment_df['Average'].mean(), color='orange', linestyle='--', label=f"Course Avg. : {round(assessment_df['Average'].mean(),2)}")
			# Student Assessment Info
			df_stud = pd.DataFrame(session['my_grades'],index=[0])
			df_stud = df_stud[['Q1','A1','Q2','A2','Midterm','Q3','A3','Final']].mean()
			df_stud = pd.DataFrame({'Assessment': df_stud.index, 'Grade': df_stud.values})
			plt.plot(df_stud['Assessment'], df_stud['Grade'], marker='o', linestyle='-',color = 'blue', label = 'My Avg. Grades')
			plt.axhline(y=df_stud['Grade'].mean(), color='blue', linestyle='--', label=f"My Avg. : {round(df_stud['Grade'].mean(),2)}")
			plt.title("Assessment Avg. Compared with Class")
			for x, y in zip(assessment_df['Assessment'], assessment_df['Average']):
				plt.annotate(str(y), xy=(x,y), xytext=(5,6), textcoords='offset points', color = 'orange')
			for x, y in zip(df_stud['Assessment'], df_stud['Grade']):
				plt.annotate(str(y), xy=(x,y), xytext=(5,6), textcoords='offset points', color = 'blue')
			plt.xlabel("Assessment")
			plt.ylabel("Grade Avg. (%)")
			plt.legend()
			plt.tight_layout()
			plt.savefig("static\img\graphs\Stud_Avg.png",transparent=True)
			plt.clf()
		return render_template('summary.html')
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
	app.run(debug=True)
