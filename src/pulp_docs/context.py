from contextvars import ContextVar

ctx_blog = ContextVar("ctx_blog", default=True)
ctx_docstrings = ContextVar("ctx_docstrings", default=True)
ctx_draft = ContextVar("ctx_draft", default=False)
ctx_path = ContextVar("ctx_path", default=None)
ctx_dryrun = ContextVar("ctx_dryrun", default=False)
