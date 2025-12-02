import re
import string


def normalize_str(string_in: str) -> str:
    # remove punctuation
    punctuation = re.compile(f"[{string.punctuation}]")
    string_in = re.sub(punctuation, " ", string_in)

    # normalize whitespace
    whitespace = re.compile(f"[{string.whitespace}]+")
    string_in = re.sub(whitespace, " ", string_in)

    # remove leading and trailing whitespace
    return string_in.strip(string.whitespace)


def str_compare(s1: str, s2: str, ignore_case: bool = True) -> bool:
    s1 = normalize_str(s1)
    s2 = normalize_str(s2)
    if ignore_case:
        s1 = s1.lower()
        s2 = s2.lower()
    return s1 == s2
