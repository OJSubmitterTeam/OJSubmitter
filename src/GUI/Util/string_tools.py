import re


def to_html(msg: str) -> str:
    s = msg.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = re.sub(r" (?= )", "&nbsp;", s)
    s = s.replace("\t", "&nbsp;&nbsp;&nbsp;&nbsp;")
    s = s.replace("\n", "<br>")
    return s
