#!/usr/bin/env python

"""main.py - This file contains handlers that are called by taskqueue and/or
cronjobs."""
import logging

import webapp2
from google.appengine.api import mail, app_identity
from api import HangManApi

from user import User
from models import Game


class SendReminderEmail(webapp2.RequestHandler):
    def get(self):
        """Send a reminder email to each User with an email about games.
        email will be sent player who has unfinished games.
        Called every day using a cron job"""
        app_id = app_identity.get_application_id()
        distribution = []
        users = User.query(User.email != None).fetch()
        games = Game.query().fetch()

        for user in users:
            for game in games:
                if (user.name == game.user_name) and (game.game_over == False):
                    distribution.append(user)
                    return

        for user in distribution:
            subject = 'This is a reminder!'
            body = 'Hello {}, try out Hangman!'.format(user.name)
            # This will send test emails, the arguments to send_mail are:
            # from, to, subject, body
            mail.send_mail('noreply@{}.appspotmail.com'.format(app_id),
                           user.email,
                           subject,
                           body)


class UpdateAverageMovesRemaining(webapp2.RequestHandler):
    def post(self):
        """Update game listing announcement in memcache."""
        HangManApi._cache_average_attempts()
        self.response.set_status(204)


app = webapp2.WSGIApplication([
    ('/crons/send_reminder', SendReminderEmail),
    ('/tasks/cache_average_attempts', UpdateAverageMovesRemaining),
], debug=True)
