from flask import Flask,render_template,url_for,request,flash,redirect
import nltk
nltk.data.path.append('./nltk_data/')
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.stem import PorterStemmer
import math,os
from flask_login import LoginManager,current_user,login_user,logout_user,login_required
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email,  EqualTo, ValidationError

from flask_bcrypt import Bcrypt

from flask_login import UserMixin


app=Flask(__name__)
app.secret_key = 'asrtarstaursdlarsn'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join('site.db')
bcrypt=Bcrypt(app)
db=SQLAlchemy(app)

login_manager=LoginManager()
login_manager.init_app(app)

login_manager.login_view='login'

@login_manager.user_loader
def get_user(ident):
  return User.query.get(int(ident))


class User(db.Model,UserMixin):
	id=db.Column(db.Integer,primary_key=True)
	username=db.Column(db.String(20),unique=True,nullable=False)
	email=db.Column(db.String(120),unique=True,nullable=False)
	image_file=db.Column(db.String(20),nullable=False,default='default.jpg')
	password=db.Column(db.String(60),nullable=False)

	def __repr__(self):
		return f'User("{self.username}","{self.email}","{self.image_file}")'



class RegistrationForm(FlaskForm):
	username=StringField('Username',validators=[DataRequired(),Length(min=2,max=10)])
	email=StringField('Email',validators=[DataRequired(),Email()])
	password=PasswordField('Password',validators=[DataRequired()])
	confirm_password=PasswordField('Confirm Password',validators=[DataRequired(),EqualTo('password')])
	submit=SubmitField('Sign Up')

	#the following function is a fascility provided by flask
	# validate_field(self,field)


	def validate_username(self,username):
		user=User.query.filter_by(username=username.data).first()
		if user:
			raise ValidationError("This username is already taken!!")

	def validate_email(self,email):
		user=User.query.filter_by(email=email.data).first()
		if user:
			raise ValidationError("This email is already taken!!")


class LoginForm(FlaskForm):
	#username=StringFeild('Username',validators=[DataRequired(),Length(min=2,max=10)])
	email=StringField('Email',validators=[DataRequired(),Email()])
	password=PasswordField('Password',validators=[DataRequired()])
	#confirm_password=PasswordField('Confirm Password',validators=[DataRequired(),EqualTo('password')])
	remember=BooleanField('Remember Me')
	submit=SubmitField('Login')

class UpdateAccountForm(FlaskForm):
	username=StringField('Username',validators=[DataRequired(),Length(min=2,max=10)])
	email=StringField('Email',validators=[DataRequired(),Email()])
	picture=FileField('Update Profile Picture',validators=[FileAllowed(['jpg','png'],'Images only!')])
	submit=SubmitField('Update')

	#the following function is a fascility provided by flask
	# validate_field(self,field)


	def validate_username(self,username):
		if username.data!=current_user.username:
			user=User.query.filter_by(username=username.data).first()
			if user:
				raise ValidationError("This username is already taken!!")

	def validate_email(self,email):
		if email.data!=current_user.email:
			user=User.query.filter_by(email=email.data).first()
			if user:
				raise ValidationError("This email is already taken!!")



@app.route('/home',methods=['GET','POST'])
@app.route('/',methods=['GET','POST'])
def home():
	if request.method=='POST':
		paragraph=request.form.get('paragraph')
		if paragraph:
			if request.form['button']=='Generate Summary':
				word_frequency= {}
				ps=PorterStemmer()
				tokenizer=word_tokenize(paragraph)

				for word in tokenizer:
				    word=ps.stem(word)
				    if word not in stopwords.words('english'):
				        if word not in word_frequency:
				            word_frequency[word]=1
				        else:
				            word_frequency[word]+=1
				    else:
				        continue

				#lets break the paragraph into the sentences 

				sentence_list=sent_tokenize(paragraph)

				#print(sentence_list)
				sentence_strengths={}

				for sentence in sentence_list:
				    total_words=len(word_tokenize(sentence))
				    for word in word_frequency:
				        if word in sentence.lower():
				            if sentence[0:15] in sentence_strengths:
				                sentence_strengths[sentence[:15]]+=word_frequency[word]
				            else:
				                sentence_strengths[sentence[:15]]=word_frequency[word]
				    sentence_strengths[sentence[:15]]=sentence_strengths[sentence[:15]]//total_words
				                
				## finding the threshold value for summarization
				sum_of_values=0
				for sentence in sentence_strengths:
				    sum_of_values+=sentence_strengths[sentence]
				threshold=sum_of_values//len(sentence_strengths)
				#print(threshold)


				# generating the summary
				sentence_count=0
				summary=''

				for sentence in sentence_list:
				    if sentence[:15] in sentence_strengths and sentence_strengths[sentence[:15]]<threshold-0.5:
				        summary+=sentence
				        sentence_count+=1

				
				
				return render_template('summary.html',summary=summary)
			
			elif request.form['button']=='Generate Title':
				word_frequency= {}
				ps=PorterStemmer()
				tokenizer=word_tokenize(paragraph)

				for word in tokenizer:
				    word=ps.stem(word)
				    if word not in stopwords.words('english') and word not in [',','/','.','"',"'"]:
				        if word not in word_frequency:
				            word_frequency[word]=1
				        else:
				            word_frequency[word]+=1
				    else:
				        continue
				count=0
				title=[]
				for k,v in sorted(word_frequency.items(),key=lambda item:item[1]): 
					if count==10:
						break
					else:
						title.append(k)
					count+=1
				title=sorted(title)
				
				return render_template('summary.html',summary=title)
		else:
			flash('You forgot something!!')

	return render_template ('home.html')


@app.route('/About')
def about():
    return render_template('About.html')




@app.route('/register',methods=['GET','POST'])
def register():
	form=RegistrationForm()
	form.email.data=str(form.email.data).lower()
	if form.validate_on_submit():
		hashed_password=bcrypt.generate_password_hash(form.password.data).decode('utf-8')
		user=User(username=form.username.data,email=form.email.data,password=hashed_password)
		db.session.add(user)
		db.session.commit()
		flash(f'Account created for {form.username.data}!','success')
		return redirect(url_for('home'))
	return render_template('register.html',title='register',form=form)


@app.route('/login',methods=['GET','POST'])
def login():
	if current_user.is_authenticated:
		return redirect(url_for('main.home'))
	form=LoginForm()
	if form.validate_on_submit():
		user=User.query.filter_by(email=form.email.data).first()
		if user and bcrypt.check_password_hash(user.password,form.password.data):
			login_user(user, remember=form.remember.data)
			next_page=request.args.get('next')
			flash(f'welcome!','success')
			return redirect(next_page) if next_page else redirect (url_for('home'))
		else:
			flash('login unsuccessful. Please check email or password','danger')
	return render_template('login.html',title='Login',form=form)


@app.route('/logout')
def logout():
	logout_user()
	return redirect(url_for('home'))


@app.route('/account',methods=['GET','POST'])
@login_required
def account():
	form=UpdateAccountForm()
	
	if form.validate_on_submit():
		current_user.username=form.username.data
		current_user.email=form.email.data
		db.session.commit()
		flash('Account Updated','primary')
	if request.method=='GET':
		form.username.data=current_user.username
		form.email.data=current_user.email
	return render_template('account.html',form=form,title=current_user.username)


if __name__=="__main__":
	app.run(debug=True)
