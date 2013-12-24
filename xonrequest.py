#!/usr/bin/env python

import subprocess as subp
import json

from flask import Flask, request, Response, stream_with_context


def main(argv):
    config_rules = json.load(open(argv[1]))
    x = Xor()
    x.add_rules(config_rules)
    x.app.run(host='0.0.0.0', debug=True)
    #x.app.run(host='0.0.0.0', debug=False)


def read_generator(fd, b):
    return iter(lambda: fd.read(b), '')


def order_args_as_route(route, kwargs):
    def is_var(s):
        return s.startswith('<') and s.endswith('>')
    def get_value_from_var(s):
        s2 = s[1:-1]
        res = ''
        if ':' in s2:
            split = s2.split(':')
            if len(split) == 2:
                if split[0] in ['int', 'float']:
                    res = str(kwargs[split[1]])
                else:
                    res = kwargs[split[1]]
            else:
                res = ''
        else:
            res = kwargs[s2]
        return res
    vs = filter(is_var, route.split('/'))
    return map(get_value_from_var, vs)

def order_args(order, args):
    arg_list = []
    for o in order + ['query', 'path', 'post']:
        if o in args:
            arg_list.extend(args[o])
            del args[o]
    return arg_list

# Function factory, hack because of late binding.
def make_f(r):
    def f(**kwargs):
        args = {}
        #TODO Do some decoding (and test with encoded data)
        args['path'] = order_args_as_route(r['route'], kwargs)
        if len(request.query_string) > 0:
            args['query'] = request.query_string.split('&')
        if request.method == 'POST':
            content_fd = request.environ['wsgi.input']
            args['post'] = content_fd.read(request.content_length).split('&')
        arg_list = order_args(r.get('order', ['query', 'path', 'post']), args)
        print arg_list
        cmd = ['bash', r['script']] + arg_list
        if 'user' in r:
            running_user = subp.check_output(['whoami']).strip()
            if r['user'] != running_user and running_user == 'root':
                cmd = ['sudo', '-u', r['user']] + cmd
            elif r['user'] != running_user:
                raise Exception('Permission denied')
        if r.get('output'):
            p = subp.Popen(cmd, stdout=subp.PIPE, stderr=subp.STDOUT,
                           bufsize=2)
            return Response(stream_with_context(read_generator(p.stdout, 1)))
        else:
            return str(subp.call(cmd))
    return f


class Xor(object):
    def __init__(self):
        self.app = Flask(__name__)

    def add_rules(self, cfg):
        for rule in cfg:
            if 'route' not in rule:
                continue
            if 'script' in rule:
                endpoint = 'f%s' % str(hash(rule['route']))
                self.app.add_url_rule(rule['route'], endpoint, make_f(rule),
                                      methods=rule.get('methods'),
                                      defaults=rule.get('defaults'))

if __name__ == '__main__':
    import sys
    main(sys.argv)