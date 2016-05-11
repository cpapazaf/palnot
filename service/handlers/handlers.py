import tornado.httpserver
import tornado.web
from tornado.options import options
import logging
import os
import http
import resource
import traceback
from ..process_executor import execute

logger = logging.getLogger("palnot.server")


class BaseHandler(tornado.web.RequestHandler):

    @tornado.gen.coroutine
    def log_exception(self, exc_type, exc_value, exc_traceback):
        logger.warning("Exception %s" % exc_value)
        if (not isinstance(exc_value, tornado.web.HTTPError)) or (exc_value.status_code >= http.client.INTERNAL_SERVER_ERROR):
            stacktrace = ''.join(traceback.format_tb(exc_traceback))
            logger.error("Stacktrace %s" % stacktrace)

    @tornado.gen.coroutine
    def write_error(self, status_code, **kwargs):
        if status_code == 404:
            message = None
            if 'exc_info' in kwargs and\
                    kwargs['exc_info'][0] == tornado.web.HTTPError:
                    message = kwargs['exc_info'][1].log_message
            self.write(message)
        elif status_code == 500:
            error_trace = ""
            for line in traceback.format_exception(*kwargs['exc_info']):
                error_trace += line

            self.write('Server Error: ' + str(error_trace))
        else:
            message = None
            if 'exc_info' in kwargs and\
                    kwargs['exc_info'][0] == tornado.web.HTTPError:
                    message = kwargs['exc_info'][1].log_message
                    self.set_header('Content-Type', 'text/plain')
                    self.write(str(message))
            self.set_status(status_code)

    def set_default_headers(self):
        pass
#        self.set_header("Access-Control-Allow-Origin", "*")

    def prepare(self):
        self.payload = {}
        if len(self.request.body) == 0:
            return
        try:
            self.payload = tornado.escape.json_decode(self.request.body)
        except ValueError:
            logger.error('could not decode %r' % self.request.body)


class InfoHandler(BaseHandler):
    SUPPORTED_METHODS = ('GET',)

    def get(self):
        """Read server parameter

           :status 200: ok
        """
        data = options.as_dict()
        data.update({'rootpath': os.path.dirname(__file__),
                     'memory': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss})
        self.write(data)


class ExecutorHandler(BaseHandler):
    SUPPORTED_METHODS = ('POST',)

    @tornado.gen.coroutine
    def post(self):

        working_dir = self.payload['working_dir']
        command = self.payload['command']
        logger.debug("Received {command} on {working_dir}".format(command=command, working_dir=working_dir))
        [success, stdout, stderr] = yield execute(command, working_dir)
        result = {'success': success, 'stdout': stdout, 'stderr': stderr}

        self.write(tornado.escape.json_encode(result))

    
class ErrorHandler(BaseHandler):
    """Generates an error response with status_code for all requests."""
    def initialize(self, status_code):
        self._status_code = status_code

    def write_error(self, status_code, **kwargs):
        if status_code == http.client.NOT_FOUND:
            self.write('Oups! Are you lost ?')
        elif status_code == http.client.METHOD_NOT_ALLOWED:
            self.write('Oups! Method not allowed.')

    def prepare(self):
        raise tornado.web.HTTPError(self._status_code)
