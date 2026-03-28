import logging
import re


PII_EMAIL_RE = re.compile(r"([a-zA-Z0-9_.+-]+)@([a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)")
PII_PHONE_RE = re.compile(r"\b(\+?\d[\d -]{7,}\d)\b")


def mask_pii(message: str) -> str:
    message = PII_EMAIL_RE.sub("***@\\2", message)
    message = PII_PHONE_RE.sub("***PHONE***", message)
    return message


class PiiFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = mask_pii(record.msg)
        return True


def setup_logging() -> None:
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    if not any(isinstance(f, PiiFilter) for f in root.filters):
        root.addFilter(PiiFilter())
