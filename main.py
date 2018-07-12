#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import os
import webapp2
import gaesessions
import hashlib
import base64
import random
import urllib
import logging
import json
import re
from datetime import datetime
from datetime import timedelta
from urllib import unquote
import xml.etree.ElementTree as et
import hmac, hashlib

from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.api import taskqueue
from google.appengine.api import images
from google.appengine.ext import blobstore
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import mail
from google.appengine.api import memcache
from google.appengine.api import search

template.register_template_library('custom_tags.my_tags') 

class Recording(db.Model):
	rec_id = db.StringProperty()
	rec_blob = blobstore.BlobReferenceProperty()
	rec_user_id = db.StringProperty()
	rec_user_name = db.StringProperty()
	rec_comment = db.TextProperty()
	rec_creation_date = db.DateTimeProperty()
	rec_word_id = db.StringProperty()
	rec_type = db.StringProperty()
	rec_language = db.StringProperty()
	rec_mash_id = db.StringProperty()
	rec_mp3_blob = blobstore.BlobReferenceProperty()
	
	
class Language(db.Model):
	LanguageID = db.StringProperty()
	LanguageISOCode = db.StringProperty()
	LanguageNameEnglish = db.StringProperty()
	LanguageNameNative = db.StringProperty()
	LanguageSupported = db.BooleanProperty()
	PartsOrdering = db.StringProperty()
	LanguageFlagURL = db.StringProperty()
	
	
class Glyph(db.Model):
	glyph_id = db.StringProperty()
	glyph_blob = blobstore.BlobReferenceProperty()
	glyph_comment = db.TextProperty()
	glyph_user_id = db.StringProperty()
	glyph_rights_protected = db.BooleanProperty()
	
	
class Word(db.Model):
	word_id = db.StringProperty()
	word_language = db.StringProperty()
	word_creator_id = db.StringProperty()
	word_type = db.StringProperty()
	word_glyph_id = db.StringProperty()
	word_syllables = db.StringProperty()
	word_text_root = db.StringProperty()
	word_text_root_normalized = db.StringProperty()
	word_text_mod_plural = db.StringListProperty()
	word_text_mod_synonym = db.StringProperty()
	#word_search_variations = db.StringProperty()
	word_text_mod_opposite = db.StringProperty()
	word_text_mod_comp_super = db.StringListProperty()
	word_text_mod_time_tense = db.StringListProperty()
	word_programmable_text_root = db.TextProperty()
	word_programmable_glyph_list = db.StringListProperty()
	word_programmable_state_count = db.StringProperty()
	word_programmable_valid_part = db.StringListProperty()
	word_gender = db.StringProperty()
	word_sub_type = db.StringProperty()
	
	
class Variables(db.Model):
	word_id_count = db.IntegerProperty()
	user_id_count = db.IntegerProperty()
	lesson_id_count = db.IntegerProperty()
	mod_id_count = db.IntegerProperty()
	masher_rule_count = db.IntegerProperty()
	glyph_id_count = db.IntegerProperty()
	mash_id_count = db.IntegerProperty()
	comment_id_count = db.IntegerProperty()
	recording_id_count = db.IntegerProperty()
	language_id_count = db.IntegerProperty()
	class_id_count = db.IntegerProperty()
	submission_id_count = db.IntegerProperty()
	ModuleIDCount = db.IntegerProperty()
	StepIDCount = db.IntegerProperty()
	

class User(db.Model):
	UserID = db.StringProperty()
	UserUsername = db.StringProperty()
	UserEmail = db.StringProperty()
	UserVerified = db.BooleanProperty()
	UserVerificationString = db.StringProperty()
	UserPassword = db.StringProperty()
	UserPasswordSalt = db.StringProperty()
	UserJoinedDate = db.DateTimeProperty()
	UserType = db.StringProperty()
	UserNativeLanguageID = db.StringProperty()
	UserLearningLanguageID = db.StringProperty()
	UserAdminLanguageID = db.StringProperty()
	
	
class Lesson(db.Model):
	lesson_id = db.StringProperty()
	lesson_name = db.StringProperty()
	lesson_description = db.TextProperty()
	lesson_word_list = db.StringListProperty()
	lesson_modifier_list = db.StringListProperty()
	lesson_part_list = db.StringListProperty()
	lesson_teacher_id = db.StringProperty()
	lesson_creation_date = db.DateTimeProperty()
	lesson_mash_list = db.StringListProperty()
	lesson_mod_list = db.StringListProperty()
	lesson_class_id = db.StringProperty()
	lesson_video_url = db.StringProperty()
	lesson_minimum_submission_count = db.StringProperty()
	
	
class Modifier_Rule(db.Model):
	ModType = db.StringProperty()
	ModKey = db.StringProperty()
	ModText = db.StringProperty()
	
	
class Masher_Rule(db.Model):
	masher_id = db.StringProperty()
	masher_word_type = db.StringProperty()
	masher_part_subject = db.BooleanProperty()
	masher_part_verb = db.BooleanProperty()
	masher_part_object = db.BooleanProperty()
	masher_part_literal = db.BooleanProperty()
	masher_word_compatibility = db.StringListProperty()
	
	
class Class(db.Model):
	class_id = db.StringProperty()
	class_teacher_id = db.StringProperty()
	class_lesson_list = db.StringListProperty()
	class_student_list = db.StringListProperty()
	class_student_mail_list = db.StringListProperty()
	class_language = db.StringProperty()
	class_name = db.StringProperty()
	class_description = db.StringProperty()
	class_teacher_name = db.StringProperty()
	class_level = db.StringProperty()
	class_requested_student_list = db.StringListProperty()
	
	
class Submission(db.Model):
	sub_id = db.StringProperty()
	sub_mash_id = db.StringProperty()
	sub_lesson_id = db.StringProperty()
	sub_student_id = db.StringProperty()
	sub_student_name = db.StringProperty()
	sub_class_id = db.StringProperty()
	sub_submission_date = db.DateTimeProperty()
	sub_status = db.StringProperty()
	sub_mark = db.StringProperty()
	sub_comment = db.TextProperty()
	sub_audio = blobstore.BlobReferenceProperty()

	
class LocalisationAsset(db.Model):
	LAID = db.StringProperty()
	LAType = db.StringProperty()
	LAValue = db.TextProperty()
	LALanguage = db.StringProperty()
	
	
class Module(db.Model):
	ModuleID = db.StringProperty()
	ModuleCreatorID = db.StringProperty()
	ModuleCreationDateTime = db.DateTimeProperty()
	ModuleCreationLanguage = db.StringProperty()
	ModuleTitle = db.StringProperty()
	ModuleSubtitle = db.StringProperty()		
	ModuleStepCount = db.StringProperty()
	ModuleArtworkURL = db.StringProperty()
	ModuleStatus = db.StringProperty()
	
	
class Step(db.Model):
	StepID = db.StringProperty()
	StepTitle = db.StringProperty()
	StepSubtitle = db.StringProperty()
	StepRecordingConfig = db.StringProperty()
	StepRatingConfig = db.StringProperty()
	StepReferenceConfig = db.StringProperty()
	StepRefAutoConfig = db.StringProperty()
	StepRefVoiceURL = db.StringProperty()
	StepMashID = db.StringProperty()
	StepModuleID = db.StringProperty()
	StepOrder = db.IntegerProperty()
	StepStatus = db.StringProperty()
	
	
class Mash(db.Model):
	MashID = db.StringProperty()
	MashMeaningText = db.StringProperty()
	MashReferenceVoiceURL = db.StringProperty()
	MashValue = db.TextProperty()
	
	
