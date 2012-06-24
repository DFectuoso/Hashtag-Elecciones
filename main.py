from google.appengine.ext import webapp, db
from google.appengine.ext.webapp import util, template

import urlparse
import logging
import sys
sys.path.insert(0, 'libs/tweepy.zip')
sys.path.insert(0, 'libs/bitly_api')
from tweepy import *
import bitly_api

import keys
import json as simplejson

bitlyApi = bitly_api.Connection('dfectuoso','R_a6dce506708c38037af4143fd07076c4')

class Vote(db.Model):
  vote                 = db.StringProperty()
  ip       = db.StringProperty()
  created  = db.DateTimeProperty(auto_now_add=True)
  nickname             = db.StringProperty()

  @staticmethod
  def get_amlo_votes():
    return Vote.all().filter("vote", "amlo").count(100000)

  @staticmethod
  def get_jvm_votes():
    return Vote.all().filter("vote", "jvm").count(100000)

  @staticmethod
  def get_quadri_votes():
    return Vote.all().filter("vote", "quadri").count(100000)

  @staticmethod
  def get_epn_votes():
    return Vote.all().filter("vote", "epn").count(100000)

  @staticmethod
  def get_nadie_votes():
    return Vote.all().filter("vote", "nadie").count(100000)

class AccessRequest(db.Model):
  request_token_key    = db.StringProperty(required=True)
  request_token_secret = db.StringProperty(required=True) 
  vote                 = db.StringProperty(required=True)

class MainHandler(webapp.RequestHandler):
  def get(self):
    amlo = Vote.get_amlo_votes()
    jvm = Vote.get_jvm_votes()
    epn  = Vote.get_epn_votes()
    quadri = Vote.get_quadri_votes()
    nadie = Vote.get_nadie_votes()
    self.response.out.write(template.render('templates/main.html', locals()))

class JsonHandler(webapp.RequestHandler):
  def get(self):
    amlo = Vote.get_amlo_votes()
    jvm = Vote.get_jvm_votes()
    epn  = Vote.get_epn_votes()
    quadri = Vote.get_quadri_votes()
    nadie = Vote.get_nadie_votes()
    self.response.out.write(simplejson.dumps({'epn':epn,'amlo':amlo,'jvm':jvm,'quadri':quadri,'nadie':nadie}))

class VoteHandler(webapp.RequestHandler):
  def get(self,vote):
    amlo = Vote.get_amlo_votes()
    jvm = Vote.get_jvm_votes()
    epn  = Vote.get_epn_votes()
    quadri = Vote.get_quadri_votes()
    nadie = Vote.get_nadie_votes()
    self.response.out.write(template.render('templates/vote.html', locals()))
 
  def post(self,vote):
    # Create the AccessToken
    auth = OAuthHandler(keys.TWITTER_CONSUMER, keys.TWITTER_SECRET)
    auth_url = auth.get_authorization_url()
    AccessRequest(request_token_key = auth.request_token.key,
                  request_token_secret = auth.request_token.secret,
                  vote=vote).put()
    self.redirect(auth_url)

class OAuthCallbackHandler(webapp.RequestHandler):
  def get(self):
    oauth_token = self.request.get("oauth_token")
    access_requests = AccessRequest.all().filter("request_token_key", oauth_token).fetch(1)
    if len(access_requests) > 0:
      access_request = access_requests[0]
      vote = access_request.vote

      auth = OAuthHandler(keys.TWITTER_CONSUMER, keys.TWITTER_SECRET)
      auth.set_request_token(access_request.request_token_key, access_request.request_token_secret)
      auth.get_access_token(self.request.get("oauth_verifier"))
      api = API(auth)
      api_user = api.verify_credentials()

      # Create Vote, TODO Find_Or_Create
      voteObject = Vote.all().filter("nickname",api_user.screen_name).fetch(1)
      if len(voteObject) == 1:
        voteObject = voteObject[0]
        voteObject.vote = vote
        voteObject.put()
      else: 
        voteObject = Vote(vote=vote, nickname=api_user.screen_name, ip=self.request.remote_addr)
        voteObject.put()

      amlo = Vote.get_amlo_votes()
      jvm = Vote.get_jvm_votes()
      epn  = Vote.get_epn_votes()
      quadri = Vote.get_quadri_votes()
      nadie = Vote.get_nadie_votes()
      try:
        message = "Acabo de votar en #HashtagElecciones Mexico 2012: http://hashtagelecciones.appspot.com, van: Jvm "+str(jvm)+",Quadri "+str(quadri)+",EPN "+str(epn)+",AMLO "+str(amlo)+",Nulo:"+ str(nadie)
        logging.error("Message" + message)
        api.update_status(message)
      except:
        logging.error("Failed to update Status on OAuthCallback")
      self.redirect("/")

app = webapp.WSGIApplication([
    ('/', MainHandler),
    ('/json', JsonHandler),
    ('/vote/(.*)', VoteHandler),
    ('/oauth_callback', OAuthCallbackHandler),
  ], debug=True)
