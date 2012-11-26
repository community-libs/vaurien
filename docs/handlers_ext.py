import os

from vaurien.behaviors import get_behaviors
from vaurien.protocols import get_protocols


_BEHAVIOR = """\

.. _behaviors:

Behaviors
=========

Vaurien provides a collections of behaviors, all of them are listed on this
page.  You can also write your own behaviors if you need. Have a look at
:ref:`extending` to learn more.

"""


_PROTO = """\

.. _protocols:

Protocols
=========

Vaurien provides a collections of protocols, which are all listed on this page.
You can also write your own protocols if you need. Have a look at
:ref:`extending` to learn more.

"""


def generate_behaviors(app):
    return generate_plugins_doc(app, 'behaviors', get_behaviors().items(),
                                _BEHAVIOR)


def generate_protocols(app):
    return generate_plugins_doc(app, 'protocols', get_protocols().items(),
                                _PROTO)


def generate_plugins_doc(app, name, items, tmpl):
    ext = app.config['source_suffix']
    filename = os.path.join(app.srcdir, "%s%s" % (name, ext))
    items.sort()
    tmpl = ('.. do not edit: this file is generated automatically'.upper()
            + tmpl + '\n\n')

    with open(filename, "w") as doc:
        doc.write(tmpl)

        for name, klass in items:
            doc.write(name + '\n')
            doc.write('-' * len(name) + '\n\n')

            if klass.__doc__ is not None:
                text = klass.__doc__.replace('\n    ', '\n')
                doc.write(text + '\n')
            else:
                doc.write('No documentation. Boooo!\n\n')

            if len(klass.options) == 0:
                continue

            doc.write('\nOptions:\n\n')
            options = klass.options.items()
            options.sort()

            for name, option in options:
                if len(option) == 3:
                    desc, type_, default = option
                    desc = '%s (%s, default: %r)' % (desc, type_.__name__,
                                                     default)
                else:
                    desc, type_, default, choices = option
                    choices = ', '.join(['%r' % val for val in choices])
                    pattern = '%s (%s, default: %r, possible values: %s)'
                    desc = pattern % (desc, type_.__name__, default, choices)

                doc.write('- **%s**: %s\n' % (name, desc))
            doc.write("\n\n")
        doc.write("\n")


def generate_doc(app):
    generate_behaviors(app)
    generate_protocols(app)


def setup(app):
    app.connect('builder-inited', generate_doc)