class MainHandler(webapp2.RequestHandler):
    def get(self):
		words_out = []
		
		v=Variables.all()
		var = v.get()
		
		while len(words_out) < 10:
			w=Word.all()
			w.filter('word_id =', str(random.randint(0, var.word_id_count)))
			
			word = w.get()
			if word != None:
				if word.word_language == 'eng':
					words_out.append(word)
	
		url = self.request.url
		secure = False
		if 'https' in url:
			secure = True
			
		la=LocalisationAsset.all()
		
		lang=Language.all()
		lang.filter('LanguageSupported =', True)
	
		template_values = {	'words' : words_out,
							'secure' : secure,
							'localisation' : la,
							'languages' : lang}
		
		path = os.path.join(os.path.dirname(__file__), 'index.html')
		self.response.out.write(template.render(path, template_values))
	
	
class contact(webapp2.RequestHandler):
	def post(self):
		name = self.request.get('contactname')
		email = self.request.get('contactemail')
		message = self.request.get('contactmessage')
	
		mail_body = """
Name: """+name+"""
Email: """+email+"""
Message: """+message+"""
"""
		
		mail_html = """
<html><head>
</head>
<body>
Name: """+name+"""<br>
Email: """+email+"""<br>
Message: """+message+"""<br>

</body>
</html>
"""
		mail.send_mail(sender="<info@teanga.me>",to="<info@teanga.me>",subject="Teanga Contact Message",body=mail_body, html=mail_html)
		
		self.redirect('/')
	
	
class glyph_serve(blobstore_handlers.BlobstoreDownloadHandler):
	def get(self):
		g=Glyph.all()
		g.filter('glyph_id =', self.request.get('id'))
		gy=g.get()
		
		self.response.headers['Cache-Control'] = "public, max-age=31556926"
		self.send_blob(blobstore.BlobInfo.get(gy.glyph_blob.key()))
	
	
class serve_recording(blobstore_handlers.BlobstoreDownloadHandler):
	def get(self):
		t=Recording.all()
		t.filter('rec_word_id = ', self.request.get('id'))
		t.filter('rec_type =', 'standard_word_recording')
		temp=t.get()
		
		self.response.headers['Content-Type'] = 'audio/mpeg'
		self.send_blob(blobstore.BlobInfo.get(temp.rec_mp3_blob.key()))
	
	
class serve_mash_recording(blobstore_handlers.BlobstoreDownloadHandler):
	def get(self):
		t=Recording.all()
		t.filter('rec_id = ', self.request.get('id'))
		temp=t.get()
		
		self.response.headers['Content-Type'] = 'audio/mpeg'
		self.send_blob(blobstore.BlobInfo.get(temp.rec_blob.key()))
	
	
class wordids(webapp2.RequestHandler):
	def get(self):
		w=Word.all()
		term = self.request.get('word')
		type = self.request.get('type')
		lang = self.request.get('lang')
	
		logging.info('lang ' + lang)
		
		#if lang == 'gle':
		#	lang = 'Irish'
		##if lang == 'eng':
		#	lang = 'English'
		#if lang == 'ger':
		#	lang = 'German'
		#if lang == 'spa':
		#	lang = 'Spanish'
		##if lang == 'fre':
		#	lang = 'French'	
			
		l = Language.all()
		l.filter('LanguageISOCode =', lang)
		v = l.get()	
		lang = v.LanguageNameEnglish
	
		logging.info(lang)	
		answer = None
		
		for instance in w:	
			logging.info(instance.word_language)
			logging.info(lang)
			if instance.word_language == lang:	
				if instance.word_type == type:
				
					foundword = instance.word_text_root 
					term = self.request.get('word')
					
					if foundword == term:
					
						json_out = []
				
						json_out.append(instance.word_glyph_id)
						json_out.append(instance.word_type)
						json_out.append(instance.word_text_root)
						json_out.append(instance.word_id)
						json_out.append(instance.word_gender)
						logging.info(json_out)
							
						logging.info(instance.word_gender)
						self.response.headers['Content-Type'] = 'application/json'
						self.response.out.write(json.dumps(json_out))
	
	
class get_upload_url(webapp2.RequestHandler):
	def get(self):
		url = blobstore.create_upload_url('/upload_mp3')
		
		json_out = {'url':url}
		
		self.response.headers['Content-Type'] = 'application/json'
		self.response.out.write(json.dumps(json_out))

		
class updateEntities(webapp2.RequestHandler):
	def get(self):
		r=Step.all()
		
		for item in r:
			item.StepRefAutoConfig = 'NO'
			item.put()
				
class upload_mp3(blobstore_handlers.BlobstoreUploadHandler):
	def post(self):
		logging.info(self.request.get('id'))
	
		r=Recording.all()
		r.filter('rec_word_id =', self.request.get('id'))
		r.filter('rec_type =', 'standard_word_recording')
		rec = r.get()
		
		upload_files = self.get_uploads('audio_blob')
		
		rec.rec_mp3_blob = upload_files[0].key()
		
		rec.put()
		
class db_edit(webapp2.RequestHandler):
	def get(self):
		m
		
	
class masher(webapp2.RequestHandler):
	def get(self):
		session = gaesessions.get_current_session()

		if session.is_active():
			
			u=User.all()
			u.filter('UserID =', session['me'].UserID)
			t = u.get()
			
			l = Language.all()
			l.filter('LanguageID =', t.UserLearningLanguageID)
			v = l.get()
			
			logging.info('id')
			logging.info(session['me'].UserID)
			
			logging.info(t)
			
			userISO = v.LanguageISOCode
			
			f = Language.all()
			
			template_values = { 'languages' : f , 'user' : t, 'langISO' : userISO}
			
			path = os.path.join(os.path.dirname(__file__), 'masher.html')
			self.response.out.write(template.render(path, template_values))
					
		else:
			self.redirect('/signin')
			
	
	
class signup(webapp2.RequestHandler):
	def post(self):
		v=Variables.all()
		var=v.get()
		
		defaultLang = self.request.get('nativeLanguage')			
		logging.info('sign up')
		logging.info(defaultLang)
		
		ISO = 'Not Defined'
			
		l = Language.all()
		l.filter('LanguageISOCode =', defaultLang)
		v = l.get()	
		ISO = v.LanguageID	
				
		logging.info(ISO)	
				
		newpassword = self.request.get('pass')
		
		if (newpassword == ''):
			logging.info('creating new Language Curator account')
			salt = getRandString(64)
			randomPassword = getRandString(8)
			password_hash = hashlib.sha512(randomPassword+salt)
			assignedPassword = password_hash.hexdigest()
			
			email = self.request.get('newUserEmail')
			email = email.strip()
			defaultUserName = email.split("@")[0]
			logging.info(email)
			logging.info('lang numbers - ')
			logging.info(self.request.get('adminLanguageNo'))
			logging.info(self.request.get('nativeLanguageNo'))
			
			adminLanguageNo = self.request.get('adminLanguageNo')
			nativeLanguageNo = self.request.get('nativeLanguageNo')
			email = self.request.get('newUserEmail')
						
			logging.info(assignedPassword)
			logging.info(defaultUserName)
		
			user=User(	UserID = str(var.user_id_count),
						UserUsername = defaultUserName,
						UserEmail = email,
						UserVerified = False,
						UserVerificationString = getRandString(25),
						UserPassword = password_hash.hexdigest(),
						UserPasswordSalt = base64.urlsafe_b64encode(salt),
						UserJoinedDate = datetime.utcnow(),
						UserType = 'USER_CURATOR',
						UserNativeLanguageID = nativeLanguageNo,
						UserLearningLanguageID = nativeLanguageNo,
						UserAdminLanguageID = nativeLanguageNo
					)
			user.put()
			var.user_id_count+=1
			var.put()
			
			mail_body = """
	Welcome to Teanga.
	
	Email: """+email+"""
	Password: """+randomPassword+"""

	Click the link below to get started.

	http://www.teanga.me/verify_user?str="""+user.UserVerificationString+"""&id="""+user.UserID+"""&l="""+self.request.get('nativeLanguage')
			
			mail.send_mail(sender="<info@teanga.me>",to=self.request.get('newUserEmail'),subject="Verification Email",body=mail_body)

			self.redirect('/signin')		
		
		elif (newpassword):
			logging.info('creating new Student account')
			salt = getRandString(64)
			password = self.request.get('pass')
			password_hash = hashlib.sha512(password+salt)
		
			learningLang = self.request.get('learningLanguage')
			learningLangISO = 'Not Defined'
			
			logging.info('learningLang')
			logging.info(learningLang)
				
			a = Language.all()
			a.filter('LanguageISOCode =', learningLang)
			y = a.get()	

			logging.info(y)
			logging.info(y.LanguageID)

			learningLangISO = y.LanguageID	
			#learningLangISO = 'eng'
				
			user=User(	UserID = str(var.user_id_count),
						UserUsername = self.request.get('name'),
						UserEmail = self.request.get('email'),
						UserVerified = False,
						UserVerificationString = getRandString(25),
						UserPassword = password_hash.hexdigest(),
						UserPasswordSalt = base64.urlsafe_b64encode(salt),
						UserJoinedDate = datetime.utcnow(),
						UserType = 'USER_STUDENT',
						UserNativeLanguageID = ISO,
						UserLearningLanguageID = learningLangISO,
						UserAdminLanguageID = "0")
				
			user.put()
			var.user_id_count+=1
			var.put()
			
			mail_body = """
	Welcome to Teanga.

	Click the link below to get started.

	http://www.teanga.me/verify_user?str="""+user.UserVerificationString+"""&id="""+user.UserID+"""&l="""+self.request.get('nativeLanguage')
			
			mail.send_mail(sender="<info@teanga.me>",to=self.request.get('email'),subject="Verification Email",body=mail_body)

			self.redirect('/signin')
	
	
