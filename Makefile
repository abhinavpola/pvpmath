OPEN_BRAVE_MACOS = open -a "Brave Browser" -n --args --incognito --new-window http://127.0.0.1:5000/

run-local:
	python3 app.py

clean:
	rm -rf __pycache__
