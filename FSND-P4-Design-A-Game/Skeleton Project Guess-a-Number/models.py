"""models.py - This file contains the class definitions for the Datastore
entities used by the Game. Because these classes are also regular Python
classes they can include methods (such as 'to_form' and 'new_game')."""

import random
from datetime import date
from protorpc import messages
from google.appengine.ext import ndb


class User(ndb.Model):
    """User profile"""
    name = ndb.StringProperty(required=True)
    email = ndb.StringProperty()


class Game(ndb.Model):
    """Game object, BaseBall
    Game rule: player needs to guess 3digits number.
    each digits are chosen from 0~9 and each digit can not be repeated.
    OK Target ex: 234, 942, 467, 103
    NG Target ex: 224, 949, 466, 100

    Players get feedback every time they guess number.
    number and digit matches --> "strike"
    number exists in target --> "ball"

    EX. Target = 234.
    Guess 234 = 3-strike and 0-ball where player won.
    Guess 235 = 2-strike and 0-ball where 2 and 3 matches with Target
    Guess 243 = 1-strike and 2-ball where 2 matches with Target, 4 and 3 exists in Target
    Guess 423 = 0-strike and 3-ball where 2, 3 and 4 exists in target but digit not matches
    Guess 782 = 0-strike and 1 ball where 2 exists in target but digit not matches

    Player ranking is evaluated by number of win.

    """
    target = ndb.IntegerProperty(repeated=True)
    user = ndb.KeyProperty(required=True, kind='User')
    game_over = ndb.BooleanProperty(required=True, default=False)
    cancelled = ndb.BooleanProperty(required=True, default=False)
    attempts_allowed = ndb.IntegerProperty(required=True, default=10)
    attempts_remaining = ndb.IntegerProperty(required=True, default=10)
    game_history = ndb.StringProperty(repeated=True)

    @classmethod
    def new_game(cls, user):
        """Creates and returns a new game"""
        # if max < min:
        #     raise ValueError('Maximum must be greater than minimum')
        game = Game(target=random.sample([0,1,2,3,4,5,6,7,8,9],3),
                    user=user,
                    game_over=False,
                    cancelled=False)
        game.put()
        return game

    def to_form(self, message):
        """Returns a GameForm representation of the Game"""
        form = GameForm()
        form.urlsafe_key = self.key.urlsafe()
        form.user_name = self.user.get().name
        form.attempts_remaining = self.attempts_remaining
        form.game_over = self.game_over
        form.message = message
        form.cancelled = self.cancelled
        form.target = self.target
        form.game_history = self.game_history
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
    attempts_remaining = messages.IntegerField(2, required=True)
    game_over = messages.BooleanField(3, required=True)
    message = messages.StringField(4, required=True)
    user_name = messages.StringField(5, required=True)
    cancelled = messages.BooleanField(6, required=True)
    target = messages.IntegerField(7, repeated=True)
    game_history = messages.StringField(8, repeated=True)

# Added for get_user_games
class GameForms(messages.Message):
    """Return multiple GameForm"""
    items = messages.MessageField(GameForm, 1, repeated=True)

class NewGameForm(messages.Message):
    """Used to create a new game"""
    user_name = messages.StringField(1, required=True)
    # min = messages.IntegerField(2, default=1)
    # max = messages.IntegerField(3, default=10)
    # attempts = messages.IntegerField(4, default=5)


class MakeMoveForm(messages.Message):
    """Used to make a move in an existing game"""
    first_digit = messages.IntegerField(1, required=True)
    second_digit = messages.IntegerField(2, required=True)
    third_digit = messages.IntegerField(3, required=True)


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