class signin(webapp2.RequestHandler):
	def get(self):
		logging.info(self.request.get('l'))
	
		template_values = { }
		
		path = os.path.join(os.path.dirname(__file__), 'signin.html')
		self.response.out.write(template.render(path, template_values))
		
		logging.info('verifying sign in')
		logging.info(self.request.get('l'))

		logging.info('redirecting to sign in page')
		#self.redirect('/signin')
		
	def post(self):
		emailString = str(self.request.get('email'))
	
		u=User.all()
		u.filter('UserEmail =', emailString)
		user=u.get()
		
		logging.info(user)
		
		logging.info(emailString)
		
		if user == None:
			self.redirect('/signin')
		else:
		
			logging.info(user.UserEmail)
			salt = base64.urlsafe_b64decode(str(user.UserPasswordSalt))
			
			logging.info('verifying password')
			logging.info('password ' + self.request.get('password'))
			logging.info('salted password ' + salt)
			
			
			d = str(self.request.get('password'))+str(salt)
			
			logging.info('together? ' + d)
			
			password_hash = hashlib.sha512(d)
			
			logging.info('user.UserPassword')
			logging.info(user.UserPassword)
			logging.info('password_hash.hexdigest()')
			logging.info(password_hash.hexdigest())
			
			if user.UserPassword == password_hash.hexdigest() and user.UserVerified == True:
				session = gaesessions.get_current_session()
				logging.info('PASSED')
				if session.is_active():
					session.terminate()
				session['me'] = user
				session.regenerate_id()
							
				logging.info('user.UserType')
				logging.info(user.UserType)
								
				if user.UserType == 'USER_ADMIN':
					self.redirect('/modules')
				if user.UserType == 'USER_CURATOR':
					self.redirect('/modules')
				if user.UserType == 'USER_STUDENT':
					self.redirect('/masher')
			else:
				self.redirect('/signin')
	
	
class signout(webapp2.RequestHandler):
	def get(self):
		session = gaesessions.get_current_session()
		if session.has_key('me'):
			session.terminate()
			self.redirect('/')
		else:
			self.redirect('/')
	
	
class verify_user(webapp2.RequestHandler):
	def get(self):
		u=User.all()
		u.filter('UserID =', self.request.get('id'))
		user=u.get()
		
		logging.info('verifying user')
		
		if user.UserVerificationString == self.request.get('str'):
			user.UserVerified = True
			user.put()
		
		logging.info(self.request.get('l'))

		self.redirect('/signin?l='+self.request.get('l'))
	
	
class mailCheck(webapp2.RequestHandler):
	def get(self):
		u=User.all()
		u.filter('UserEmail =', self.request.get('email'))
		user=u.get()
		
		data={}
		data['exists'] = False
		if user != None:
			data['exists'] = True
			
		self.response.headers['Content-Type'] = 'application/json'
		self.response.out.write(json.dumps(data))

		
class modules(webapp2.RequestHandler):
	def get(self):
		session = gaesessions.get_current_session()
		if session.is_active():
			if session['me'].UserType == 'USER_ADMIN' or session['me'].UserType == 'USER_CURATOR':
				m=Module.all()
				m.filter('ModuleStatus !=', 'Deleted')
				
				mods = Modifier_Rule.all()
				mods.order('ModKey')

				l=Language.all()
				
				u=User.all()
				u.filter('UserID =', session['me'].UserID)
				t = u.get()
			
				template_values = { 'modules' : m,
									'languages' : l,
									'mods' : mods,
									'user' : t}
			
				path = os.path.join(os.path.dirname(__file__), 'module.html')
				self.response.out.write(template.render(path, template_values))
			else:
				self.redirect('/signin')
		else:
			self.redirect('/signin')
		
		
class languages(webapp2.RequestHandler):
	def get(self):
		session = gaesessions.get_current_session()
		if session.is_active():
			if session['me'].UserType == 'USER_ADMIN':
				l=Language.all()
				u=User.all()
				
				u=User.all()
				u.filter('UserID =', session['me'].UserID)
				t = u.get()
			
				template_values = { 'languages' : l, 'user': t}
				
				
				logging.info(l)
			
				path = os.path.join(os.path.dirname(__file__), 'languages.html')
				self.response.out.write(template.render(path, template_values))
			else:
				self.redirect('/signin')
		else:
			self.redirect('/signin')
		
		
class images(webapp2.RequestHandler):
	def get(self):
		session = gaesessions.get_current_session()
		if session.is_active():
			if session['me'].UserType == 'USER_ADMIN':
				g=Glyph.all()
				u=User.all()
				
				l=Language.all()
				
				
				u=User.all()
				u.filter('UserID =', session['me'].UserID)
				t = u.get()
			
				template_values = { 'languages' : l, 'images' : g, 'user':t}
			
				path = os.path.join(os.path.dirname(__file__), 'images.html')
				self.response.out.write(template.render(path, template_values))
			else:
				self.redirect('/signin')
		else:
			self.redirect('/signin')
		
		
class getImageUploadURL(webapp2.RequestHandler):
	def get(self):
		url = blobstore.create_upload_url('/imageUploadHandler')
		
		json_out = {'result' : '200 OK', 'data' : url}
		self.response.headers['Content-Type'] = 'application/json'
		self.response.out.write(json.dumps(json_out))
		
		
class imageUploadHandler(blobstore_handlers.BlobstoreUploadHandler):
	def post(self):
		v=Variables.all()
		var=v.get()
	
		id = self.request.get('imageID')
		
		g=Glyph.all()
		g.filter('glyph_id =', id)
		glyph = g.get()
	
		upload_files = self.get_uploads('file')
	
		if glyph:
			glyph.glyph_comment = self.request.get('comment')
			
			if len(upload_files)>0:
				logging.info("set new blob")
				glyph.glyph_blob = upload_files[0].key()
				
			glyph.put()
		else:
			if len(upload_files)>0:
				g=Glyph(glyph_id = str(var.glyph_id_count),
						glyph_blob = upload_files[0].key(),
						glyph_comment = self.request.get('comment'),
						glyph_user_id = "",
						glyph_rights_protected = False)
				g.put()
				
				var.glyph_id_count+=1
				var.put()
		
		self.redirect('/images')
		
		
