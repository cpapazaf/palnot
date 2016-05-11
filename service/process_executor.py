import logging
import subprocess
import tornado
from tornado.gen import Return

logger = logging.getLogger("palnot.server")


@tornado.gen.coroutine
def execute(cmdArray, workingDir):

    stdout = ''
    stderr = ''

    try:
        try:
            process = subprocess.Popen(cmdArray, cwd=workingDir,
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=1)
        except OSError:
            raise Return([False, '', 'ERROR : command(' + ' '.join(cmdArray) + ') could not get executed!'])

        for line in iter(process.stdout.readline, b''):

            try:
                echoLine = line.decode("utf-8")
            except:
                echoLine = str(line)

            stdout += echoLine

        for line in iter(process.stderr.readline, b''):

            try:
                echoLine = line.decode("utf-8")
            except:
                echoLine = str(line)

            stderr += echoLine

    except (KeyboardInterrupt, SystemExit) as err:
        raise Return([False, '', str(err)])

    process.stdout.close()

    returnCode = process.wait()
    if returnCode != 0 or stderr != '':
        raise Return([False, stdout, stderr])
    else:
        raise Return([True, stdout, stderr])
