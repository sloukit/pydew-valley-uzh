local:
	python main.py

clean:
	rm -rf build
	rm -rf .tox

web-debug: clean
	# pygbag --ume_block=0 ./main.py
	pygbag --PYBUILD 3.12 ./main.py

web: clean
	pygbag --ume_block=0 --template default.tmpl --git --PYBUILD 3.12 ./main.py

git: clean
	pygbag --git ./main.py

package: clean
	pygbag --build --ume_block=0 --template default.tmpl --git --PYBUILD 3.12 ./main.py

run-server:
	cd pydew_valley/build/web && python -m http.server