class getUploadWordURL(webapp2.RequestHandler):
	def get(self):
		url = blobstore.create_upload_url('/wordUploadHandler')
		
		json_out = {'result' : '200 OK', 'data' : url}
		self.response.headers['Content-Type'] = 'application/json'
		self.response.out.write(json.dumps(json_out))
		
		
class wordUploadHandler(blobstore_handlers.BlobstoreUploadHandler):
	def post(self):
		session = gaesessions.get_current_session()
		if session.is_active():
			if session['me'].UserType == 'USER_ADMIN' or session['me'].UserType == 'USER_CURATOR':
				v=Variables.all()
				var=v.get()
				
				upload_files = self.get_uploads('file')
				
				w=Word.all()
				w.filter('word_id =', self.request.get('wordID'))
				word=w.get()
				
				l=Language.all()
				l.filter('LanguageID =', session['me'].UserAdminLanguageID)
				lang = l.get()
							
				a = self.request.get('wordText')					
				wordText = urllib.unquote(str(a)).decode("utf-8") 
				
				logging.info(wordText)
				logging.info('language')
				logging.info(self.request.get('wordLanguage'))						
				logging.info(type(wordText))
	
				if word:
					word.word_text_root = wordText
					word.word_text_root_normalized = unicode(self.request.get('wordText').lower())
					word.word_syllables = self.request.get('wordSyllables')
					word.word_type = self.request.get('wordType')
					word.word_gender = self.request.get('wordGender')
					word.word_language = self.request.get('wordLanguage')	
					word.put() 
				
					r=Recording.all()
					r.filter('rec_type =', 'standard_word_recording')
					r.filter('rec_word_id =', word.word_id)
					
					if len(upload_files)>0:
						rec=r.get()
						rec.rec_mp3_blob = upload_files[0].key()
						rec.put()
				else:
					w=Word(	word_id = str(var.word_id_count),
							word_language = self.request.get('wordLanguage'),	
							word_creator_id = session['me'].UserID,
							word_type = self.request.get('wordType'),
							word_glyph_id = self.request.get('imageID'),
							word_syllables = "",
							word_text_root = wordText,
							word_text_root_normalized = unicode(self.request.get('wordText').lower()),
							word_text_mod_plural = [],
							word_text_mod_synonym = "",
							word_text_mod_opposite = "",
							word_text_mod_comp_super = [],
							word_text_mod_time_tense = [],
							word_programmable_text_root = "",
							word_programmable_glyph_list = [],
							word_programmable_state_count = "",
							word_programmable_valid_part = [],
							word_gender = self.request.get('wordGender'),
							word_sub_type = "")
							
					w.put()
					
					if len(upload_files)>0:
						r=Recording(rec_id = str(var.recording_id_count),
								rec_blob = upload_files[0].key(),
								rec_user_id = session['me'].UserID,
								rec_user_name = session['me'].UserUsername,
								rec_comment = "",
								rec_creation_date = datetime.utcnow(),
								rec_word_id = str(var.word_id_count),
								rec_type = 'standard_word_recording',
								rec_language = self.request.get('wordLanguage'),
								rec_mash_id = '0',
								rec_mp3_blob = upload_files[0].key())
						r.put()
					
					var.recording_id_count+=1
					var.word_id_count+=1
					var.put()
				
				self.redirect('/words')
			else:
				self.redirect('/signin')
		else:
			self.redirect('/signin')
		
		
class words(webapp2.RequestHandler):
	def get(self):
		session = gaesessions.get_current_session()
		if session.is_active():
			if session['me'].UserType == 'USER_ADMIN' or session['me'].UserType == 'USER_CURATOR':
				l=Language.all()
				l.filter('LanguageID =', session['me'].UserAdminLanguageID)
				lang = l.get()
				
				logging.info('lang ' + str(lang))
				logging.info('this is it')				
				logging.info(session['me'].UserAdminLanguageID)				

				u=User.all()
				u.filter('UserID =', session['me'].UserID)
				t = u.get()
						
				H=Language.all()		
						
				template_values = {'languages' : H, 'user' : t}									
			
				path = os.path.join(os.path.dirname(__file__), 'words.html')
				self.response.out.write(template.render(path, template_values))
			else:
				self.redirect('/signin')
		else:
			self.redirect('/signin')
		
		
class voices(webapp2.RequestHandler):
	def get(self):
		session = gaesessions.get_current_session()
		if session.is_active():
			if session['me'].UserType == 'USER_ADMIN':
				l=Language.all()
				u=User.all()
				
				l=Language.all()
				
			
				u=User.all()
				u.filter('UserID =', session['me'].UserID)
				t = u.get()
				
				template_values = { 'languages' : l,
									'user' : t}
			
				path = os.path.join(os.path.dirname(__file__), 'voices.html')
				self.response.out.write(template.render(path, template_values))
			else:
				self.redirect('/signin')
		else:
			self.redirect('/signin')
		
		
class users(webapp2.RequestHandler):
	def get(self):
		session = gaesessions.get_current_session()
		if session.is_active():
			if session['me'].UserType == 'USER_ADMIN':
				u=User.all()
				
				l=Language.all()
				
				
				a=User.all()
				a.filter('UserID =', session['me'].UserID)
				t = a.get()
								
				template_values = { 'languages' : l, 'users' : u , 'user' : t}
								
				path = os.path.join(os.path.dirname(__file__), 'users.html')
				self.response.out.write(template.render(path, template_values))
			else:
				self.redirect('/signin')
		else:
			self.redirect('/signin')
		
		
class getWords(webapp2.RequestHandler):
	def get(self):
		l = Language.all()
		l.filter('LanguageISOCode =', self.request.get('lang'))
		lang = l.get()
	
		w=Word.all()
		w.filter('word_language =', self.request.get('lang'))
		w.order('word_text_root')
		
		json_out = {}
		
		for item in w:
			json_out[item.word_id] = {'word_id' : item.word_id, 'word_text_root' : item.word_text_root, 'word_type' : item.word_type, 'word_glyph_id' : item.word_glyph_id, 'word_gender' : item.word_gender, 'word_syllables' : item.word_syllables}
		
		self.response.headers.add_header("Access-Control-Allow-Origin", "*")
		self.response.headers['Content-Type'] = 'application/json'
		self.response.out.write(json.dumps(json_out))
		
class getRecordings(webapp2.RequestHandler):
	def get(self):
		l = Language.all()
		l.filter('LanguageISOCode =', self.request.get('lang'))
		lang = l.get()
	
		w=Recording.all()
		json_out = []
							
		for item in w:
			time = item.rec_creation_date
			time = time.strftime("%B %d, %Y")	
			json_out.append({'rec_creation_date' : time, 'rec_language' : item.rec_language, 'rec_type' : item.rec_type, 'rec_word_id' : item.rec_word_id, 'rec_mash_id' : item.rec_mash_id, 'rec_id' : item.rec_id})
		
		logging.info('json_out')
		logging.info(json_out)
		
		self.response.headers.add_header("Access-Control-Allow-Origin", "*")
		self.response.headers['Content-Type'] = 'application/json'
		self.response.out.write(json.dumps(json_out))	

		
class getImages(webapp2.RequestHandler):
	def get(self):
		g=Glyph.all()
		
		json_out = []
		
		for item in g:
			logging.info(item.glyph_comment);
			json_out.append({'glyph_id' : item.glyph_id, 'glyph_comment' : item.glyph_comment})
			
		self.response.headers.add_header("Access-Control-Allow-Origin", "*")
		self.response.headers['Content-Type'] = 'application/json'
		self.response.out.write(json.dumps(json_out))

