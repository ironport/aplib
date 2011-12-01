# -*- coding: utf-8 -*-
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

"""Unittests for translation module.



- Talk about noramlization and setting language and locale aliasing with default encoding.
"""

__version__ = '$Revision: #2 $'


from aplib import translation
import unittest
import os
import shutil
import time
import unittest

class Test(unittest.TestCase):

    foo_expected = {
        'en_US':
            {'test': 'test',
             'test1': 'test1',
             'test2': 'test2',
             'test3': 'test3',
             'test4': 'oddball',
             'test5': 'test5',
             'missing': 'missing',
            },
        'de_DE':
            {'test': 'groß',
             'test1': 'für',
             'test2': 'test2',
             'test3': 'test3',
             'test4': 'freundleben',
             'test5': 'zeitgeist',
             'missing': 'missing',
            },
        'es':
            {'test': 'Español',
             'test1': 'burrito',
             'test2': 'quesadilla',
             'test3': 'taco',
             'test4': 'paella',
             'test5': 'test5',
             'missing': 'missing',
            },
    }

    def setUp(self):
        translation.reset()

    def _localedir(self, name):
        return os.path.join(os.getcwd(), 'translation', name)

    def test_gettext(self):
        translation.add_domain('foo', self._localedir('locale1'))
        for lang, matches in self.foo_expected.items():
            translation.set_language((lang,))
            for source, trans in matches.items():
                for method in ('gettext', 'gettext_lazy'):
                    m = getattr(translation, method)
                    self.assertEqual(m(source), trans)
                for method in ('ugettext', 'ugettext_lazy'):
                    m = getattr(translation, method)
                    self.assertEqual(m(source), unicode(trans, 'utf-8'))

    def test_preferred_locale(self):
        translation.add_domain('foo', self._localedir('locale1'))
        for lang, matches in self.foo_expected.items():
            translation.set_language((lang,))
            for source, trans in matches.items():
                try:
                    unicode(trans, 'US-ASCII')
                except UnicodeDecodeError:
                    self.assertRaises(UnicodeEncodeError, translation.lgettext, source)
                    l = translation.lgettext_lazy(source)
                    self.assertRaises(UnicodeEncodeError, lambda: str(l))
                    self.assertRaises(UnicodeEncodeError, lambda: unicode(l))
                else:
                    self.assertEqual(translation.lgettext(source), trans)
                    self.assertEqual(translation.lgettext_lazy(source), trans)
                os.environ['LANG'] = 'es_ES.UTF-8'
                try:
                    self.assertEqual(translation.lgettext(source), trans)
                    self.assertEqual(translation.lgettext_lazy(source), trans)
                finally:
                    del os.environ['LANG']

    def test_funky_encoding(self):
        translation.add_domain('foo', self._localedir('locale1'))
        translation.set_language(('ja_JP.SJIS',))
        self.assertEqual(translation.gettext('test'), '\x82\x9f\x83@\xea\x9f\xea\xa2')
        # Default locale is normally us-ascii, can't convert shift-jis to ASCII.
        self.assertRaises(UnicodeEncodeError, translation.lgettext, 'test')
        os.environ['LANG'] = 'ja_JP.SJIS'
        try:
            self.assertEqual(translation.lgettext('test'), '\x82\x9f\x83@\xea\x9f\xea\xa2')
            os.environ['LANG'] = 'ja_JP.UTF-8'
            self.assertEqual(translation.lgettext('test'), '\xe3\x81\x81\xe3\x82\xa1\xe5\xa0\xaf\xe7\x91\xa4')
        finally:
            del os.environ['LANG']
        self.assertEqual(translation.ugettext('test'), u'\u3041\u30a1\u582f\u7464')

    def test_lazy(self):
        translation.add_domain('foo', self._localedir('locale1'))
        translation.set_language(('es',))
        l1 = translation.gettext_lazy('test')
        self.assertTrue(isinstance(l1, translation.LazyTranslation))
        l2 = translation.gettext_lazy('test1')

        self.assertTrue(isinstance(l1 + l2, translation.LazyTranslation))
        self.assertEqual(str(l1 + l2), 'Españolburrito')

        m = translation.gettext_lazy('test %(arg1)s %(arg2)s') % {'arg1': 'one',
                                                                  'arg2': 'two',
                                                                 }
        self.assertTrue(isinstance(m, translation.LazyTranslation))
        self.assertEqual(str(m), 'chalupa two one')

        m = int(translation.gettext_lazy('1'))
        self.assertTrue(isinstance(m, int))
        self.assertEqual(m, 1)

        m = translation.gettext_lazy('-').join(
            (translation.gettext_lazy('test'),
             translation.gettext_lazy('test1')))
        self.assertTrue(isinstance(m, translation.LazyTranslation))
        self.assertEqual(str(m), 'Español-burrito')

        # Not going to test all the LazyTranslation methods.

        # dgettext_lazy and ldgettext_lazy handled by test_domain.
        # ugettext_lazy tested by test_gettext
        # lgettext_lazy tested by test_preferred_locale

        # chain a few operations together
        m1 = translation.gettext_lazy('test')
        m2 = translation.gettext_lazy('test1')
        m3 = m1 + m2
        self.assertTrue(isinstance(m3, translation.LazyTranslation))
        self.assertEqual(m3, 'Españolburrito')
        m4 = m3 * 2
        self.assertTrue(isinstance(m4, translation.LazyTranslation))
        self.assertEqual(str(m4), 'EspañolburritoEspañolburrito')
        m5 = m4.lower()
        self.assertTrue(isinstance(m5, translation.LazyTranslation))
        self.assertEqual(m5.decode('utf-8'), u'españolburritoespañolburrito')
        self.assertEqual(str(m5), 'españolburritoespañolburrito')
        self.assertEqual(m5, 'españolburritoespañolburrito')

        # change language
        m1 = translation.gettext_lazy('test')
        self.assertEqual(m1, 'Español')
        translation.set_language(('en_US',))
        self.assertEqual(m1, 'test')

    def test_lazy_domain(self):
        # Create lazy before domain is installed.
        m = translation.gettext_lazy('test')
        self.assertEqual(str(m), 'test')
        translation.add_domain('foo', self._localedir('locale1'))
        self.assertEqual(str(m), 'test')
        translation.set_language(('es',))
        self.assertEqual(str(m), 'Español')

    def test_domain(self):
        # Note, set_as_global is True, so second overrides first.
        translation.add_domain('foo', self._localedir('locale1'))
        translation.add_domain('bar', self._localedir('locale1'))
        translation.set_language(('en_US',))

        self.assertEqual(translation.gettext('bar'), 'blah')
        self.assertEqual(translation.gettext('test'), 'test')
        self.assertEqual(translation.gettext('test2'), 'foo')

        # dgettext and ldgettext should be the same.
        for method in ('dgettext', 'ldgettext', 'dgettext_lazy', 'ldgettext_lazy'):
            m = getattr(translation, method)
            self.assertEqual(m('foo', 'bar'), 'bar')
            self.assertEqual(m('foo', 'test'), 'test')
            self.assertEqual(m('foo', 'test2'), 'test2')

            self.assertEqual(m('bar', 'bar'), 'blah')
            self.assertEqual(m('bar', 'test'), 'test')
            self.assertEqual(m('bar', 'test2'), 'foo')
        translation.set_language(('es',))
        for method in ('dgettext', 'ldgettext', 'dgettext_lazy', 'ldgettext_lazy'):
            m = getattr(translation, method)
            self.assertEqual(m('foo', 'bar'), 'bar')
            # Locale conversion won't work with US-ASCII
            if not method.startswith('ldgettext'):
                self.assertEqual(m('foo', 'test'), 'Español')
            self.assertEqual(m('foo', 'test2'), 'quesadilla')

            self.assertEqual(m('bar', 'bar'), 'bar')
            if not method.startswith('ldgettext'):
                self.assertEqual(m('bar', 'test'), 'Español-bar')
            self.assertEqual(m('bar', 'test2'), 'test2')

    def test_domain_get(self):
        translation.add_domain('foo', self._localedir('locale1'))
        translation.add_domain('bar', self._localedir('locale1'))
        translation.set_language(('es',))

        d_foo = translation.get_domain('foo')
        self.assertEqual(d_foo.gettext('test'), 'Español')
        d_bar = translation.get_domain('bar')
        self.assertEqual(d_bar.gettext('test'), 'Español-bar')

    def test_language(self):
        translation.add_domain('foo', self._localedir('locale1'))
        # Test environment variable as default.
        os.environ['LANG'] = 'de'
        try:
            self.assertEqual(translation.gettext('test4'), 'freundleben')
        finally:
            del os.environ['LANG']

        # Test 'C'.
        translation.set_language(('C',))
        self.assertEqual(translation.gettext('test4'), 'test4')

        # Test lang method.
        def lang():
            return ('fr', 'es')
        translation.set_language(lang)
        self.assertEqual(translation.gettext('test4'), 'paella')


    def test_catalog_update(self):
        translation.add_domain('foo', self._localedir('locale1'))
        translation.set_language(('en',))
        self.assertEqual(translation.gettext('test'), 'test')
        self.assertEqual(translation.gettext('test4'), 'oddball')

        translation.add_domain('foo', self._localedir('locale2'))
        self.assertEqual(translation.gettext('test'), 'test')
        self.assertEqual(translation.gettext('test1'), 'test1')
        self.assertEqual(translation.gettext('test2'), '2-test2')
        self.assertEqual(translation.gettext('test3'), 'test3')
        self.assertEqual(translation.gettext('asdf1'), '2-asdf1')
        self.assertEqual(translation.gettext('asdf2'), '2-asdf2')
        self.assertEqual(translation.gettext('test4'), 'oddball')
        self.assertEqual(translation.gettext('test5'), 'test5')

        translation.reset()
        translation.add_domain('foo', self._localedir('locale2'))
        translation.set_language(('en',))
        self.assertEqual(translation.gettext('test'), '2-test')
        self.assertEqual(translation.gettext('test1'), '2-test1')
        self.assertEqual(translation.gettext('test2'), '2-test2')
        self.assertEqual(translation.gettext('test3'), '2-test3')
        self.assertEqual(translation.gettext('asdf1'), '2-asdf1')
        self.assertEqual(translation.gettext('asdf2'), '2-asdf2')
        self.assertEqual(translation.gettext('test4'), 'test4')
        self.assertEqual(translation.gettext('test5'), 'test5')

        translation.add_domain('foo', self._localedir('locale1'))
        self.assertEqual(translation.gettext('test'), '2-test')
        self.assertEqual(translation.gettext('test1'), '2-test1')
        self.assertEqual(translation.gettext('test2'), '2-test2')
        self.assertEqual(translation.gettext('test3'), '2-test3')
        self.assertEqual(translation.gettext('asdf1'), '2-asdf1')
        self.assertEqual(translation.gettext('asdf2'), '2-asdf2')
        self.assertEqual(translation.gettext('test4'), 'oddball')
        self.assertEqual(translation.gettext('test5'), 'test5')

        # Make something that updates.
        translation.reset()
        translation.set_language(('en',))
        path = os.path.join(os.getcwd(), 'translation', 'locale-dynamic', 'en_US', 'LC_MESSAGES')
        target = os.path.join(path, 'foo.mo')
        if os.path.exists(target):
            os.unlink(target)
        os.symlink(os.path.join(path, 'foo1.mo'), target)
        translation.add_domain('foo', self._localedir('locale-dynamic'))
        self.assertEqual(translation.gettext('test'), 'test-dyn1')
        os.unlink(target)
        os.symlink(os.path.join(path, 'foo2.mo'), target)
        translation.add_domain('foo', self._localedir('locale-dynamic'))
        self.assertEqual(translation.gettext('test'), 'test-dyn2')

    def test_refresh(self):
        for check_timestamps in (True, False):
            translation.reset()
            lazy = translation.gettext_lazy('test')
            self.assertEqual(str(lazy), 'test')
            self.assertEqual(translation.gettext('test'), 'test')

            translation.set_language(('en',))
            path = os.path.join(os.getcwd(), 'translation', 'locale-dynamic', 'en_US', 'LC_MESSAGES')
            target = os.path.join(path, 'foo.mo')
            if os.path.exists(target):
                os.unlink(target)

            shutil.copyfile(os.path.join(path, 'foo1.mo'), target)
            # Make sure timestamps are different.
            t = time.time()
            os.utime(target, (t-120, t-120))
            translation.add_domain('foo', self._localedir('locale-dynamic'))

            self.assertEqual(str(lazy), 'test-dyn1')
            self.assertEqual(translation.gettext('test'), 'test-dyn1')

            os.unlink(target)
            # Make sure timestamps are different.
            shutil.copyfile(os.path.join(path, 'foo2.mo'), target)
            os.utime(target, (t-60, t-60))
            translation.get_domain('foo').refresh(check_timestamps)
            self.assertEqual(str(lazy), 'test-dyn2')
            self.assertEqual(translation.gettext('test'), 'test-dyn2')

            os.unlink(target)
            # Make sure timestamps are different.
            shutil.copyfile(os.path.join(path, 'foo1.mo'), target)
            os.utime(target, (t-30, t-30))
            translation.get_domain('foo').refresh(check_timestamps)
            self.assertEqual(str(lazy), 'test-dyn1')
            self.assertEqual(translation.gettext('test'), 'test-dyn1')

    def test_plural(self):
        # Note, set_as_global is True, so second overrides first.
        translation.add_domain('foo', self._localedir('locale1'))
        translation.add_domain('plural', self._localedir('locale1'))
        translation.set_language(('en_US',))

        for method in ('dngettext', 'ldngettext'):
            m = getattr(translation, method)
            self.assertEqual(m('plural', 'a', 'as', 0), 'as')
            self.assertEqual(m('plural', 'a', 'as', 1), 'a')
            self.assertEqual(m('plural', 'a', 'as', 2), 'as')

            self.assertEqual(m('foo', 'a', 'as', 0), 'as')
            self.assertEqual(m('foo', 'a', 'as', 1), 'a')
            self.assertEqual(m('foo', 'a', 'as', 2), 'as')

        for method in ('ngettext', 'lngettext'):
            m = getattr(translation, method)
            self.assertEqual(m('a', 'as', 0), 'as')
            self.assertEqual(m('a', 'as', 1), 'a')
            self.assertEqual(m('a', 'as', 2), 'as')

        self.assertEqual(translation.ungettext('a', 'as', 0), u'as')
        self.assertEqual(translation.ungettext('a', 'as', 1), u'a')
        self.assertEqual(translation.ungettext('a', 'as', 2), u'as')

        translation.set_language(('sl',))
        for method in ('dngettext', 'ldngettext'):
            m = getattr(translation, method)
            self.assertEqual(m('plural', 'a', 'as', 0), 'a3')
            self.assertEqual(m('plural', 'a', 'as', 1), 'a0')
            self.assertEqual(m('plural', 'a', 'as', 2), 'a1')
            self.assertEqual(m('plural', 'a', 'as', 3), 'a2')
            self.assertEqual(m('plural', 'a', 'as', 4), 'a2')
            self.assertEqual(m('plural', 'a', 'as', 5), 'a3')

            self.assertEqual(m('foo', 'a', 'as', 0), 'as')
            self.assertEqual(m('foo', 'a', 'as', 1), 'a')
            self.assertEqual(m('foo', 'a', 'as', 2), 'as')

        for method in ('ngettext', 'lngettext'):
            m = getattr(translation, method)
            self.assertEqual(m('a', 'as', 0), 'a3')
            self.assertEqual(m('a', 'as', 1), 'a0')
            self.assertEqual(m('a', 'as', 2), 'a1')
            self.assertEqual(m('a', 'as', 3), 'a2')
            self.assertEqual(m('a', 'as', 4), 'a2')
            self.assertEqual(m('a', 'as', 5), 'a3')

        self.assertEqual(translation.ungettext('a', 'as', 0), u'a3')
        self.assertEqual(translation.ungettext('a', 'as', 1), u'a0')
        self.assertEqual(translation.ungettext('a', 'as', 2), u'a1')
        self.assertEqual(translation.ungettext('a', 'as', 3), u'a2')
        self.assertEqual(translation.ungettext('a', 'as', 4), u'a2')
        self.assertEqual(translation.ungettext('a', 'as', 5), u'a3')

    def test_normalization(self):
        translation.add_domain('foo', self._localedir('locale1'))
        translation.set_language(('en',))
        self.assertEqual(translation.gettext('test4'), 'oddball')
        translation.set_language(('es_ES',))
        self.assertEqual(translation.gettext('test4'), 'paella')
        translation.set_language(('en_GB',))
        self.assertEqual(translation.gettext('test4'), 'test4')
        translation.set_language(('en_GB', 'en'))
        self.assertEqual(translation.gettext('test4'), 'oddball')
        translation.set_language(('es_ES.UTF-8',))
        self.assertEqual(translation.gettext('test4'), 'paella')
        translation.set_language(('de_DE@euro',))
        self.assertEqual(translation.gettext('test4'), 'freundleben')

