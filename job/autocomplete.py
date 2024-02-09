import os
import argparse
import readline

JOB_PROJECT_DIR = '/Users/rafalszulinski/Desktop/developing'  # replace with your actual path
readline.parse_and_bind('tab: complete')
def _jobProjectDir(path):
    return os.listdir(path)

def _job_complete(text, state):
   
    COMP_WORDS = readline.get_line_buffer().split()
    COMP_CWORD = len(COMP_WORDS) - 1
    cur = COMP_WORDS[COMP_CWORD]
    prev = COMP_WORDS[COMP_CWORD - 1] if COMP_CWORD > 0 else ''

    if COMP_WORDS[1] == '-m':
        if COMP_CWORD == 5:
            if COMP_WORDS[3] == '-move':
                assetname = sorted(os.listdir(f"{JOB_PROJECT_DIR}/{COMP_WORDS[2]}"))[0]
                path = f"{JOB_PROJECT_DIR}/{COMP_WORDS[2]}/{assetname}"
                return _jobProjectDir(path)[state]
            elif COMP_WORDS[3] == '-permissions':
                return ['g+r', 'g-r', 'g+w', 'g-w', 'g+x', 'g-x'][state]
            elif COMP_WORDS[3] == '-userDirs':
                if COMP_WORDS[4] == '-add':
                    assetname = sorted(os.listdir(f"{JOB_PROJECT_DIR}/{COMP_WORDS[2]}"))[0]
                    path = f"{JOB_PROJECT_DIR}/{COMP_WORDS[2]}/{assetname}"
                    return _jobProjectDir(path)[state]
    elif COMP_WORDS[1] in ['-s', '-c']:
        if COMP_CWORD == 2:
            path = JOB_PROJECT_DIR
            if os.path.isdir(path):
                return [f for f in os.listdir(path) if 'schema' not in f][state]
        elif COMP_CWORD == 3:
            path = f"{JOB_PROJECT_DIR}/{COMP_WORDS[COMP_CWORD-1]}"
            if os.path.isdir(path):
                return [f for f in os.listdir(path) if 'template' not in f][state]

    if COMP_CWORD == 1:
        return ['-s', '-c', '-m'][state]

readline.set_completer(_job_complete)

parser = argparse.ArgumentParser()
parser.add_argument('-s', help='s argument')
parser.add_argument('-c', help='c argument')
parser.add_argument('-m', help='m argument')
args = parser.parse_args()

print(args)