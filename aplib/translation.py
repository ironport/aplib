# Copyright (c) 2002-2011 IronPort Systems and Cisco Systems
#
# Permission is hereby granted, free of charge, to any person obtaining a copy  
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights  
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell 
# copies of the Software, and to permit persons to whom the Software is 
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in 
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE 
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# $Header: //prod/main/ap/aplib/aplib/translation.py#3 $

"""Internationalization support.

This module provides a more powerful interface to the gettext library. In
particular, it provides lazy evaluation support and the ability to register
multiple directories for the same domain.

You should reference the Python gettext module documentation or the GNU gettext
documentation (http://www.gnu.org/software/gettext/manual/gettext.html) for
more detail.  The GNU documentation is excellent and detailed, and provides
lots of information for translators.

This module does not use any of the globals used in the gettext module (like
``bindtextdomain`` or ``bind_textdomain_codeset``) nor does it install
functions into the builtin module like the ``gettext.install`` function does.
If you are using code that is unaware of this module, then you will still need
to register the domains with the ``gettext`` module.

Process Overview
================
The general process of internationalizing a program involves:

- Marking strings in the program for translation by wrapping them in one of the
  gettext functions.  (See `Basic Usage`_)

- Somewhere in your application you need to register the "domain" and the
  directory where your translations will reside.  (See `Registration`_)

- Extract the strings into a PO template file (using xgettext).  PO stands for
  "Portable Object".  (See `Translation Files`_)

- Copy the PO template to a PO file for a specific language (or use msginit).
  Or, if you are updating an existing file, use msgmerge to update an existing
  file.

- Edit the new PO file and add the translations for that language.

- Once all translations are done, convert the PO files to MO files using
  msgfmt.  MO stands for "Machine Object".

By default, the language that will be displayed when your program is run is
controlled by some environment variables.  Or, you can manually set the
language.  See `Language Selection`_.

Domains
=======
Gettext segregates translations into "domains".  A domain is just a simple
string that you come up with, typically the name of your application.  This
allows independent parts of code that have been independently translated to
reference their own sets of translations.

See `Recommended Usage`_ for suggestions about how to use domains.

Locale Names
============
The language and character set are determined by the "locale".  The format for
the locale name has several different formats:

- ``ll``: ISO 639 two-letter language code (typically lower-case).
- ``ll_CC``: ``CC`` is the ISO 3166 two-letter country code (typically upper-case).
- ``ll_CC.encoding``: This includes the character set encoding, such as
  ``UTF-8`` or ``ISO8859-1``.
- ``ll_CC@variant``: Indicates a variant of the language.  For example,
  ``sr_RS@latin`` is Serbian in Latin script whereas ``sr_RS`` is Serbian in
  Cyrillic.

There are two places where this comes into play.  The first is the directory name
you use to store your translation files.  The second is the language the user
chooses (such as through an environment variable).  Care must be taken so that
these two can map to one another.  See `Normalization`_ for more detail.

There is also a special locale called "C" which disables all localization.

Beware that HTTP uses a slightly different syntax for language codes in the
HTTP headers.  See RFC 3066 or RFC 4646 and RFC 2616.

ISO 639-2 provides three-letter codes for some rare languages.  The two-letter
should be used if it is available.

Basic Usage
===========
When you are marking strings for translation, you wrap them in a call to one
of the gettext functions.  For example::

    from aplib import translation

    print translation.gettext('Hello World')

Typical convention is to alias the call to gettext to a function called ``_``
such as::

    from aplib.translation import gettext as _

    print _('Hello World')

It is debatable whether or not to use underscore in Python.  It is also used as
the "previous value" in the shell and doctest tests, which may cause
interference.  Being explicit can force the programmer to determine which
function is the appropriate one.

Beware that when the strings are extracted from your application using xgettext
(or pygettext) that you must instruct it which identifiers you used to mark
your strings.  See `Translation Files`_ for more detail.

If no translation is available for the current language (or you have failed to
properly register your domain), then it will return the original message as-is.

If you are marking strings in the global scope to be translated, and your
application allows the user to change the language during runtime, then you
must defer the translation until it is displayed.  There are two ways you can
go about this.  One is to mark the messages with a null function so that
xgettext will find them, but wait to call the real translation function inside
your code.  Such as::

    from aplib.translation import gettext

    def _(message): return message

    sample_string = _('A string to be translated.')

    # Inside a function, use the real gettext call.
    def foo():
        print gettext(sample_string)

The other technique is to use the "lazy" variants of the gettext functions.
See `Lazy Evaluation`_ for more detail, but a sample would be::

    from aplib.translation import gettext_lazy as _

    sample_string = _('A string to be translated.')

    def foo():
        print sample_string

There are several different variants of the gettext function.  They are:

- `gettext`: The normal version which returns a string in the character set
  that the translation file for the current language was written in.

- `lgettext`: Variant that returns the message using the "preferred system
  encoding".

- `ugettext`: Variant that returns the value as a unicode object, if you prefer
  to use unicode.

- `dgettext`: Variant to get a translation for a specific domain.

- `ngettext`: Variant for translating strings that contain plurals.  See
  `Plurals`_ for more detail.

There are methods that combine the above variants, such as `ldgettext`,
`lngettext`, `ungettext`, `dngettext`, and `ldngettext`.

See the `Encodings`_ and `Usage Gotchas`_ sections for more detail on which
function to use.

Registration
============
When your application first starts up, you need to tell it where the
translation files are.  You do this with the `add_domain` function.

The global functions (`gettext`, `ugettext`, etc.) can only work against one
domain, known as the "global domain".  By default, when you call `add_domain`,
that domain is set as the global domain.  If you are using multiple domains,
you need to be clear which code may use the global versions and which code must
look up their domain explicitly (either using `dgettext` and its variants or
`get_domain`).

Language Selection
==================
By default, the system will determine the language to display by examining the
"LANGUAGE", "LC_ALL", "LC_MESSAGES", and "LANG" environment variables (in that
order).  These environment variables may list multiple preferred languages by
separating them with colons.  The first language that has an available
translation will be used.

You can set the current language with the `set_language` function. This will
set the preferred language globally.  Also, you may use the
`set_language_current_thread` function for setting the language on a per-thread
basis.

See `Normalization`_ below for issues with comparing locale names with
different variants.

See `Locale Names`_ above for detail about the format of the language string.
Note that this module is case-insensitive when comparing language strings.

Encodings
=========
A full discussion of encodings and character sets is well beyond the scope of
this documentation.  However, some issues are important to bring up.

Generally you want to show the content in the encoding that the user prefers
and can handle.  On a command-line app, this can be driven by the terminal type
and the language environment variables (though this is not very well
standardized).  For a web app, the acceptable character encodings are provided
by the "Accept-Charset" header.

By default, `gettext` will use the encoding that is stored in the translation
file. Depending on which character sets you want to support, and how your
translation files are stored, this may not be appropriate.  However, if (for
example) all of your translation files are stored in UTF-8 and you only want to
support UTF-8, then the `gettext` function is appropriate.

The `lgettext` function will use the "preferred system encoding".  This is
defined by the ``locale`` module and can be driven by the LANG environment
variable.  By default this is US-ASCII (because "C" is the default locale).  If
you are writing something like a web application, then using `lgettext` is not
appropriate because either you standardize on a consistent character encoding
(like UTF-8) or you let the user drive the correct encoding via their
Accept-Charset header.  If you are writing a command-line application, then
`lgettext` may be appropriate.

The `ugettext` function is best for full compatibility as long as your
application is unicode-aware.  By using unicode, you can differentiate between
bytes and characters (for things like determining the length of a string).  It
also allows you to defer the decision of which encoding to use until it is
displayed to the user.  However, this requires that your application is
unicode-aware and will convert the unicode object to bytes in the correct way.
Simply calling ``str()`` on a unicode object to display it is not appropriate
because it will use Python's default encoding which is hard-coded to "ascii".
You will need to use the ``encode`` method of the unicode objects to display
them in the appropriate character set.

It is helpful to understand that Python has two default encodings.  It has the
unicode default encoding, which is hard-coded to "ascii" unless overridden by a
sitecustomize module.  The unicode default encoding is used when converting a
string to a unicode object or vice versa without specifying the encoding. There
is also the ``locale`` module's default encoding, which is driven by the
language environment variables or manually set with the ``setlocale`` function.
The default is the "C" locale which defaults to the US-ASCII encoding.  The
locale default encoding is used by the `lgettext` function.

Normalization
=============
Because the locale name can take so many different forms, there are some rules
for how comparison of locale names is done.  Somehow we need to bridge the gap
between the locale the user has specified and the locale that your translations
files are saved as.

If the user uses the 2-letter abbreviated language code (such as ``en``), then
it will pick the language's main dialect.  Similarly, if the user does not
include the encoding (like ``ja_JP``) then it will use the default encoding
(which in that case is ``ja_JP.eucJP``).  These default mappings are hard-coded
in Python's ``locale`` module.

This module will always look for translation files based on that expansion of
the user's desired language.  The order it looks for translation files is
``ll_CC.encoding``, ``ll_CC``, ``ll.encoding``, ``ll``.

Some examples of this expansion:

- ``en``: ``('en_US.ISO8859-1', 'en_US', 'en.ISO8859-1', 'en')``
- ``en_GB``: ``('en_GB.ISO8859-1', 'en_GB', 'en.ISO8859-1', 'en')``
- ``ja_JP``: ``('ja_JP.eucJP', 'ja_JP', 'ja.eucJP', 'ja')``
- ``ja_JP.SJIS``: ``('ja_JP.SJIS', 'ja_JP', 'ja.SJIS', 'ja')``

In cases where you specify an unknown language or dialect, then the expansion
is slightly different:

- ``unknown``: ``('unknown',)``
- ``unknown_foo``: ``('unknown_foo', 'unknown')``
- ``en_unknown``: ``('en_unknown', 'en')``

Locale names are always compared case-insensitively.

See `Recommended Usage`_ for some thoughts about how to name your translation
directories and how to set your language.

Plurals
=======
How plurals are constructed is different for different languages.  The form
taken depends on the number of elements you are referring to.  Whenever you are
displaying a message that talks about the plurality of something, use
`ngettext` or one of its variants.  This allows the translator to provide the
appropriate forms for their language. `ngettext` assumes you are writing your
code in English (or similar) which has 2 plural forms where "singular" is used
when the count is 1, and "plural" is used otherwise.  Keep in mind that other
languages may use three or four different forms based on completely different
rules, and those rules are stored in the translation file.

Lazy Evaluation
===============
If you have an application where the user can change their language while it is
running, and if you have any strings defined in a global or class scope, then
you will need to somehow defer translation until it is displayed.  One way to
do that is to mark your message with a null function and then manually
translate it later in the code (as described in `Basic Usage`_).  Another
technique is to use the "lazy" variants of the gettext functions exposed in
this module.  These variants will return a `LazyTranslation` instance.  This
object behaves like a string.  Operations on a string object that return a
string are deferred as well (they return a different `LazyTranslation`
instance).  For example, you can have a deferred join of strings doing this::

    message1 = _('foo')
    message2 = _('bar')
    joined = _('').join((message1, message2))

``joined`` will be a ``LazyTranslation`` object.  When you convert it to a
string (like with ``str()``), it will first translate the two arguments, and
then join them together.

Translation Files
=================
Overview
--------
There are three types of translation files you should be aware of.  The first
is a POT file (Portable Object Template) with the extension of ``.pot``.  This
is the file that is generated when you run xgettext (or pygettext) over your
source code.  You then copy (or merge) that POT file to a PO file with the
extension of ``.po``. This is the file you send to the translator and they fill
with the translated text. You can also use the ``msginit`` program which will
fill in some of the metadata in the PO file.  Once you get the translated text
back, you use msgfmt to convert it to an MO file (Machine Object) with the
extension of ``.mo`` which is a binary format.

Extraction
----------
When you use xgettext (or pygettext) for extracting strings from your code, you
will need to be aware of which keywords it searches for.  By default, xgettext
in Python code will search for strings wrapped in one of the following function calls:

- ``gettext``
- ``ugettext``
- ``dgettext``
- ``ngettext``
- ``ungettext``
- ``dngettext``
- ``_``

If you use the extraction program that comes in Python's tools directory
(``pygettext.py``), it only uses the default keyword of ``_``.

Thus, in your code, if you have the following::

    from aplib.translation import gettext_lazy

    message = gettext_lazy('foo')

This will NOT get properly extracted by the default settings.  You will either
need to make sure your code uses one of the default keywords, or extend the
list of acceptable keywords when you run the extraction program.

Merging
-------
If you already have existing translations, and you update the code to change or
add existing strings, then you can use the ``msgmerge`` program to merge the
changes to an existing translation.  What you do is use ``xgettext`` to first
extract all the strings and generate a PO template file.  Then, you use
``msgmerge`` with the new template file and an old translation file.  It will,
for example, add any new strings.  It also supports fuzzy matching if you have
changed an existing string.

Usage Gotchas
=============
Unicode
-------
You need to be careful whenever dealing with strings in a specific encoding. If
you do not use Unicode, you will be limited on what you can do with a string.
For example, you will not be able to correctly determine the number of
characters in a string.  Another example is that if you attempt to truncate a
string, this will fail with some encodings.  If you use unicode, you will not
have these problems. However, if you use unicode, then your display layer will
need to be aware of it, and to know what character set it needs to be displayed
as.

Argument Strings
----------------
If you have a string where you are substituting multiple variables, use
dictionary-style format strings.  Different languages may need to rearrange the
arguments. It also gives the translator better context about what you are
trying to say.  For example::

    # This is BAD!
    print _('String "%s" has %d characters.') % (s, len(s))
    # This is CORRECT
    print _('String "%(str)s has %(num)d characters.') % {'str': s,
                                                          'num': len(s),
                                                         }

Even if you only have 1 argument, using dictionary formatting may be a good
idea to help the translator understand the context.

Also, make sure that the substitution is done outside of the gettext call::

    # This is BAD!
    print _('Hello, %s' % user)
    # This is CORRECT
    print _('Hello, %s') % user

Don't use string concatenation::

    # This is BAD!
    print _('Hello, ') + user
    # This is CORRECT
    print _('Hello, %s') % user

Ambiguity
---------
Avoid using short strings or sentence fragments::

    # This is BAD!
    print _('No match')
    # This is CORRECT
    print _('Your search did not match any entries.')

Don't separate a multi-line message into multiple calls::

    # This is BAD!
    print _('This is a test of')
    print _('a multi-line message.')
    # This is CORRECT
    print _('This is a test of\\n\\
    a multi-line message.')

Try to avoid messages more than 10 lines.  If you change one word in a very
large message, the translator will have to carefully proofread the entire thing
to understand what has changed.

Misc
----
- Beware of strings using plurals (see `Plurals`_).
- Make sure the extraction keywords you use with xgettext match what you use in
  your code.

Recommended Usage
=================
How you use gettext depends heavily on the type of application or library you
are making, and what needs you want to fulfil.  Some general guidelines to
think about:

- Domains: It is generally easier if all of your code uses one domain.  This
  allows you to use the global functions, and also simplifies the management of
  the translation files.  This depends a lot on how you release your code,
  whether it is an application, a framework, or a library, which languages you
  intend to support, and what costs you're willing to pay for translation.

- Encodings: UTF-8 is widely supported and is often a good choice.  However,
  there may be special circumstances that demand different encodings.  Just be
  aware of what your users want.

- Locale Names: When naming your locale directories, it generally helps to keep
  them as generic as possible.  So, instead of 'en_US' when you only have one
  English translation, use 'en'.

- Unicode: Use unicode if possible.  Just make sure your display layer is aware
  of it and will convert it to the correct encoding.

- Global strings: Use `LazyTranslation` objects whenever you have global
  strings.  It's easier to do this from the start than to retrofit it.  If you
  are using unicode, make sure your display layer is aware of the
  `LazyTranslation` instances and will encode them properly.

Misc Notes
==========
- Python does not require GNU gettext to be installed for it to work.  It even
  provides its own versions of xgettext and msgfmt (see Tools/i18n/pygettext.py
  and msgfmt.py).

References
==========
- Python gettext documentation: http://docs.python.org/library/gettext.html
- GNU gettext documentation:
  http://www.gnu.org/software/gettext/manual/gettext.html
- ISO 639 Two Letter Language Codes:
- ISO 639.2 Two and Three Letter Language Codes:
  http://www.loc.gov/standards/iso639-2/php/code_list.php

- RFC 4646 (for HTTP): http://www.ietf.org/rfc/rfc4646.txt
  (See older RFCs 3066 and 1766 for historical information.)
- Language identifiers (for HTTP): http://www.i18nguy.com/unicode/language-identifiers.html
"""