class saveMash(webapp2.RequestHandler):
	def post(self):
		
		tempStep = self.request.get('StepData').split('=\r\n')
		
		stepString=''
		
		v=Variables.all()
		var = v.get()	
		
		for item in tempStep:
			stepString+=item
		
		stepData = json.loads(stepString)
			
		if stepString == '""':
			keys = []
		else:
			keys = stepData.keys()
			
		files = {}
		
		for key in keys: 
			
			s=Step.all()
			stepNo = self.request.get('StepID')
			s.filter('StepID =', stepNo) #was key
			step = s.get()					
			if step == None:
			
				url = ''
			
			else:		
				
				m=Mash.all()
				mashID = self.request.get('mashID')
				m.filter('MashID =', mashID)
				mash = m.get()
				
				url=''
				
				logging.info('mashmeaningtext')
				logging.info(self.request.get('mashMeaningText'))
					
				mash.MashMeaningText = self.request.get('mashMeaningText')
				mash.MashReferenceVoiceURL = url		
				mash.MashValue = self.request.get('MashValue')		
													
				var.put()
				mash.put()
				

class saveStep(blobstore_handlers.BlobstoreUploadHandler):
	def post(self):
		
		v=Variables.all()
		var = v.get()	
		
		upload_files = self.get_uploads('audio')
	
		s=Step.all()
		stepID = str(self.request.get('StepID'))		
		s.filter('StepID =', stepID) 
		step = s.get()
		
		k=Language.all()
		langISO = str(self.request.get('ModuleCreationLanguage'))		
		logging.info('langISO ' + langISO)
		
		k.filter('LanguageISOCode =', langISO) 
		lang = k.get()
		
		logging.info('lang ')
		logging.info(lang)
		
		command = self.request.get('Command')		
		ModuleCreationLanguage = self.request.get('ModuleCreationLanguage')		
		logging.info(command)		
		logging.info(ModuleCreationLanguage)		
		
			
		if command == "add":
						
			t=Step.all()
			t.filter('StepModuleID =', self.request.get('StepModuleID'))
			currentStepNumber = int(self.request.get('StepNumber'))
			newStepNumber = int(currentStepNumber + 1)
			logging.info('current Step')
			logging.info(currentStepNumber)	
			
			logging.info('Step Order')
			logging.info(newStepNumber)	
			
			newStep = Step(	StepID = str(var.StepIDCount),
							StepTitle = 'New Step',
							StepSubtitle = '',
							StepRecordingConfig = 'NO',
							StepRatingConfig = 'NO',
							StepReferenceConfig = 'NO',
							StepRefAutoConfig = 'NO',
							StepRefVoiceURL = 'None',
							StepMashID = str(var.mash_id_count),
							StepModuleID = str(self.request.get('StepModuleID')),
							StepOrder = newStepNumber,
							StepStatus = 'OK')
													
			var.StepIDCount+=1				
			logging.info('newStep.StepID ')	
			logging.info(newStep.StepID)
			m=Module.all()
			m.filter('ModuleID =', self.request.get('StepModuleID'))
			mod = m.get()
			
			logging.info('Module ID is ' + self.request.get('StepModuleID'))
			logging.info('Old Module Step Count is ' + mod.ModuleStepCount)
			
			newModCount = int(mod.ModuleStepCount)
			newModCount = (newModCount + 1)
			logging.info('new module step count: ')
			logging.info(newModCount)
			mod.ModuleStepCount = str(newModCount)		
			mod.put()
			logging.info('New Module Step Count is ' + mod.ModuleStepCount)
			

			for stepInstance in t:
				if  stepInstance.StepOrder >= newStep.StepOrder :	
					stepInstance.StepOrder = stepInstance.StepOrder + 1					
					stepInstance.put()					
							
			#if ModuleCreationLanguage == 'gle':
			#	blankjson = '[{"PartType": "PART_VERB","Word": []}, {"PartType": "PART_SUBJECT","Word": [{"WordID": "0","WordImageURL": "img/player/blank.gif","WordType": "word_noun","WordSubtype": "","WordGender": "GENDER_NONE","Mod": []}]}, {"PartType": "PART_OBJECT","Word": []}]'				
			#else:
			#	blankjson = '[{"PartType":"PART_SUBJECT", "Word":[{"WordID":"0","WordImageURL":"img/player/blank.gif","WordType":"word_noun",  "WordSubtype":"", 	"WordGender":"GENDER_NONE", "Mod": [ ]}]},{"PartType":"PART_VERB","Word": []},{"PartType": "PART_OBJECT","Word": []}]'				
			
			partsOrdering = lang.PartsOrdering;
			#logging.info(partsOrdering)
			#logging.info('partsOrdering')
			
			#if ModuleCreationLanguage == 'gle':
			#	blankjson = '[{"PartType": "PART_VERB","Word": []}, {"PartType": "PART_SUBJECT","Word": [{"WordID": "0","WordImageURL": "img/player/blank.gif","WordType": "word_noun","WordSubtype": "","WordGender": "GENDER_NONE","Mod": []}]}, {"PartType": "PART_OBJECT","Word": []}]'				
			#else:
			#	blankjson = '[{"PartType":"PART_SUBJECT", "Word":[{"WordID":"0","WordImageURL":"img/player/blank.gif","WordType":"word_noun",  "WordSubtype":"", 	"WordGender":"GENDER_NONE", "Mod": [ ]}]},{"PartType":"PART_VERB","Word": []},{"PartType": "PART_OBJECT","Word": []}]'				
					
					
			partsOrderingArray = partsOrdering.split(',')					
			newjson = '['
						
			for parts in partsOrderingArray:
				logging.info(parts)
				parts = str(parts)
				
				if parts == 'verb':
					newjson += '{"PartType": "PART_VERB","Word": []},'
					logging.info('adding verb')
				elif parts == 'subject':
					newjson += '{"PartType": "PART_SUBJECT","Word": [{"WordID": "0","WordImageURL": "img/player/blank.gif","WordType": "word_noun","WordSubtype": "","WordGender": "GENDER_NONE","Mod": []}]},'
					logging.info('adding subject')
				elif parts == 'noun':
					newjson += '{"PartType": "PART_OBJECT","Word": [{"WordID": "0","WordImageURL": "img/player/blank.gif","WordType": "word_noun","WordSubtype": "","WordGender": "GENDER_NONE","Mod": []}]},'
					logging.info('adding noun')
				elif parts == 'object':
					logging.info('adding object')
					newjson += '{"PartType": "PART_OBJECT","Word": []},'
				
						
			newjson = newjson[:-1]	
			newjson += ']'	
				
			logging.info('newjson')
			logging.info(newjson)
			
			newMash = Mash(	MashID = str(var.mash_id_count),
							MashMeaningText = "",
							MashReferenceVoiceURL = 'None',
							MashValue = newjson )		
			
			var.mash_id_count+=1		
			newMash.put()			
			var.put()
			newStep.put()			
			
			
		elif command == 'saveExisting':			
			
			t=Step.all()
			t.filter('StepID =', str(self.request.get('StepID')))
			step = t.get()
			
			logging.info('Editing step : ' + stepID)
			logging.info('BLOB')
			logging.info(upload_files)
			
			if upload_files:
				logging.info('uploading new file')
				ModuleCreationLanguage = self.request.get('ModuleCreationLanguage')		
				url=""				
				r = Recording(	rec_id = str(var.recording_id_count),
								rec_blob = upload_files[0], 	#files[stepNo]
								rec_user_id = "0",
								rec_user_name = "0",
								rec_comment = "",
								rec_creation_date = datetime.utcnow(),
								rec_word_id = "0",
								rec_type = "StepRecording",
								rec_language = ModuleCreationLanguage,
								rec_mash_id = str(var.mash_id_count),
								rec_mp3_blob = None)				
				logging.info('rec_id ' + r.rec_id)
				logging.info('rec_mash_id ' + r.rec_mash_id)
				r.put()
				url = "/serve_mash_recording?id="+str(var.recording_id_count)				
				step.StepRefVoiceURL = url
				logging.info('created new recording ' + url)
				logging.info('created new recording in lang ' +  ModuleCreationLanguage)
				
				logging.info('stepID ' + str(self.request.get('StepID')))
			else:
				#step.StepRefVoiceURL = self.request.get('StepRefVoiceURL')
				#WITH THIS ON, IF SAVING EXISTING STEP AND NO NEW REC IS MADE, IT IS OVERWRITTEN BY LAST SAVED FIELD
				#IF RECORDED FOR FIRST TIME, THEN SAVEEXISTING STEP AGAIN, THIS OVERWRITES AS NULL
				# REC MADE, SAVED, THEN CALLING SAVING EXISTING FUNCTION WITH NUL STEPVOICEURL FROM JS, DELETING RECORDING IN BACKEND
				logging.info('StepRefVoiceURL IS')
				logging.info(self.request.get('StepRefVoiceURL'))
				logging.info('No new recording was made')
				
			step.StepReferenceConfig = self.request.get('StepReferenceConfig')
			step.StepRecordingConfig = self.request.get('StepRecordingConfig')
			step.StepRatingConfig = self.request.get('StepRatingConfig')	
			step.StepRefAutoConfig = self.request.get('StepRefAutoConfig')	
			logging.info('ref audio config')
			logging.info(self.request.get('StepRefAutoConfig')	)
			logging.info(step.StepRefAutoConfig)
			step.StepTitle = self.request.get('StepTitle')
				
			var.recording_id_count+=1			
			var.put()
			step.put()
				
		elif command == "remove":
									
			a=Step.all()
			a.filter('StepID =', str(self.request.get('StepID')))	
			currentStep = a.get()
			
			c=Step.all()
			c.filter('StepModuleID =', self.request.get('StepModuleID'))
			
			logging.info('current step order')
			logging.info(currentStep.StepOrder)
			
			
			for stepInstance in c:
				if  currentStep.StepOrder < stepInstance.StepOrder :
					logging.info('should be above current step, decrementing: ')				
					logging.info('StepID: ')
					logging.info(stepInstance.StepID)
					logging.info(' current stepInstance.StepOrder: ')
					logging.info(stepInstance.StepOrder)
					stepInstance.StepOrder = stepInstance.StepOrder - 1						
					stepInstance.put()
					
			currentStep.StepStatus = 'Deleted'
			currentStep.StepOrder = int(currentStep.StepOrder) - int(1000)
			currentStep.put()				
			
			r=Module.all()
			r.filter('ModuleID =', self.request.get('StepModuleID'))
			mod = r.get()
			
			logging.info('removing. current modstepCount: ' + mod.ModuleStepCount)
	
			newModCount = int(mod.ModuleStepCount )
			newModCount = (newModCount - 1)
			logging.info('new mod count: ')
			logging.info(newModCount)
			logging.info('string new mod count: ')
			logging.info(str(newModCount))
			mod.ModuleStepCount = str(newModCount)
			mod.put()
			
			logging.info('New Module Step Count is ')
			logging.info(mod.ModuleStepCount)
			
			
							
