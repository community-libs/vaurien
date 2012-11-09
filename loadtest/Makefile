.PHONY: bench test report

build:
	virtualenv .
	bin/easy_install funkload
	bin/easy_install gevent
	bin/easy_install werkzeug

test:
	bin/fl-run-test loadtest.py

bench:
	bin/fl-run-bench loadtest.py VaurienTest.test_vaurien

report:
	bin/fl-build-report --html -o html simple-bench.xml
