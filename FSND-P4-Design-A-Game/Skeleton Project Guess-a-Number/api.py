# -*- coding: utf-8 -*-`
"""api.py - Create and configure the Game API exposing the resources.
This can also contain game logic. For more complex games it would be wise to
move game logic to another file. Ideally the API will be simple, concerned
primarily with communication to/from the API's users."""


import logging
import endpoints
from protorpc import remote, messages
from google.appengine.api import memcache
from google.appengine.api import taskqueue

from models import User, Game, Score

# GameForms, UserRank, UserRanks added
from models import StringMessage, NewGameForm, GameForm, MakeMoveForm,\
    ScoreForms, GameForms, UserRank, UserRanks
from utils import get_by_urlsafe

NEW_GAME_REQUEST = endpoints.ResourceContainer(NewGameForm)
GET_GAME_REQUEST = endpoints.ResourceContainer(
        urlsafe_game_key=messages.StringField(1),)

GET_SCORE_REQUEST = endpoints.ResourceContainer(
    number_of_results=messages.IntegerField(1),)

MAKE_MOVE_REQUEST = endpoints.ResourceContainer(
    MakeMoveForm,
    urlsafe_game_key=messages.StringField(1),)
USER_REQUEST = endpoints.ResourceContainer(user_name=messages.StringField(1),
                                           email=messages.StringField(2))

MEMCACHE_MOVES_REMAINING = 'MOVES_REMAINING'