# Future ideas:
# - Set the default character set per language and/or per domain.
# - Set a default character set for unicode LazyTranslation instances so that
#   ``str`` works and the display layer does not need to be aware of
#   LazyTranslation.
# - Optimizations, such as the language normalization.

__version__ = '$Revision: #3 $'

import copy
import errno
import gettext as _gettext_module
import os

##############################################################################

def gettext(message):
    """Translate a string using the global domain.

    :Parameters:
        - `message`: The message to translate.

    :Return:
        Returns a translated string.  If no translation is available,
        then `message` is returned.
    """
    return _global_domain.gettext(message)

def lgettext(message):
    """Translate a string using the global domain using the preferred
    system encoding.

    The preferred system encoding can be determined by the
    ``locale.getpreferredencoding()`` function.  This can be controlled by
    calling ``setlocale`` or setting the ``LANG`` environment variable with a
    character set (such as "de_DE.UTF-8").

    :Parameters:
        - `message`: The message to translate.

    :Return:
        Returns a translated string.  If no translation is available,
        then `message` is returned.
    """
    return _global_domain.lgettext(message)

def ugettext(message):
    """Translate a string using the global domain.

    :Parameters:
        - `message`: The message to translate.

    :Return:
        Returns a unicode object of the translated string.  If no translation
        is available, then `message` is returned as a unicode string. Beware
        this is encoded with the default system unicode encoding set by
        ``sys.setdefaultencoding(...)`` which typically defaults to ASCII.
    """
    return _global_domain.ugettext(message)

