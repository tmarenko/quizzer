import os
import subprocess

os.environ['FLASK_APP'] = 'quizzer'
os.environ['FLASK_ENV'] = 'development'
if not os.path.exists("instance/quizzer.sqlite"):
    subprocess.call(['flask', 'init-db'])
subprocess.call(['flask', 'run', '--host=0.0.0.0'])
