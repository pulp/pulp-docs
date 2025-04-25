from contextvars import ContextVar


ctx_blog = ContextVar("ctx_blog", default=True)
ctx_draft = ContextVar("ctx_draft", default=False)