def dgettext(domain, message):
    """Translate a string.

    :Parameters:
        - `domain`: The domain to use.
        - `message`: The message to translate.

    :Return:
        Returns a translated string.  If no translation is available,
        then `message` is returned.
    """
    return get_domain(domain).gettext(message)

def ldgettext(domain, message):
    """Translate a string.

    This is the domain-specific variant of `lgettext`, see that method for
    details.

    :Parameters:
        - `domain`: The domain to use.
        - `message`: The message to translate.

    :Return:
        Returns a translated string.  If no translation is available,
        then `message` is returned.
    """
    return get_domain(domain).lgettext(message)

def ngettext(singular, plural, n):
    """Translate a plural string using the global domain.

    :Parameters:
        - `singular`: The singular variant of the message to translate.
        - `plural`: The plural variant of the message to translate.
        - `n`: The count of things to determine singular or plural.

    :Return:
        Returns the correct singular or plural translated message. If no
        translation is available, then it will return `singular` if `n` is 1,
        otherwise `plural`.
    """
    return _global_domain.ngettext(singular, plural, n)

def lngettext(singular, plural, n):
    """Translate a plural string using the global domain using the preferred
    system encoding.

    This is the plural variant of `lgettext`, see that method for
    details.

    :Parameters:
        - `singular`: The singular variant of the message to translate.
        - `plural`: The plural variant of the message to translate.
        - `n`: The count of things to determine singular or plural.

    :Return:
        Returns the correct singular or plural translated message. If no
        translation is available, then it will return `singular` if `n` is 1,
        otherwise `plural`.
    """
    return _global_domain.lngettext(singular, plural, n)

