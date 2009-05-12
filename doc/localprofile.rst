Local Profiles
==============

The Motion app supports use of local profiles for its TypePad users. Local
profiles are additional custom fields that are stored in Motion's own
database, not in TypePad. While all TypePad profiles have the same fields,
individual Motion implementations can define their own local profile data for
their group members.


Defining the model
------------------

To store local profile data, use a Django model. The necessary functions for
are provided by the `typepadapp.models.profiles.UserProfile` model class, so
you need only subclass it and add the site's additional custom fields.

For example, you might add a `UserProfile` model to the ``motion.models``
module::

   from django.db import models

   import typepadapp.models.profiles

   class UserProfile(typepadapp.models.profiles.UserProfile):
       hiphop_name = models.CharField(max_length=80)

This model will provide one "Hiphop name" field. See the Django documentation
about models [#models]_ for what fields and options are available.


Telling Motion about the model
------------------------------

Once you've defined a local profile model, configure it in the settings as
your ``AUTH_PROFILE_MODULE``::

   AUTH_PROFILE_MODULE = 'motion.UserProfile'

See the Django documentation for ``AUTH_PROFILE_MODULE`` [#apm]_
for how to use it. Note that your ``AUTH_PROFILE_MODULE`` must be of the form
``package.Class``, where your module is in ``package.models.Class``. This is a
limitation of Django.


Customizing templates
---------------------

Once configured, the stock Motion profile will support it automatically
through the use of a Django form.

See the Django documentation on forms [#forms]_ and model forms [#modelform]_
for how they work.


.. rubric:: Footnotes

.. [#models] `Models <http://docs.djangoproject.com/en/1.0/topics/db/models/>`__
.. [#apm] `User authentication in Django: Storing additional information about users <http://docs.djangoproject.com/en/1.0/topics/auth/#storing-additional-information-about-users>`_
.. [#forms] `Working with forms <http://docs.djangoproject.com/en/1.0/topics/forms/>`_
.. [#modelform] `Creating forms from models <http://docs.djangoproject.com/en/1.0/topics/forms/modelforms/>`_
