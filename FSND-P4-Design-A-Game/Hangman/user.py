import random
from datetime import date
from protorpc import messages
from google.appengine.ext import ndb

class User(ndb.Model):
    """User profile"""
    name = ndb.StringProperty(required=True)
    email = ndb.StringProperty()

class UserRank(messages.Message):
    """Return user ranking based on number of win"""
    user_name = messages.StringField(1, required=True)
    win_number = messages.IntegerField(2, required=True)

class UserRanks(messages.Message):
    """Return multiple UserRank"""
    items = messages.MessageField(UserRank, 1, repeated=True)

class StringMessage(messages.Message):
    """StringMessage-- outbound (single) string message to user"""
    message = messages.StringField(1, required=True)