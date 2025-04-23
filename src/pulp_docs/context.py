from contextvars import ContextVar


ctx_draft = ContextVar("ctx_draft", default=False)