class saveModule(webapp2.RequestHandler):
	def post(self):
		
		m=Module.all()
		m.filter('ModuleID =', self.request.get('moduleID'))
		mod = m.get()
		
		v=Variables.all()
		var = v.get()
		
		if mod == None:
			mod = Module(	ModuleID = str(var.ModuleIDCount),
							ModuleCreatorID = "1",
							ModuleCreationDateTime = datetime.utcnow(),
							ModuleCreationLanguage = self.request.get('moduleCreationLanguage'),
							ModuleTitle = self.request.get('moduleTitle'),
							ModuleSubtitle = self.request.get('moduleSubtitle'),
							ModuleStepCount = "1",
							ModuleArtworkURL = 'CHAPPI-TEANGA-MONKEY-SMALL-WHITE.png',
							ModuleStatus = "InProgress")
			var.ModuleIDCount+=1
		
			
			newStep = Step(		StepID = str(var.StepIDCount),
								StepTitle = 'New Step',
								StepSubtitle = '',
								StepRecordingConfig = 'NO',
								StepRatingConfig = 'NO',
								StepReferenceConfig = 'NO',
								StepRefAutoConfig = 'NO',
								StepRefVoiceURL = 'None',
								StepMashID = str(var.mash_id_count),
								StepModuleID = str(mod.ModuleID),
								StepOrder = int("0"),
								StepStatus = 'OK')
			var.StepIDCount+=1
			
			ModuleCreationLanguage = self.request.get('moduleCreationLanguage')
			
			logging.info(ModuleCreationLanguage)
			
			#if ModuleCreationLanguage == 'gle':
			#	blankjson = '[{"PartType": "PART_VERB","Word": []}, {"PartType": "PART_SUBJECT","Word": [{"WordID": "0","WordImageURL": "img/player/blank.gif","WordType": "word_noun","WordSubtype": "","WordGender": "GENDER_NONE","Mod": []}]}, {"PartType": "PART_OBJECT","Word": []}]'				
			#else:
			#	blankjson = '[{"PartType":"PART_SUBJECT", "Word":[{"WordID":"0","WordImageURL":"img/player/blank.gif","WordType":"word_noun",  "WordSubtype":"", 	"WordGender":"GENDER_NONE", "Mod": [ ]}]},{"PartType":"PART_VERB","Word": []},{"PartType": "PART_OBJECT","Word": []}]'				
			
			logging.info('searching for ISO based on this language')
			
			k=Language.all()			
			k.filter('LanguageISOCode =', ModuleCreationLanguage)
			 
			logging.info(ModuleCreationLanguage)
			lang = k.get()
			partsOrdering = lang.PartsOrdering;
			partsOrderingArray = partsOrdering.split(',')
						
			logging.info('partsOrdering')	
			logging.info(partsOrdering)			
								
			newjson = '['
						
			for parts in partsOrderingArray:
				logging.info(parts)
				parts = str(parts)
				if parts == 'verb':
					newjson += '{"PartType": "PART_VERB","Word": []},'
				elif parts == 'subject':
					newjson += '{"PartType": "PART_SUBJECT","Word": [{"WordID": "0","WordImageURL": "img/player/blank.gif","WordType": "word_noun","WordSubtype": "","WordGender": "GENDER_NONE","Mod": []}]},'
				elif parts == 'object':
					newjson += '{"PartType": "PART_OBJECT","Word": []},'
				elif parts == 'noun':
					newjson += '{"PartType": "PART_OBJECT","Word": []},'
						
			newjson = newjson[:-1]	
			newjson += ']'	
				
			logging.info('newjson')
			logging.info(newjson)
			
			
			
			newMash = Mash(	MashID = str(var.mash_id_count),
								MashMeaningText = "",
								MashReferenceVoiceURL = 'None',
								MashValue = newjson )
				
			var.mash_id_count+=1		
			newMash.put()
			newStep.put()
			var.put()			
			
		else:
		
			logging.info('moduleTitle')
			logging.info(mod.ModuleTitle)
			logging.info(self.request.get('moduleTitle'))
		
			mod.ModuleTitle = self.request.get('moduleTitle')
			
			mod.ModuleSubtitle = self.request.get('moduleSubtitle')
			mod.ModuleCreationLanguage = self.request.get('moduleLanguage')
			mod.ModuleArtworkURL = self.request.get('moduleArtworkURL')
						
		mod.put()
		
		json_out = {'result' : '200 OK'}
		
		self.response.headers['Content-Type'] = 'application/json'
		self.response.out.write(json.dumps(json_out))
				
class removeItem(webapp2.RequestHandler):
	def get(self):
		type = self.request.get('type')		
		title = self.request.get('title')
		logging.info('REMOVING')
		logging.info(type)
		logging.info(title)		
		
		if type == 'Module':
			
			m=Module.all()
			m.filter('ModuleID =', self.request.get('id'))
			mod = m.get()
			
			if mod:
				title = mod.ModuleTitle
				mod.ModuleStatus = 'Deleted'
				mod.put()
				logging.info('deleted')
				
		if type == 'Step':
			s=Step.all()
			s.filter('StepID =', self.request.get('id'))
			step = s.get()
			logging.info('deleting step')
			
			if step:
				title = step.StepTitle
				step.StepStatus = 'Deleted'
				step.put()
				logging.info('deleted step')
				
		if type == 'Image':
			g=Glyph.all()
			g.filter('glyph_id =', self.request.get('id'))
			glyph = g.get()
			
			if glyph:
				glyph.delete()
				
		if type == 'Word':
			w=Word.all()
			w.filter('word_id =', self.request.get('id'))
			word = w.get()
			
			if word:
				word.delete()
		
		if type == 'User':
			u=User.all()
			u.filter('UserID =', self.request.get('id'))
			user = u.get()
			
			if user:
				user.delete()
		
