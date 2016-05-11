#!/usr/bin/env python
import base64
import logging
import uuid
import tornado.httpserver
from tornado.options import define, options
import tornado.web
from service.handlers.handlers import InfoHandler, ExecutorHandler, ErrorHandler

logger = logging.getLogger("palnot.server")

define('config', default='server.conf', help='full path to the configuration file')
define('debug', default=False, help='debug True False')
define('port', default='8080', help='port to start server on', group='application')

urls = [
    (r'/api/info', InfoHandler),
    (r'/api/v1/executor', ExecutorHandler)
]


def setup_application(app_options):
    settings = {
        'cookie_secret': base64.b64encode(uuid.uuid4().bytes + uuid.uuid4().bytes),
    }

    settings.update(app_options)

    application = tornado.web.Application(urls, **settings)
    tornado.web.ErrorHandler = ErrorHandler

    return application


def main():
    tornado.options.parse_command_line()

    if options.config:
        config_to_read = options.config
    else:
        config_to_read = './server.conf'

    tornado.options.parse_config_file(config_to_read)

    if options.debug:
        logging.getLogger("palnot.server").setLevel(logging.DEBUG)

    http_server = tornado.httpserver.HTTPServer(setup_application(options.group_dict('application')))
    http_server.listen(options.port)

    tornado.ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    main()