# I removed the set_language_charset function because it didn't make sense.
# Leaving this here until we figure out how to set default character sets.
#
#    def test_charset(self):
#        translation.add_domain('foo', self._localedir('locale1'))
#        translation.set_language(('en',))
#        translation.set_language_charset('en', 'utf-8')
#        self.assertEqual(translation.gettext('test'), 'test')
#        translation.set_language(('es',))
#        self.assertEqual(translation.gettext('test'), 'Español')
#        translation.set_language_charset('es', 'utf-8')
#        self.assertEqual(translation.gettext('test'), 'Español')
#        translation.set_language_charset('es', 'utf-16')
#        self.assertEqual(translation.gettext('test'), '\xff\xfeE\x00s\x00p\x00a\x00\xf1\x00o\x00l\x00')
#
#        # Test changing midway with lazy.
#        translation.reset()
#        translation.add_domain('foo', self._localedir('locale1'))
#        translation.set_language(('es',))
#        t = translation.gettext_lazy('test')
#        self.assertEqual(t, 'Español')
#        self.assertEqual(str(t), 'Español')
#        self.assertRaises(UnicodeDecodeError, lambda: unicode(t))
#        translation.set_language_charset('es', 'US-ASCII')
#        self.assertRaises(UnicodeEncodeError, lambda: str(t))
#        self.assertRaises(UnicodeEncodeError, lambda: unicode(t))
#        translation.set_language_charset('es', 'utf-8')
#        self.assertEqual(str(t), 'Español')
#
    def test_thread_local(self):
        translation.add_domain('foo', self._localedir('locale1'))
        self.assertEqual(translation.gettext('test'), 'test')
        self.assertEqual(translation.gettext('test4'), 'test4')
        translation.set_language(('es',))
        self.assertEqual(translation.gettext('test'), 'Español')
        self.assertEqual(translation.gettext('test4'), 'paella')
        translation.set_language_current_thread(('de',))
        self.assertEqual(translation.gettext('test'), 'groß')
        self.assertEqual(translation.gettext('test4'), 'freundleben')

        translation.reset()
        translation.add_domain('foo', self._localedir('locale1'))
        self.assertEqual(translation.gettext('test'), 'test')
        self.assertEqual(translation.gettext('test4'), 'test4')
        t = translation.gettext_lazy('test')
        self.assertEqual(t, 'test')
        current = [('es',)]
        def lang():
            return current[0]
        translation.set_language_current_thread(lang)
        self.assertEqual(t, 'Español')
        self.assertEqual(translation.gettext('test'), 'Español')
        self.assertEqual(translation.gettext('test4'), 'paella')
        current[0] = ('de',)
        self.assertEqual(t, 'groß')
        self.assertEqual(translation.gettext('test'), 'groß')
        self.assertEqual(translation.gettext('test4'), 'freundleben')

    def test_radd(self):
        # Strings do not have radd, so it needs to be handled specially.
        translation.add_domain('foo', self._localedir('locale1'))
        translation.set_language(('es',))
        self.assertEqual('- ' + translation.gettext_lazy('test'), '- Español')
        self.assertEqual(translation.gettext_lazy('test') + 'asdf', 'Españolasdf')

if __name__ == '__main__':
    unittest.main()