class getUploadLink(webapp2.RequestHandler):
	def get(self):
		url = blobstore.create_upload_url('/saveStep')
		
		json_out = {'result' : '200 OK', 'data' : url, 'moduleID' : self.request.get('moduleID')}
		self.response.headers['Content-Type'] = 'application/json'
		self.response.out.write(json.dumps(json_out))
		
		
class ApiListHandler(webapp2.RequestHandler):
	def get(self, type):
		if type=="modules":
			m=Module.all()
			m.filter('ModuleStatus !=', 'Deleted')
			#m.order('ModuleID')
			m.get()
			
			l=Language.all()
			l.filter('LanguageSupported =', True)
			#m.order('ModuleID')
			l.get()
			
			moduleData = []
			moduleArray = []
			langArray = []
			
			for lang in l:
				langData = {'LanguageISOCode' : lang.LanguageISOCode, 'LanguageSupported' : lang.LanguageSupported, 'LanguageID' : lang.LanguageID, 'LanguageNameEnglish' : lang.LanguageNameEnglish, 'LanguageNameNative' : lang.LanguageNameNative, 'LanguageFlagURL' : lang.LanguageFlagURL}
				#moduleData.append(tempModule2)
				langArray.append(langData)	
			
			for module in m:
				modData = {'ModuleID' : module.ModuleID, 'ModuleTitle' : module.ModuleTitle, 'ModuleArtworkURL' : module.ModuleArtworkURL, 'ModuleCreationLanguage' : module.ModuleCreationLanguage, 'ModuleStatus' : module.ModuleStatus, 'LanguageInfo' : langArray }
				moduleData.append(modData)

			json_out = {'result' : '200 OK', 'message' : 'OK', 'data' : moduleData}
			
			self.response.headers.add_header("Access-Control-Allow-Origin", "*")
			self.response.headers['Content-Type'] = 'application/json'
			self.response.out.write(json.dumps(json_out))
		elif type=="steps":
			s=Step.all()
			s.filter('StepStatus =', 'OK')
			s.order('StepID')
			
			stepData = []
			
			for step in s:
				tempStep = {'StepID' : step.StepID, 'StepTitle' : step.StepTitle}
				stepData.append(tempStep)
			
			json_out = {'result' : '200 OK', 'message' : 'OK', 'data' : stepData}
			
			self.response.headers.add_header("Access-Control-Allow-Origin", "*")
			self.response.headers['Content-Type'] = 'application/json'
			self.response.out.write(json.dumps(json_out))
		else:
			self.redirect('/404/')

			
class ApiIDHandler(webapp2.RequestHandler):
	def get(self, type, id):
		if type == 'modules':
			m=Module.all()
			m.filter('ModuleID =', id)
			module = m.get()
			
			l=Language.all()
			l.filter('LanguageSupported =', True)
			lang = l.get()
			
			logging.info('languages')
			logging.info(lang)
			
			if module:
				moduleData = {'ModuleID' : module.ModuleID, 'ModuleCreatorID' : module.ModuleCreatorID, 'ModuleCreationDateTime' : module.ModuleCreationDateTime.strftime("%m/%d/%Y %I:%M %p"), 'ModuleTitle' : module.ModuleTitle, 'ModuleSubtitle' : module.ModuleSubtitle, 'ModuleArtworkURL' : module.ModuleArtworkURL, 'ModuleStatus' : module.ModuleStatus}
				message = 'OK'
				result = '200 OK'
			else:
				moduleData = {}
				message = 'Module Not Found'
				result = '404 Not Found'
				self.response.set_status(404)
			
			json_out = {'result' : result, 'message' : message, 'data' : moduleData}
			
			self.response.headers.add_header("Access-Control-Allow-Origin", "*")
			self.response.headers['Content-Type'] = 'application/json'
			self.response.out.write(json.dumps(json_out))
		elif type == 'steps':
			s=Step.all()
			s.filter('StepID =', id)
			step = s.get()
			
			if module:
				stepData = {'StepID' : step.StepID, 'StepTitle' : step.StepTitle, 'StepSubtitle' : step.StepSubtitle, 'StepRecordingConfig' : step.StepRecordingConfig, 'StepRatingConfig' : step.StepRatingConfig,  'StepRefVoiceURL' : step.StepRefVoiceURL, 'StepMashID' : step.StepMashID, 'StepRefAutoConfig' : step.StepRefAutoConfig}
				message = 'OK'
				result = '200 OK'
			else:
				stepData = {}
				message = 'Module Not Found'
				result = '404 Not Found'
				self.response.set_status(404)
			
			json_out = {'result' : result, 'message' : message, 'data' : stepData}
			
			self.response.headers.add_header("Access-Control-Allow-Origin", "*")
			self.response.headers['Content-Type'] = 'application/json'
			self.response.out.write(json.dumps(json_out))
		else:
			#should redirect to 404 page
			self.redirect('/404/')

			
class ApiStepHandler(webapp2.RequestHandler):
	def get(self, type1, id, type2):
		if type1 == 'modules':
			if type2 == 'steps':
				m=Module.all()
				m.filter('ModuleID =', id)
				module = m.get()
				
				if module:
					s=Step.all()
					s.filter('StepModuleID =', id)
					s.filter('StepStatus =', 'OK')
					s.order('StepOrder')
					
					stepData = []
					
					for step in s:
						m=Mash.all()
						m.filter('MashID =', step.StepMashID)
						mash = m.get()
						
						mashMeaningArray = mash.MashMeaningText.split()
						completedSearchArray = {}
						searchArray = []
							
						w=Word.all()
					
						if mash:
							mash_json = {'MashID' : mash.MashID, 'MashMeaningText' : mash.MashMeaningText, 'MashVoiceURL' : mash.MashReferenceVoiceURL, 'MashPart' : mash.MashValue} 
						else:
							mash_json={}
					
						temp_s = {'StepID' : step.StepID, 'StepTitle' : step.StepTitle, 'StepSubtitle' : step.StepSubtitle, 'StepRecordingConfig' : step.StepRecordingConfig, 'StepRatingConfig' : step.StepRatingConfig, 'StepReferenceConfig' : step.StepReferenceConfig, 'StepRefVoiceURL' : step.StepRefVoiceURL, 'StepMash' : mash_json, 'StepModuleID' : step.StepModuleID, 'StepOrder' : step.StepOrder, 'StepMeaningTextInfo' : searchArray, 'StepRefAutoConfig' : step.StepRefAutoConfig}
						logging.info(searchArray)
						
						stepData.append(temp_s)
					
					message = 'OK'
					result = '200 OK'
				else:
					stepData = []
					message = 'Module Not Found'
					result = '404 Not Found'
					
				json_out = {'result' : result, 'message' : message, 'data' : stepData}
			
				self.response.headers.add_header("Access-Control-Allow-Origin", "*")
				self.response.headers['Content-Type'] = 'application/json'
				self.response.out.write(json.dumps(json_out))
			else:
				self.redirect('/404')
		else:
			self.redirect('/404')
			
			
def getRandString(length):
	rand_string = ''
	chars = "abcdefghijklmnopqrstuvwxyz"
	for i in range(0,length):
		rand_string = rand_string+random.choice(chars)
	return rand_string
	
	