def ungettext(singular, plural, n):
    """Translate a plural string using the global domain.

    This is the unicode variable of `ngettext`.  See `ugettext`
    for details and warnings about using unicode.

    :Parameters:
        - `singular`: The singular variant of the message to translate.
        - `plural`: The plural variant of the message to translate.
        - `n`: The count of things to determine singular or plural.

    :Return:
        Returns the correct singular or plural translated message as a unicode
        object. If no translation is available, then it will return the unicode
        version of `singular` if `n` is 1, otherwise `plural`.
    """
    return _global_domain.ungettext(singular, plural, n)

def dngettext(domain, singular, plural, n):
    """Translate a plural string.

    :Parameters:
        - `domain`: The domain to use.
        - `singular`: The singular variant of the message to translate.
        - `plural`: The plural variant of the message to translate.
        - `n`: The count of things to determine singular or plural.

    :Return:
        Returns the correct singular or plural translated message. If no
        translation is available, then it will return `singular` if `n` is 1,
        otherwise `plural`.
    """
    return get_domain(domain).ngettext(singular, plural, n)

def ldngettext(domain, singular, plural, n):
    """Translate a plural string using the preferred system encoding.

    This is the locale variant of `dngettext`.  See `lgettext` for details and
    about the preferred encoding.

    :Parameters:
        - `domain`: The domain to use.
        - `singular`: The singular variant of the message to translate.
        - `plural`: The plural variant of the message to translate.
        - `n`: The count of things to determine singular or plural.

    :Return:
        Returns the correct singular or plural translated message. If no
        translation is available, then it will return `singular` if `n` is 1,
        otherwise `plural`.
    """
    return get_domain(domain).lngettext(singular, plural, n)