@endpoints.api(name='guess_a_number', version='v1')
class GuessANumberApi(remote.Service):
    """Game API"""
    @endpoints.method(request_message=USER_REQUEST,
                      response_message=StringMessage,
                      path='user',
                      name='create_user',
                      http_method='POST')
    def create_user(self, request):
        """Create a User. Requires a unique username"""
        # same user_name can not be used, user_name is unique
        if User.query(User.name == request.user_name).get():
            raise endpoints.ConflictException(
                    'A User with that name already exists!')
        user = User(name=request.user_name, email=request.email)
        user.put()
        return StringMessage(message='User {} created!'.format(
                request.user_name))

    @endpoints.method(request_message=NEW_GAME_REQUEST,
                      response_message=GameForm,
                      path='game',
                      name='new_game',
                      http_method='POST')
    def new_game(self, request):
        """Creates new game"""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                    'A User with that name does not exist!')
        try:
            game = Game.new_game(user.key)
        except ValueError:
            raise endpoints.BadRequestException('Maximum must be greater '
                                                'than minimum!')

        # Use a task queue to update the average attempts remaining.
        # This operation is not needed to complete the creation of a new game
        # so it is performed out of sequence.
        taskqueue.add(url='/tasks/cache_average_attempts')
        return game.to_form('Good luck playing Guess a Number!')

    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}',
                      name='get_game',
                      http_method='GET')
    def get_game(self, request):
        """Return the current game state."""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game:
            return game.to_form('Time to make a move!')
        else:
            raise endpoints.NotFoundException('Game not found!')

    @endpoints.method(request_message=MAKE_MOVE_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}',
                      name='make_move',
                      http_method='PUT')
    def make_move(self, request):
        """Makes a move. Returns a game state with message"""
        strike = 0
        ball = 0

        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game.game_over:
            return game.to_form('Game already over!')

        target = game.target
        copy_target = target[:]

        game.attempts_remaining -= 1
        # check strike and if strike, change target digit to "s" for check ball
        if request.first_digit == copy_target[0]:
            strike += 1
            copy_target[0] = 9999
        if request.second_digit == copy_target[1]:
            strike += 1
            copy_target[1] = 9999
        if request.third_digit == copy_target[2]:
            strike += 1
            copy_target[2] = 9999
        # check ball
        if request.first_digit in copy_target:
            ball += 1
        if request.second_digit in copy_target:
            ball += 1
        if request.third_digit in copy_target:
            ball += 1

        if strike == 3:
            # TODO: can make add history function
            game.game_history.append(
                "Guess: {}{}{}, result: {} strike and {} ball".format(
                request.first_digit, request.second_digit, request.third_digit,
                strike, ball))
            game.end_game(True)
            return game.to_form('You win!')
        else:
            msg = "{} strike and {} ball!".format(str(strike), str(ball))

        if game.attempts_remaining < 1:
            game.game_history.append(
                "Guess: {}{}{}, result: {} strike and {} ball".format(
                request.first_digit, request.second_digit, request.third_digit,
                strike, ball))
            game.end_game(False)
            return game.to_form(msg + ' Game over!')
        else:
            game.game_history.append(
                "Guess: {}{}{}, result: {} strike and {} ball".format(
                request.first_digit, request.second_digit, request.third_digit,
                strike, ball))
            game.put()
            return game.to_form(msg)

    @endpoints.method(response_message=ScoreForms,
                      path='scores',
                      name='get_scores',
                      http_method='GET')
    def get_scores(self, request):
        """Return all scores"""
        return ScoreForms(items=[score.to_form() for score in Score.query()])

    @endpoints.method(request_message=USER_REQUEST,
                      response_message=ScoreForms,
                      path='scores/user/{user_name}',
                      name='get_user_scores',
                      http_method='GET')
    def get_user_scores(self, request):
        """Returns all of an individual User's scores"""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                    'A User with that name does not exist!')
        scores = Score.query(Score.user == user.key)
        return ScoreForms(items=[score.to_form() for score in scores])

    @endpoints.method(response_message=StringMessage,
                      path='games/average_attempts',
                      name='get_average_attempts_remaining',
                      http_method='GET')
    def get_average_attempts(self, request):
        """Get the cached average moves remaining"""
        return StringMessage(message=memcache.get(MEMCACHE_MOVES_REMAINING) or '')

    @staticmethod
    def _cache_average_attempts():
        """Populates memcache with the average moves remaining of Games"""
        games = Game.query(Game.game_over == False).fetch()
        if games:
            count = len(games)
            total_attempts_remaining = sum([game.attempts_remaining
                                        for game in games])
            average = float(total_attempts_remaining)/count
            memcache.set(MEMCACHE_MOVES_REMAINING,
                         'The average moves remaining is {:.2f}'.format(average))

    # Extend API, get_user_games: This returns all of a User's active games.
    @endpoints.method(request_message=USER_REQUEST,
                      response_message=GameForms,
                      path='games/user/active/{user_name}',
                      name='get_user_active_games',
                      http_method='GET')
    def get_user_active_games(self, request):
        """This returns all of a User's active games"""
        user = User.query(User.name == request.user_name).get()
        games = Game.query(Game.user == user.key, Game.game_over == False,
                           Game.cancelled == False).fetch()
        return GameForms(items=[game.to_form("Active games of {}".format(user.name)) for game in games])

    # Extend API, get_user_games: This returns all of a User's all games.
    @endpoints.method(request_message=USER_REQUEST,
                      response_message=GameForms,
                      path='games/user/all/{user_name}',
                      name='get_user_all_games',
                      http_method='GET')
    def get_user_all_games(self, request):
        """This returns all of a User's active/finished games"""
        user = User.query(User.name == request.user_name).get()
        games = Game.query(Game.user == user.key).fetch()
        return GameForms(items=[game.to_form("All games of {}".format(user.name)) for game in games])

    # Extend API,cancel_game: This endpoint allows users to cancel a game in progress
    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=StringMessage,
                      path='game/cancel/{urlsafe_game_key}',
                      name='cancel_game',
                      http_method='PUT')
    def cancel_game(self, request):
        """Cancel game in progress."""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game:
            game.cancelled = True
            game.put()
            return StringMessage(message="Current game has been cancelled!")
        else:
            raise endpoints.NotFoundException('Game not found!')

    # Extend API,get_high_scores: This endpoint is to return highscores of games,
    # Can be limited by optional parameter number_of_results
    @endpoints.method(request_message=GET_SCORE_REQUEST,
                      response_message=ScoreForms,
                      path='game/highscores',
                      name='get_high_scores',
                      http_method='GET')
    def get_high_scores(self, request):
        """return highscores limited with number_of_results"""
        if request.number_of_results:
            scores = Score.query().order(Score.guesses).fetch(limit = request.number_of_results)
        else:
            scores = Score.query().order(Score.guesses).fetch()
        return ScoreForms(items=[score.to_form() for score in scores])

    @endpoints.method(response_message=UserRanks,
                      path='user/rankings',
                      name='get_user_rankings',
                      http_method='GET')
    def get_user_rankings(self, request):
        """Return UserRank class, sorted by win_number with descending order"""
        items = []
        users = User.query().fetch()

        for user in users:
            win_number = 0
            scores = Score.query(Game.user == user.key).fetch()

            for score in scores:
                if score.won == True:
                    win_number += 1

            items.append(UserRank(user_name=user.name, win_number=win_number))
        items.sort(key=lambda x: x.win_number, reverse=True)
        return UserRanks(items=items)

    # Extend API, get_game_history:
    # Your API Users may want to be able to see a 'history' of moves for each game.
    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=GameForm,
                      path='game/history/{urlsafe_game_key}',
                      name='get_game_history',
                      http_method='GET')
    def get_game_history(self, request):
        """return game history of certain game"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        # TODO: need to check the way to show only Game history
        return game.to_form("Please check Game history!")

api = endpoints.api_server([GuessANumberApi])
