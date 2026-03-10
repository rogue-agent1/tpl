#!/usr/bin/env python3
"""tpl - Tiny template engine for text files.

One file. Zero deps. Fill templates fast.

Usage:
  tpl.py render template.txt name=World count=5
  tpl.py render template.txt --json vars.json
  echo "Hello {{name}}" | tpl.py render - name=World
  tpl.py check template.txt              → list variables
  tpl.py envsubst template.txt           → substitute from env vars
"""

import argparse
import json
import os
import re
import sys


PATTERN = re.compile(r'\{\{(\w+)(?:\|([^}]*))?\}\}')  # {{var}} or {{var|default}}


def find_vars(text: str) -> list[dict]:
    found = []
    seen = set()
    for m in PATTERN.finditer(text):
        name = m.group(1)
        default = m.group(2)
        if name not in seen:
            seen.add(name)
            found.append({"name": name, "default": default})
    return found


def render(text: str, variables: dict) -> str:
    def replacer(m):
        name = m.group(1)
        default = m.group(2)
        if name in variables:
            val = variables[name]
            return str(val)
        if default is not None:
            return default
        return m.group(0)  # leave as-is if no value and no default
    return PATTERN.sub(replacer, text)


def parse_vars(pairs: list[str]) -> dict:
    result = {}
    for pair in pairs:
        if "=" in pair:
            k, v = pair.split("=", 1)
            # Smart type coercion
            if v.lower() == "true":
                result[k] = True
            elif v.lower() == "false":
                result[k] = False
            elif v.isdigit():
                result[k] = int(v)
            else:
                try:
                    result[k] = float(v)
                except ValueError:
                    result[k] = v
    return result


def read_template(path: str) -> str:
    if path == "-":
        return sys.stdin.read()
    with open(path) as f:
        return f.read()


def cmd_render(args):
    text = read_template(args.template)
    variables = {}
    if args.json_file:
        with open(args.json_file) as f:
            variables = json.load(f)
    if args.vars:
        variables.update(parse_vars(args.vars))
    result = render(text, variables)
    if args.output:
        with open(args.output, "w") as f:
            f.write(result)
    else:
        print(result, end="")


def cmd_check(args):
    text = read_template(args.template)
    variables = find_vars(text)
    if not variables:
        print("No template variables found")
        return
    for v in variables:
        default = f' (default: "{v["default"]}")' if v["default"] is not None else " (required)"
        print(f"  {v['name']}{default}")


def cmd_envsubst(args):
    text = read_template(args.template)
    result = render(text, dict(os.environ))
    print(result, end="")


def main():
    p = argparse.ArgumentParser(description="Tiny template engine")
    sub = p.add_subparsers(dest="cmd")

    s = sub.add_parser("render")
    s.add_argument("template")
    s.add_argument("vars", nargs="*", help="key=value pairs")
    s.add_argument("--json", dest="json_file", help="JSON file with variables")
    s.add_argument("-o", "--output", help="Output file")
    s.set_defaults(func=cmd_render)

    s = sub.add_parser("check")
    s.add_argument("template")
    s.set_defaults(func=cmd_check)

    s = sub.add_parser("envsubst")
    s.add_argument("template")
    s.set_defaults(func=cmd_envsubst)

    args = p.parse_args()
    if not args.cmd:
        p.print_help()
        return 1
    return args.func(args) or 0


if __name__ == "__main__":
    sys.exit(main())