##############################################################################

def gettext_lazy(message):
    """Lazy variant of `gettext`.

    :Return:
        Returns a `LazyTranslation` instance.
    """
    return LazyTranslation(None, 'gettext', (message,))

def lgettext_lazy(message):
    """Lazy variant of `lgettext`.

    :Return:
        Returns a `LazyTranslation` instance.
    """
    return LazyTranslation(None, 'lgettext', (message,))

def ugettext_lazy(message):
    """Lazy variant of `ugettext`.

    :Return:
        Returns a `LazyTranslation` instance.
    """
    return LazyTranslation(None, 'ugettext', (message,))

def dgettext_lazy(domain, message):
    """Lazy variant of `dgettext`.

    :Return:
        Returns a `LazyTranslation` instance.
    """
    return LazyTranslation(get_domain(domain), 'gettext', (message,))

def ldgettext_lazy(domain, message):
    """Lazy variant of `ldgettext`.

    :Return:
        Returns a `LazyTranslation` instance.
    """
    return LazyTranslation(get_domain(domain), 'lgettext', (message,))

def ngettext_lazy(singular, plural, n):
    """Lazy variant of `ngettext`.

    :Return:
        Returns a `LazyTranslation` instance.
    """
    return LazyTranslation(None, 'ngettext', (singular, plural, n))

def lngettext_lazy(singular, plural, n):
    """Lazy variant of `lngettext`.

    :Return:
        Returns a `LazyTranslation` instance.
    """
    return LazyTranslation(None, 'lngettext', (singular, plural, n))

def ungettext_lazy(singular, plural, n):
    """Lazy variant of `ungettext`.

    :Return:
        Returns a `LazyTranslation` instance.
    """
    return LazyTranslation(None, 'ungettext', (singular, plural, n))

def dngettext_lazy(domain, singular, plural, n):
    """Lazy variant of `dngettext`.

    :Return:
        Returns a `LazyTranslation` instance.
    """
    return LazyTranslation(get_domain(domain), 'ngettext', (singular, plural, n))

def ldngettext_lazy(domain, singular, plural, n):
    """Lazy variant of `ldngettext`.

    :Return:
        Returns a `LazyTranslation` instance.
    """
    return LazyTranslation(get_domain(domain), 'lngettext', (singular, plural, n))

##############################################################################

