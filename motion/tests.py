import unittest

from django.db import models

from typepadapp.models.users import User


class ProfileTestCase(unittest.TestCase):

    def setUp(self):
        import typepadapp.models.profiles
        class UserProfile(typepadapp.models.profiles.UserProfile):
            hiphop_name = models.CharField(max_length=80)

        import motion.models
        motion.models.UserProfile = UserProfile

        from django.conf import settings
        settings.AUTH_PROFILE_MODULE = 'motion.UserProfile'

        from django.core import management
        management.call_command('syncdb', verbosity=1, interactive=False)

    def testProfile(self):
        from motion.models import UserProfile
        p = UserProfile(user_id='6paf37603c44724b3a',
            hiphop_name='dj fred')
        p.save()

        u = User(id='6paf37603c44724b3a')

        self.assertEquals(u.get_profile(), p)
