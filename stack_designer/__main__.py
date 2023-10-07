import argparse
from string import Template
import json
import os
import shutil


def validation(data: dict):
    ...

def build(args):
    with open(args.template) as f:
        template = f.read()
        
    with open(args.config) as f:
        config = f.read()
        validation(json.loads(config))
        
    t = Template(template)
    result = t.safe_substitute(placeholer=config)
    
    if os.path.exists(args.output):
        shutil.rmtree(args.output)
    
    os.makedirs(args.output)

    with open(os.path.join(args.output, "index.html"), "w") as f:
        f.write(result)

def serve(args):
    from http.server import SimpleHTTPRequestHandler, test, ThreadingHTTPServer
    from functools import partial
    import contextlib
    import socket
        
    handler_class = partial(SimpleHTTPRequestHandler,
                                directory=args.output)

    # ensure dual-stack is not disabled; ref #38907
    class DualStackServer(ThreadingHTTPServer):
        def server_bind(self):
            # suppress exception when protocol is IPv4
            with contextlib.suppress(Exception):
                self.socket.setsockopt(
                    socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
            return super().server_bind()

    build(args)
    test(
        HandlerClass=handler_class,
        ServerClass=DualStackServer,
        port=args.port,
        bind=args.bind,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    
    def add_common_args(cmd):
        template = os.path.join(os.path.abspath(os.path.dirname(__file__)), "default.html")
        
        cmd.add_argument('-c', '--config', type=str, required=True)
        cmd.add_argument('-t', '--template', type=str, default=template)
        cmd.add_argument('-o', '--output', type=str, default="public")
    
    cmd_build = subparsers.add_parser('build', help="")
    add_common_args(cmd_build)
    cmd_build.set_defaults(handler=build)

    cmd_serve = subparsers.add_parser('serve', help="")
    add_common_args(cmd_serve)
    cmd_serve.add_argument('-p', '--port', type=str, default=8000)
    cmd_serve.add_argument('-b', '--bind', type=str, default=None)
    cmd_serve.set_defaults(handler=serve)


    args = parser.parse_args()
    if hasattr(args, 'handler'):
        args.handler(args)
    else:
        # 未知のサブコマンドの場合はヘルプを表示
        parser.print_help()
    