class LazyTranslation(object):

    """Lazy translation object.

    The lazy translation object provides a method to defer translation until a
    string is actually displayed to the user.  This is typically useful for
    strings defined in the global context.

    This object behaves like a string or unicode object, though it does
    not subclass either of them.  Operations that normally return a string like
    ``__add__``, ``__mod__`` or ``join`` will instead return another
    LazyTranslation object that defers the operation until the value is
    displayed.

    Comparison will compared the translated value.

    To get the resulting translation, you either use ``str``, ``unicode``,
    or ``encode`` or ``decode`` methods.  What you do depends on which
    lazy gettext method you called and how you want the data.

    Situation 1 - Unicode Function
    ------------------------------
    If you used one of the unicode functions like `ugettext_lazy`, then this
    object behaves like a unicode object.  In this case, you either call
    ``unicode(my_lazy)`` to get a unicode value or call something like
    ``my_lazy.encode('utf-8')`` to get a python string encoded in UTF-8.

    As with any unicode value, it is not recommended that you call
    ``str(my_lazy)`` because it will use the default encoding which is
    typically hard-coded to "ascii" unless overridden by a sitecustomize
    module.

    Situation 2 - String Function
    -----------------------------
    If you used one of the non-unicode functions like `gettext_lazy`, then this
    object behaves like a string object.  In this case, you either call
    ``str(my_lazy)`` to get a string, or call something like
    ``my_lazy.decode('utf-8')`` to get a unicode object (be careful, use
    whatever character set is appropriate for the current language).

    As with any string value, it is not recommended that you call
    ``unicode(my_lazy)`` because it will use the default encoding which is
    typically hard-coded to "ascii".

    See ``sys.getdefaultencoding()`` and ``sys.setdefaultencoding()`` for
    details about how the default unicode encoding is set.
    """

    _operations = ()

    def __init__(self, domain, method, args):
        self._domain = domain
        self._method = method
        self._args = args

    def _make_with_op(self, operation):
        l = LazyTranslation(self._domain, self._method, self._args)
        l._operations = self._operations + (operation,)
        return l

    @staticmethod
    def _convert_translation(x):
        if isinstance(x, LazyTranslation):
            return x._apply()
        else:
            return x

    def _apply(self):
        if self._domain is None:
            domain = _global_domain
        else:
            domain = self._domain
        result = getattr(domain, self._method)(*self._args)
        if self._operations:
            for operation in self._operations:
                op = operation[0]
                op_args = operation[1:]
                # Check for custom overrides.
                m = '_'+op
                if hasattr(self, m):
                    result = getattr(self, m)(result, *op_args)
                else:
                    # Otherwise, call the result's version.
                    # Convert any arguments from LazyTranslation to the real thing.
                    op_args = map(self._convert_translation, op_args)
                    result = getattr(result, op)(*op_args)
        return result

    def __str__(self):
        return str(self._apply())

    def __unicode__(self):
        return unicode(self._apply())

    ##########################################################################
    # Things that return a LazyTranslation.
    def __add__(self, other):
        return self._make_with_op(('__add__', other))
    def __mod__(self, other):
        return self._make_with_op(('__mod__', other))
    def __radd__(self, other):
        return self._make_with_op(('__radd__', other))
    def __mul__(self, n):
        return self._make_with_op(('__mul__', n))
    def __rmul__(self, n):
        return self._make_with_op(('__rmul__', n))
    def capitalize(self):
        return self._make_with_op(('capitalize',))
    def center(self, *args):
        return self._make_with_op(('center',) + args)
    def join(self, seq):
        return self._make_with_op(('join', seq))
    def ljust(self, *args):
        return self._make_with_op(('ljust',) + args)
    def lower(self):
        return self._make_with_op(('lower',))
    def lstrip(self, *args):
        return self._make_with_op(('lstrip',) + args)
    def replace(self, *args):
        return self._make_with_op(('replace',) + args)
    def rjust(self, *args):
        return self._make_with_op(('rjust',) + args)
    def rstrip(self, *args):
        return self._make_with_op(('rstrip',) + args)
    def strip(self, *args):
        return self._make_with_op(('strip',) + args)
    def swapcase(self):
        return self._make_with_op(('swapcase',))
    def title(self):
        return self._make_with_op(('title',))
    def translate(self, *args):
        return self._make_with_op(('translate',) + args)
    def upper(self):
        return self._make_with_op(('upper',))
    def zfill(self, width):
        return self._make_with_op(('zfill', width))
    def __cmp__(self, other):
        if isinstance(other, LazyTranslation):
            return cmp(self._apply(), other._apply())
        else:
            return cmp(self._apply(), other)

    ##########################################################################
    # Things that apply immediately.
    def __int__(self): return int(self._apply())
    def __long__(self): return long(self._apply())
    def __float__(self): return float(self._apply())
    def __complex__(self): return complex(self._apply())
    def __hash__(self): return hash(self._apply())
    def __contains__(self, char): return char in self._apply()
    def __len__(self): return len(self._apply())
    def __getitem__(self, index): return self._apply()[index]
    def __getslice__(self, start, end): return self._apply()[start:end]
    def count(self, *args): return self._apply().count(*args)
    def decode(self, *args): return self._apply().decode(*args)
    def encode(self, *args): return self._apply().encode(*args)
    def endswith(self, *args): return self._apply().endswith(*args)
    def expandtabs(self, *args): return self._apply().expandtabs(*args)
    def find(self, *args): return self._apply().find(*args)
    def index(self, *args): return self._apply().index(*args)
    def isalpha(self): return self._apply().isalpha()
    def isalnum(self): return self._apply().isalnum()
    def isdecimal(self): return self._apply().isdecimal()
    def isdigit(self): return self._apply().isdigit()
    def islower(self): return self._apply().islower()
    def isnumeric(self): return self._apply().isnumeric()
    def isspace(self): return self._apply().isspace()
    def istitle(self): return self._apply().istitle()
    def isupper(self): return self._apply().isupper()
    def partition(self, sep): return self._apply().partition(sep)
    def rfind(self, *args): return self._apply().rfind(*args)
    def rindex(self, *args): return self._apply().rindex(*args)
    def rpartition(self, sep): return self._apply().rpartition(sep)
    def split(self, *args): return self._apply().split(*args)
    def rsplit(self, *args): return self._apply().rsplit(*args)
    def splitlines(self, *args): return self._apply().splitlines(*args)
    def startswith(self, *args): return self._apply().startswith(*args)

    ##########################################################################
    # Deferred methods.
    def _join(self, data, seq):
        return data.join([self._convert_translation(x) for x in seq])

    def ___radd__(self, data, other):
        # str does not have radd.
        return self._convert_translation(other) + data


