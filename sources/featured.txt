Featured accounts
=================

Motion sites can have *featured accounts*. If the Motion site has featured
accounts, the home page shows only those accounts' events, not the events of
all site members.

An account can also be marked featured on the TypePad cloud side. When an
account is so marked, external actions that happen on other sites are
collected by TypePad and provided in the accounts' profile.

These two behaviors together create the Motion app's "featured account"
experience: the home page is the profile event stream for the featured
account. Other site members can favorite and comment and even post new content
themselves, but their events are only shown on their profiles. (Apps in your
project can provide other member event views besides the home page, though.)

Featuring an account in Motion
------------------------------

To feature an account, set the ``FEATURED_MEMBER`` setting to that TypePad
user's XID::

    FEATURED_MEMBER = '6p0ddba11ba5eba11'

This will enable the featured home page view, providing only the named user's
events on the home page of the site.

Featuring an account in TypePad
-------------------------------

Again, user accounts must be featured on TypePad's side in order for TypePad
to collect those users' external behavior. Accounts are featured on TypePad
using the ``admin-typeapp`` tool available to TypePad operations staff.
