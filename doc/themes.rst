Theming Motion
==============

The Motion templates support theming through both replacement templates and
new stylesheets and images.

Making a new theme
------------------

Start a new theme by making a new Django application in your project. Use the
special ``typepadapp`` command to get the basic theme file layout
automatically. For instance, if you were making a kittens theme, you'd make a
new ``kittens`` app::

    python manage.py typepadapp kittens

Once it's created, tell your Django project about it by adding it to your
``settings.py`` under ``INSTALLED_APPS``::

    INSTALLED_APPS = (
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'typepadapp',
        'motion',
        'kittens',
    )

Having Django serve your theme
------------------------------

Django will need to be able to translate the URL for your theme to the path on
disk where your app is installed. This works differently depending on how your
Motion project is being served.

If you're using the Django ``runserver`` during development, add your theme's
URL by adding your Django app to your project's urlconfs. Your app already has
an ``urls.py`` that will hook up your theme; you need only add it to your
project's URLs by adding it to the ``urls.py`` in the root of your project::

    urlpatterns = patterns('',
        (r'^', include('kittens.urls')),
        (r'^', include('motion.urls')),
        (r'^', include('typepadapp.urls')),
    )

Django can then serve your theme at the ``/static/themes/kittens/`` URL path.

When serving your project with mod_wsgi, files are served by Apache instead of
Django, so you'll need to add the ``Alias`` yourself in the Apache
configuration. That will look like this::

    Alias /static/themes/kittens /path/to/kittens/static/theme

This needs to be *before* any more general alias, such as ``/static`` or
``/``. There are probably other ``Alias`` lines in the Apache configuration
that you can add this new line with.

Selecting the new theme
-----------------------

Configure your project to use your theme with the ``THEME`` setting in your
``local_settings.py``::

    THEME = 'kittens'

The Motion templates will then link to your new theme. Yay!