##############################################################################

class Domain(object):

    """Translation domain.

    This represents a gettext domain.  This may have multiple translation files
    registered (in separate directories) for the same domain.

    This exposes the standard gettext methods that will apply to this domain
    only.

    :IVariables:
        - `domain`: The name of the domain.
    """

    # Implementation notes:
    # - As a performance enhancement, instead of using the add_fallback
    #   mechanism, we could potentially use a "merge" technique where you use
    #   {}.merge() on the catalog in the GNUTranslation instance.  This would
    #   only matter if you use multiple locale directories.
    # - As a performance enhancement, we should consider caching the language
    #   normalization and mapping.

    # self._chained_trans is a dictionary with the key being the lowercase of
    # the language.  The value is a GNUTranslation instance with all the
    # directories added as fallbacks.

    # self._trans is a dictionary with the key being the lowercase of the
    # language.  The value is a list of (translation, localedir) tuples where
    # translation is a GNUTranslation instance and localedir is the directory
    # where this domain was loaded for this language.  We keep this separate
    # dictionary (from the _chained_trans) so that if a user calls
    # add_localedir with the same directory we'll reload that translation
    # from disk and rebuild the chained translation.

    def __init__(self, domain):
        self.domain = domain
        self._trans = {}
        self._chained_trans = {}
        # These two are used for optimizing refresh.
        self._mo_timestamps = {}
        self._localedir_langs = {}
        self._null = _gettext_module.NullTranslations()

    def add_localedir(self, localedir):
        localedir = os.path.abspath(localedir)
        # Dynamically find all languages.
        all_langs = self._find_all_langs(localedir)
        if not all_langs:
            raise IOError(errno.ENOENT, 'No translation file found for domain', self.domain)
        self._localedir_langs[localedir] = all_langs
        for lang, mofile in all_langs:
            lang = lang.lower()
            # Don't bother with gettext caching or lookup logic, we know
            # exactly what we want and we want to allow the user to reload
            # mofiles if they get updated.
            t = _gettext_module.GNUTranslations(open(mofile, 'rb'))
            st = os.stat(mofile)
            self._mo_timestamps[mofile] = st.st_mtime
            try:
                ts = self._trans[lang]
            except KeyError:
                self._trans[lang] = [(t, localedir)]
            else:
                # See if we've already seen this domain/localedir/lang.
                for index, (other_t, other_localedir) in enumerate(ts):
                    if other_localedir == localedir:
                        # Duplicate found, just replace it.
                        ts[index] = (t, localedir)
                        break
                else:
                    # Duplicate not found.
                    ts.append((t, localedir))

            # Rebuild the chained version.
            chained = copy.copy(self._trans[lang][0][0])
            self._chained_trans[lang] = chained
            for t, localedir in self._trans[lang][1:]:
                chained.add_fallback(copy.copy(t))

    def _find_all_langs(self, localedir):
        result = []
        filenames = os.listdir(localedir)
        for filename in filenames:
            path = os.path.join(localedir, filename)
            if os.path.isdir(path):
                mofile = os.path.join(path, 'LC_MESSAGES', self.domain + '.mo')
                if os.path.exists(mofile):
                    result.append((filename, mofile))
        # Sorted for comparison in _check_mo_update.
        result.sort()
        return result

    def refresh(self, check_timestamps=True):
        """Reload all translation files from disk.

        :Parameters:
            - `check_timestamps`: If True, will only refresh if a .mo file has
              been modified. If False, will unconditionally reload the .mo
              file.
        """
        localedirs = set()
        for tran_list in self._trans.values():
            for trans, localedir in tran_list:
                localedirs.add(localedir)
        for localedir in localedirs:
            if not check_timestamps or self._check_mo_update(localedir):
                self.add_localedir(localedir)

    def _check_mo_update(self, localedir):
        all_langs = self._find_all_langs(localedir)
        try:
            if self._localedir_langs[localedir] != all_langs:
                return True
        except KeyError:
            return True

        for lang, mofile in all_langs:
            st = os.stat(mofile)
            try:
                if self._mo_timestamps[mofile] != st.st_mtime:
                    return True
            except KeyError:
                # This should never happen.
                return True
        return False

    def _get_method(self, method):
        try:
            languages = _thread_language.languages
        except AttributeError:
            languages = _global_languages

        # There are opportunities for caching here to improve performance.
        # Things like language normalization are fairly complicated.  However
        # since the list of languages could potentially be provided by a user,
        # a long lived process could accumulate a lot of cached entries, so
        # it would require some pruning logic, which is more than I want to do
        # right now.
        for language in languages():
            language = language.lower()
            if language == 'c':
                # This is a special case that forces no translation
                # (English because of POSIX standard).
                return getattr(self._null, method)
            # Shouldn't really be poking our nose at an internal function,
            # but this seems better than copying the entire thing.
            for lang in _gettext_module._expand_lang(language):
                try:
                    trans = self._chained_trans[lang.lower()]
                except KeyError:
                    # This language is not available.
                    pass
                else:
                    return getattr(trans, method)
        else:
            # None of the languages are available.
            return getattr(self._null, method)

    def gettext(self, message):
        return self._get_method('gettext')(message)

    def lgettext(self, message):
        return self._get_method('lgettext')(message)

    def ugettext(self, message):
        return self._get_method('ugettext')(message)

    def ngettext(self, singular, plural, n):
        return self._get_method('ngettext')(singular, plural, n)

    def lngettext(self, singular, plural, n):
        return self._get_method('lngettext')(singular, plural, n)

    def ungettext(self, singular, plural, n):
        return self._get_method('ungettext')(singular, plural, n)

    def info(self):
        return self._get_method('info')()

    def __repr__(self):
        return 'Domain(\'%s\')' % (self.domain,)


