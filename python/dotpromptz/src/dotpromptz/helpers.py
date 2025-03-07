import json
from typing import Any, Dict

from handlebars import Handlebars

# Initialize Handlebars instance
hbs = Handlebars


# Define helper functions
def json_helper(context, options=None):
    """Convert context to JSON string safely."""
    if hasattr(context, "to_dict"):
        context = context.to_dict()

    # Fix: Check if options exists and handle PyJs objects properly
    if options:
        if hasattr(options, 'to_python'):
            options = options.to_python()
        indent = options.get("indent") if isinstance(options, dict) else 0
    else:
        indent = 0

    return json.dumps(context, indent=indent)


# def json_helper(context, options=None):
#     # Convert PyJsObject to Python native type before serializing
#     if hasattr(context, 'to_python'):
#         context = context.to_python()
#     indent = options.get("indent", 0) if isinstance(options, dict) else 0
#     return json.dumps(context, indent=indent)


def role_helper(role):
    # Remove quotes and convert to string if needed
    if hasattr(role, 'to_python'):
        role = role.to_python()
    return f"<<role:{role}>>"


def history_helper(action=None):
    return f"<<history>>"


def section_helper(name):
    # Remove quotes and convert to string if needed
    if hasattr(name, 'to_python'):
        name = name.to_python()
    return f"<<section:{name}>>"


def media_helper(media_type, media_url):
    # Remove quotes and convert to string if needed
    if hasattr(media_type, 'to_python'):
        media_type = media_type.to_python()
    if hasattr(media_url, 'to_python'):
        media_url = media_url.to_python()
    return f"<<media:{media_url} {media_type}>>"


def if_equals_helper(arg1, arg2, options):
    """Handlebars ifEquals helper"""
    # Convert PyJsObject to Python native type if needed
    if hasattr(arg1, 'to_python'):
        arg1 = arg1.to_python()
    if hasattr(arg2, 'to_python'):
        arg2 = arg2.to_python()

    if arg1 == arg2:
        return options["fn"](options["data"])
    return options["inverse"](options["data"])


def unless_equals_helper(arg1, arg2, options):
    """Handlebars unlessEquals helper"""
    # Convert PyJsObject to Python native type if needed
    if hasattr(arg1, 'to_python'):
        arg1 = arg1.to_python()
    if hasattr(arg2, 'to_python'):
        arg2 = arg2.to_python()

    if arg1 != arg2:
        return options["fn"](options["data"])
    return options["inverse"](options["data"])


# Register helpers
Handlebars.helpers["json"] = json_helper
Handlebars.helpers["role"] = role_helper
Handlebars.helpers["history"] = history_helper
Handlebars.helpers["section"] = section_helper
Handlebars.helpers["media"] = media_helper
Handlebars.helpers["ifEquals"] = if_equals_helper
Handlebars.helpers["unlessEquals"] = unless_equals_helper


# Render function
def render(template_str, context):
    """Compile and render a Handlebars template with the provided context."""
    template = Handlebars.compile(template_str)
    result = template(context)
    # Unescape HTML entities if needed
    if hasattr(result, 'replace'):
        result = result.replace('&lt;', '<').replace('&gt;', '>').replace(
            '&#x27;', "'")
    return result