class changeLanguage(webapp2.RequestHandler):	
	def post(self):
		session = gaesessions.get_current_session()
	
		newLanguage = self.request.get('newLanguage')
		langType = self.request.get('langType')
		UserID = self.request.get('UserID')
		
		logging.info('changing language to: ' + newLanguage)
		logging.info('langType: ' + langType)
		
		m=User.all()
		m.filter('UserID =', UserID)
		user = m.get()
		
		if langType == 'learningLanguage':
			user.UserLearningLanguageID = newLanguage
		else:		
			user.UserAdminLanguageID = newLanguage
		
		user.put()
		
		
		self.response.out.write('completed')
		
class changeModuleStatus(webapp2.RequestHandler):	
	def post(self):
		session = gaesessions.get_current_session()
	
		ModuleID = self.request.get('ModuleID')
		NewModuleStatus = self.request.get('NewModuleStatus')
		
		m=Module.all()
		m.filter('ModuleID =', ModuleID)
		module = m.get()
			
		logging.info('TEST')	
		logging.info(module.ModuleStatus)
		logging.info(NewModuleStatus)
		
		module.ModuleStatus = NewModuleStatus
		
		module.put()	
	
		self.response.out.write('completed')

class changeLanguageStatus(webapp2.RequestHandler):	
	def post(self): 

		langISO = str(self.request.get('langISO'))
		
		logging.info(langISO)
		
		m=Language.all()
		m.filter('LanguageISOCode =', langISO)
		language = m.get()
		
		logging.info(language.LanguageSupported)
		
		if language.LanguageSupported == True:
			language.LanguageSupported = False
		elif language.LanguageSupported ==  False:
			language.LanguageSupported = True
		
		logging.info(language.LanguageSupported)
		
		language.put()	
	
		self.response.out.write('completed')
		

class addLanguage(webapp2.RequestHandler):	
	def post(self): 

		logging.info('creating new language')
		
		editExistingMode = str(self.request.get('editExistingMode'))
		
		logging.info(editExistingMode)
		
		if editExistingMode == 'false':
		
			logging.info('Adding language')
		
			m=Variables.all()
			#m.filter('Name/ID =', 'id=20002')
			globalLangVariables = m.get()
		
			logging.info('globalLangVariables.language_id_count')
			logging.info(globalLangVariables.language_id_count)
		
			
			langIDInt = int(globalLangVariables.language_id_count)
			langIDIntNew = langIDInt + 1
			
			
			logging.info(str(self.request.get('LanguageFlagURL')))
			
			logging.info('langIDInt')
			logging.info(langIDInt)
			
			langIDIntString = str(langIDInt + 1)
			
			logging.info('langIDIntString')
			logging.info(langIDIntString)
			
			globalLangVariables.language_id_count = langIDIntNew;
			globalLangVariables.put()
		
			logging.info('globalLangVariables.language_id_count')
			logging.info(globalLangVariables.language_id_count)
		
		
			partsOrder = str(self.request.get('PartsOrdering')).lower()
			
			logging.info(partsOrder)

			newLanguage = Language(	LanguageISOCode = str(self.request.get('LanguageISOCode')),
									LanguageNameNative = str(self.request.get('LanguageNameNative')),
									LanguageNameEnglish = str(self.request.get('LanguageNameEnglish')),
									LanguageSupported = False,
									PartsOrdering	 = partsOrder,
									LanguageFlagURL	 = str(self.request.get('LanguageFlagURL')),
									LanguageID = str(globalLangVariables.language_id_count)
									)
			newLanguage.put()	
		
		elif editExistingMode == 'true':
		
			logging.info('Editing existing')
			
			LanguageNameEnglish = str(self.request.get('LanguageNameEnglish'))
			LanguageNameEnglishOld = str(self.request.get('LanguageNameEnglishOld'))
		
			
			logging.info('LANG ENGLISH')
			logging.info(LanguageNameEnglishOld)
					
		
			l = Language.all()
			l.filter('LanguageNameEnglish =', LanguageNameEnglishOld)
			lang=l.get()
			
			partsOrder = str(self.request.get('PartsOrdering')).lower()
			partsOrder = str(partsOrder);
			
			logging.info(partsOrder)
	
			logging.info(type(partsOrder))
			
			logging.info('LANGTEST')
			logging.info(self.request.get('LanguageISOCode'))
			
			
			lang.LanguageISOCode = str(self.request.get('LanguageISOCode'))
			lang.LanguageNameNative = str(self.request.get('LanguageNameNative'))
			lang.LanguageNameEnglish = str(self.request.get('LanguageNameEnglish'))
			lang.PartsOrdering	 = partsOrder
			lang.LanguageFlagURL	 = str(self.request.get('LanguageFlagURL'))
			
			lang.put()	
		
		self.response.out.write('completed')		

class makeChange(webapp2.RequestHandler):
	def post(self): 
	
		id = str(self.request.get('id'))
	
		logging.info('id')
		logging.info(id)
	
		m=Recording.all()
		m.filter('rec_id =', id)
		word=m.get()
		
		if word != None:		
			logging.info('word')
			logging.info(word)
		
			if word.rec_language == 'English':
				logging.info('changing word param ');
				word.rec_language = 'eng'
		
			if word.rec_language == 'German':
				logging.info('changing word param ');
				word.rec_language = 'ger'
			
			if word.rec_language == 'Irish':
				logging.info('changing word param ');
				word.rec_language = 'gle'

			if word.rec_language == 'French':
				logging.info('changing word param ');
				word.rec_language = 'fre'
					
			if word.rec_language == 'German':
				logging.info('changing word param ');
				word.rec_language = 'ger'
				
			if word.rec_language == 'Spanish':
				logging.info('changing word param ');
				word.rec_language = 'spa'	
				
			a = Language.all()
			a.filter('LanguageNameEnglish =', word.rec_language)
			y = a.get()	
			word.rec_language = y.LanguageID	
				
				
			word.put()	
		
		else:
			logging.info('no word found')
		
		
class updateDB(webapp2.RequestHandler):
	def get(self):
	
		logging.info('updating db');	
		m=Recording.all()
		
		for instance in m:	
			taskqueue.add(queue_name='default', method='POST', url='/makeChange', params={'id' : instance.rec_id})
			
		
app = webapp2.WSGIApplication([
		('/', MainHandler),
		('/contact', contact),
		('/addLanguage', addLanguage),
		('/glyph_serve', glyph_serve),
		('/serve_recording', serve_recording),
		('/serve_mash_recording', serve_mash_recording),
		('/wordids', wordids),
		('/get_upload_url', get_upload_url),
		('/upload_mp3', upload_mp3),
		('/db_edit', db_edit),
		('/masher', masher),
		('/signup', signup),
		('/signin', signin),
		('/signout', signout),
		('/verify_user', verify_user),
		('/mailCheck', mailCheck),
		('/modules', modules),
		('/updateEntities', updateEntities),
		('/languages', languages),
		('/images', images),
		('/getImageUploadURL', getImageUploadURL),
		('/imageUploadHandler', imageUploadHandler),
		('/getUploadWordURL', getUploadWordURL),
		('/wordUploadHandler', wordUploadHandler),
		('/words', words),
		('/voices', voices),
		('/users', users),
		('/updateDB', updateDB),
		('/getWords', getWords),
		('/getRecordings', getRecordings),
		('/makeChange', makeChange),
		('/getImages', getImages),
		('/saveModule', saveModule),
		('/saveMash', saveMash),
		('/saveStep', saveStep),
		('/changeLanguage', changeLanguage),
		('/changeModuleStatus', changeModuleStatus),
		('/changeLanguageStatus', changeLanguageStatus),
		('/removeItem', removeItem),
		('/getUploadLink', getUploadLink),
		('/api/([^/]+)', ApiListHandler),
		('/api/([^/]+)/(\d+)', ApiIDHandler),
		('/api/([^/]+)/(\d+)/([^/]+)', ApiStepHandler),
		('/api/([^/]+)/([^/]+)/([^/]+)', ApiStepHandler),
		('/*', MainHandler)
], debug=True)