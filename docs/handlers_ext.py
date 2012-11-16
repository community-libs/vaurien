import os

from vaurien.behaviors import get_behaviors


_HEADER = """\

.. _behaviors:

Handlers
========

Vaurien provides a collections of behaviors.

"""


def generate_behaviors(app):
    path = os.path.join(app.srcdir, 'behaviors')
    ext = app.config['source_suffix']
    filename = os.path.join(app.srcdir, "behaviors%s" % ext)
    items = get_behaviors().items()
    items.sort()

    with open(filename, "w") as doc:
        doc.write(_HEADER)

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


def setup(app):
    app.connect('builder-inited', generate_behaviors)
