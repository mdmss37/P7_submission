"""models.py - This file contains the class definitions for the Datastore
entities used by the Game. Because these classes are also regular Python
classes they can include methods (such as 'to_form' and 'new_game')."""

import random
from datetime import date
from protorpc import messages
from google.appengine.ext import ndb

# TODO: will increase wordlist.
WORDS_LIST = ["student", "teacher", "pineapple", "apple", "flower"]

class User(ndb.Model):
    """User profile"""
    name = ndb.StringProperty(required=True)
    email = ndb.StringProperty()


class Game(ndb.Model):
    """Game object, Hangman

    Player ranking is evaluated by number of win.

    """
    target = ndb.StringProperty(required=True)
    state = ndb.StringProperty(required=True)
    user = ndb.KeyProperty(required=True, kind='User')
    game_over = ndb.BooleanProperty(required=True, default=False)
    cancelled = ndb.BooleanProperty(required=True, default=False)
    attempts_allowed = ndb.IntegerProperty(required=True, default=6)
    attempts_remaining = ndb.IntegerProperty(required=True, default=6)
    game_history = ndb.StringProperty(repeated=True)

    @classmethod
    def new_game(cls, user):
        """Creates and returns a new game"""
        target = random.choice(WORDS_LIST)
        game = Game(target=target,
                    state="_"*len(target),
                    user=user,
                    game_over=False,
                    cancelled=False)
        game.put()
        return game

    def to_form(self, message):
        """Returns a GameForm representation of the Game"""
        form = GameForm()
        form.urlsafe_key = self.key.urlsafe()
        form.target = self.target
        form.state = self.state
        form.user_name = self.user.get().name
        form.game_over = self.game_over
        form.cancelled  = self.cancelled
        form.attempts_allowed = self.attempts_allowed
        form.attempts_remaining = self.attempts_remaining
        form.game_history = self.game_history
        form.message = message
        return form

    def end_game(self, won=False):
        """Ends the game - if won is True, the player won. - if won is False,
        the player lost."""
        self.game_over = True
        self.put()
        # Add the game to the score 'board'
        score = Score(user=self.user, date=date.today(), won=won,
                      guesses=self.attempts_allowed - self.attempts_remaining)
        score.put()


class Score(ndb.Model):
    """Score object"""
    user = ndb.KeyProperty(required=True, kind='User')
    date = ndb.DateProperty(required=True)
    won = ndb.BooleanProperty(required=True)
    guesses = ndb.IntegerProperty(required=True)

    def to_form(self):
        return ScoreForm(user_name=self.user.get().name, won=self.won,
                         date=str(self.date), guesses=self.guesses)


class GameForm(messages.Message):
    """GameForm for outbound game state information"""
    urlsafe_key = messages.StringField(1, required=True)
    target = messages.StringField(2, required=True)
    state = messages.StringField(3, required=True)
    user_name = messages.StringField(4, required=True)
    game_over = messages.BooleanField(5, required=True)
    cancelled = messages.BooleanField(6, required=True)
    attempts_allowed = messages.IntegerField(7, required=True)
    attempts_remaining = messages.IntegerField(8, required=True)
    game_history = messages.StringField(9, repeated=True)
    message = messages.StringField(10, required=True)

# Added for get_user_games
class GameForms(messages.Message):
    """Return multiple GameForm"""
    items = messages.MessageField(GameForm, 1, repeated=True)

class NewGameForm(messages.Message):
    """Used to create a new game"""
    user_name = messages.StringField(1, required=True)

class MakeMoveForm(messages.Message):
    """Used to make a move in an existing game"""
    character = messages.StringField(1, required=True)

class ScoreForm(messages.Message):
    """ScoreForm for outbound Score information"""
    user_name = messages.StringField(1, required=True)
    date = messages.StringField(2, required=True)
    won = messages.BooleanField(3, required=True)
    guesses = messages.IntegerField(4, required=True)


class ScoreForms(messages.Message):
    """Return multiple ScoreForms"""
    items = messages.MessageField(ScoreForm, 1, repeated=True)

class UserRank(messages.Message):
    """Return user ranking based on number of win"""
    user_name = messages.StringField(1, required=True)
    win_number = messages.IntegerField(2, required=True)

class UserRanks(messages.Message):
    """Return multiple UserRank"""
    items = messages.MessageField(UserRank, 1, repeated=True)

class StringMessage(messages.Message):
    """StringMessage-- outbound (single) string message"""
    message = messages.StringField(1, required=True)
