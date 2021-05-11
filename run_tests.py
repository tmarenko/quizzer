import os
import sys
import subprocess

sys.path.append(os.path.dirname(__file__))
os.environ['FLASK_APP'] = 'quizzer'
os.environ['FLASK_ENV'] = 'development'
with open("pytest.log", "w") as log_file:
    subprocess.call(['coverage', 'run', '-m', 'pytest'])
    subprocess.call(['coverage', 'html'])
