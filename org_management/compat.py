"""Runtime compatibility shims for interpreter/dependency version mismatches.

Each shim feature-detects the breakage it repairs and is a no-op when the
running combination of Python and Django does not need it, so nothing here has
to be removed when the environment is upgraded.
"""
import copy


def patch_template_context_copy():
    """Repair ``BaseContext.__copy__`` on Python 3.13+ with Django 4.2.

    ``django/template/context.py`` copies a context with::

        duplicate = copy(super())
        duplicate.dicts = self.dicts[:]

    Through Python 3.12 ``copy.copy()`` on a ``super`` object went through
    ``__reduce_ex__`` and returned a fresh instance of the underlying class.
    Python 3.13+ returns the ``super`` proxy itself, which has no ``__dict__``,
    so the assignment raises::

        AttributeError: 'super' object has no attribute 'dicts'
                        and no __dict__ for setting new attributes

    That breaks every template that pushes a new context scope -- the Django
    admin, ``{% include %}``, inclusion tags -- and the whole test suite.
    Django 4.2 is only supported on Python 3.8-3.12 and will not be patched
    upstream, so restore the pre-3.13 semantics: a new instance of the concrete
    class carrying a shallow copy of the original's ``__dict__``.
    """
    from django.template.context import BaseContext

    try:
        copy.copy(BaseContext())
    except AttributeError:
        pass  # Broken interpreter/Django combination -- patch it below.
    else:
        return  # Already works; leave Django alone.

    def __copy__(self):
        duplicate = BaseContext.__new__(type(self))
        duplicate.__dict__.update(self.__dict__)
        duplicate.dicts = self.dicts[:]
        return duplicate

    BaseContext.__copy__ = __copy__
