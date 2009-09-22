import unittest

from django.db import models
from django.template import Context, Template
from django.utils.safestring import mark_safe

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

    def test_profile(self):
        from motion.models import UserProfile
        p = UserProfile(user_id='6paf37603c44724b3a',
            hiphop_name='dj fred')
        p.save()

        u = User(id='6paf37603c44724b3a')

        self.assertEquals(u.get_profile(), p)


class TwittilizeTestCase(unittest.TestCase):

    template = Template('{% load twittilize %}{{ testtext|twittilize }}')

    def run_tests(self, *args):
        for testtext, expected in args:
            context = Context({'testtext': testtext})
            result = self.template.render(context)
            self.assertEquals(result, expected)

    def test_basic(self):
        self.run_tests(
            ('', ''),
            ('a', 'a'),
            ('This is a test tweet.', 'This is a test tweet.'),
        )

    def test_links(self):
        self.run_tests(
            ('This ends with a link http://example.com/asfdasf',
             'This ends with a link <a href="http://example.com/asfdasf" rel="nofollow">http://example.com/asfdasf</a>'),
            ('This has a http://example.com/link in the middle',
             'This has a <a href="http://example.com/link" rel="nofollow">http://example.com/link</a> in the middle'),
            ('http://example.com/link at the start',
             '<a href="http://example.com/link" rel="nofollow">http://example.com/link</a> at the start'),
        )

    def test_usernames(self):
        self.run_tests(
            ('homg can you believe that crazy @example',
             'homg can you believe that crazy @<a href="http://twitter.com/example">example</a>'),
            ('RT @example This is a test tweet.',
             'RT @<a href="http://twitter.com/example">example</a> This is a test tweet.'),
            ('@example homg so many test tweets D:',
             '@<a href="http://twitter.com/example">example</a> homg so many test tweets D:'),
            ('@somebody @whobody @thatbody',
             '@<a href="http://twitter.com/somebody">somebody</a> '
                '@<a href="http://twitter.com/whobody">whobody</a> '
                '@<a href="http://twitter.com/thatbody">thatbody</a>'),
            ("I really liked @somebody's tweet",
             'I really liked @<a href="http://twitter.com/somebody">somebody</a>&#39;s tweet'),
        )

    def test_hashtags(self):
        self.run_tests(
            ('This is a tweet with a #hashtag',
             'This is a tweet with a <a href="http://twitter.com/search?q=#hashtag">#hashtag</a>'),
            ('This is a #tweet with an inline tag',
             'This is a <a href="http://twitter.com/search?q=#tweet">#tweet</a> with an inline tag'),
            ('#hashtags rarely come at the front',
             '<a href="http://twitter.com/search?q=#hashtags">#hashtags</a> rarely come at the front'),
            ('Using #some-long-hashtag is fine #spaces--',
             'Using <a href="http://twitter.com/search?q=#some-long-hashtag">'
                '#some-long-hashtag</a> is fine <a href="http://twitter.com/'
                'search?q=#spaces">#spaces</a>--'),
            ('Hashtags have #fU77&!$$(!)!($!)%#&@(#&$)nny_syntax!',
             'Hashtags have <a href="http://twitter.com/search?q=#fU77&amp;!'
                '$$(!)!($!)%#&amp;@(#&amp;$)nny_syntax">#fU77&amp;!$$(!)!($!'
                ')%#&amp;@(#&amp;$)nny_syntax</a>!'),
            ("#hashtags' syntax for #o'neill's stream",
             '<a href="http://twitter.com/search?q=#hashtags">#hashtags</a>'
                '&#39; syntax for <a href="http://twitter.com/search?q='
                """#o&#39;neill">#o&#39;neill</a>&#39;s stream"""),
        )

    def test_complex(self):
        self.run_tests(
            ('RT @monkinetic Grease Alley continues to grow: http://bit.ly/nmpoK #lego #scifi',
             'RT @<a href="http://twitter.com/monkinetic">monkinetic</a> '
                'Grease Alley continues to grow: '
                '<a href="http://bit.ly/nmpoK" rel="nofollow">http://bit.ly/nmpoK</a> '
                '<a href="http://twitter.com/search?q=#lego">#lego</a> '
                '<a href="http://twitter.com/search?q=#scifi">#scifi</a>'),
        )

    def test_safety(self):
        self.run_tests(
            ('I was <a href="http://example.com/awesome">totally</a> <script>bad_things()</script> and like hey',
             'I was &lt;a href=&quot;http://example.com/awesome&quot;&gt;totally&lt;/a&gt; &lt;script&gt;bad_things()&lt;/script&gt; and like hey'),
        )

    def test_futureproof(self):
        """Checks that the auto-linking doesn't auto-link strings that are
        already linked."""
        self.run_tests(
            (mark_safe('RT @<a href="http://twitter.com/monkinetic">monkinetic</a> '
                'Grease Alley continues to grow: '
                '<a href="http://bit.ly/nmpoK" rel="nofollow">http://bit.ly/nmpoK</a> '
                '<a href="http://twitter.com/search?q=#lego">#lego</a> '
                '<a href="http://twitter.com/search?q=#scifi">#scifi</a>'),
             'RT @<a href="http://twitter.com/monkinetic">monkinetic</a> '
                'Grease Alley continues to grow: '
                '<a href="http://bit.ly/nmpoK" rel="nofollow">http://bit.ly/nmpoK</a> '
                '<a href="http://twitter.com/search?q=#lego">#lego</a> '
                '<a href="http://twitter.com/search?q=#scifi">#scifi</a>'),
        )
