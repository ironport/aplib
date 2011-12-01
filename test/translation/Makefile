# $Header: //prod/main/ap/aplib/test/translation/Makefile#1 $

# For some reason msgmerge messes up the SHIFT-JIS character set.
# Just handle that one manually.
msgmerge:
	(for po in */*/LC_MESSAGES/*.po ; \
	 do \
	 	if [ $$po != "locale1/ja_JP.SJIS/LC_MESSAGES/foo.po" ] ; \
	 	then \
			domain=`basename -s .po "$$po"` ; \
                        POTDIR=$${po%%/*} ; \
			msgmerge -U "$$po" $$POTDIR/$$domain.pot ; \
		fi ; \
	 done)


msgfmt:
	(for po in */*/LC_MESSAGES/*.po ; \
	 do \
		base=$${po%.*} ;\
		output_filename=$${base}.mo ;\
		msgfmt $$po -o $$output_filename ; \
	 done)