##############################################################################

_domains = {}

_global_domain = Domain(None)

def add_domain(domain, localedir, set_as_global=True):
    """Add a domain.

    You may access this domain's specific translation functions by using
    the ``get_domain`` function.  If you set ``set_as_global``, then
    the global functions in this module will point to this domain.

    You may add the same domain multiple times with different localedirs,
    and those localedirs are appended to that domain's lookup sequence. If
    you specify the same domain/localedir pair as a previous call, then
    it will reload the catalog for that domain/localedir.

    :Parameters:
        - `domain`: A string of the domain to add.
        - `localedir`: The directory where to look for language files. It
          looks for language files matching the pattern
          ``localedir/<language>/LC_MESSAGES/<domain>.mo``.
        - `set_as_global`: Whether or not to set the global functions in this
          module to point to this domain.

    :Exceptions:
        - `IOError`: Translations for the given domain were not found at
          the given localedir.
    """
    global _global_domain

    try:
        d = _domains[domain]
    except KeyError:
        d = Domain(domain)
        _domains[domain] = d
    d.add_localedir(localedir)
    if set_as_global:
        _global_domain = d

def get_domain(domain):
    """Return a gettext domain translation object.

    This will always return a domain object, even if the domain has not yet
    been registered.  If a locale directory for this domain is later
    registered, then the domain object will start using that directory.

    :Parameters:
        - `domain`: The domain to get.

    :Return:
        Returns a `Domain` instance for this domain.
    """
    try:
        return _domains[domain]
    except KeyError:
        d = Domain(domain)
        _domains[domain] = d
        return d

def reset():
    """Clear all settings.

    This will remove all domains, reset the global translation, and remove all
    language settings and character sets.  This is mainly intended for the
    unittests.
    """
    global _global_domain
    _domains.clear()
    _global_domain = Domain(None)
    global _global_languages
    _global_languages = _global_default_languages
    global _thread_language
    _thread_language = _thread_local()

##############################################################################

def _global_default_languages():
    for var in ('LANGUAGE', 'LC_ALL', 'LC_MESSAGES', 'LANG'):
        value = os.environ.get(var)
        if value:
            languages = value.split(':')
            return languages
    else:
        # No environment variables set.
        return ()

_global_languages = _global_default_languages

def set_language(languages):
    """Set the global preferred language.

    This sets the preferred language.  ``languages`` can be a list of
    languages to use.  In this case, the first language found that has a
    matching translation available will be used.

    Alternatively, it can be a callable which will return a list of
    languages. This allows you to control the current language to use at
    runtime.

    If no language is ever set, then it will look at these environment variables
    in this order:

    - LANGUAGE
    - LC_ALL
    - LC_MESSAGES
    - LANG

    The environment variable may be a colon separated list of languages.

    :Parameters:
        - `languages`: A list of preferred languages, or a callback that
          will return the list of preferred languages.
    """
    # Check for potentially common mistake.
    if isinstance(languages, (str, unicode)):
        raise TypeError('languages must be a sequence or callable, not %s' % (type(languages),))

    global _global_languages
    if callable(languages):
        _global_languages = languages
    else:
        _global_languages = lambda: languages

def _thread_local():
    try:
        import coro
        return coro.ThreadLocal()
    except ImportError:
        import threading
        return threading.local()

_thread_language = _thread_local()

def set_language_current_thread(languages):
    """Set the preferred language for the current thread.

    This is the same as the `set_language` function, except it sets it for
    the current thread.  If you do not set the preferred language for a
    thread, then it will use the global setting from `set_language` or the
    environment variables if that has not been called.

    :Parameters:
        - `languages`: A list of preferred languages, or a callback that
          will return the list of preferred languages.
    """
    # Check for potentially common mistake.
    if isinstance(languages, (str, unicode)):
        raise TypeError('languages must be a sequence or callable, not %s' % (type(languages),))
    if callable(languages):
        callable_lang = languages
    else:
        callable_lang = lambda: languages
    _thread_language.languages = callable_lang
