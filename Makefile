test:
	podman run --rm -it -v `pwd`:/code:rw,Z python:3.11 bash -c 'cd /code && pip install tox && tox'
package:
	python -m build
clean:
	rm -rf build dist *.wheel
