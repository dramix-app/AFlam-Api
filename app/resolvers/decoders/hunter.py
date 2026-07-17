"""
Hunter decoder - unpacks Hunter-coded JavaScript (used by SuperEmbed, FlixHQ, etc.)
"""
import re
from typing import List, Tuple


async def hunter(
    h: str, u: str, n: str, t: str, e: int, r: int
) -> str:
    """
    Unpack Hunter-coded JavaScript.
    Parameters are extracted from eval(function(h,u,n,t,e,r)...)(...)
    """
    n = int(n)
    e = int(e)
    t = int(t)

    result = ''
    i = 0
    while i < n:
        k = _radix(h[i]) if _isdigit(h[i]) else 0
        result += _get_value_from_table(k, u, t, e)
        i += 1

    return result


async def process_hunter_args(args_str: str) -> Tuple[str, str, int, int, int, int]:
    """Parse the hunter arguments string into proper types."""
    parts = args_str.split(',')
    if len(parts) == 6:
        return (parts[0], parts[1], int(parts[2]), int(parts[3]), int(parts[4]), int(parts[5]))
    # Try to handle differently formatted args
    return tuple(parts[:6])


def _radix(c: str) -> int:
    """Get the radix value for a character."""
    if c.isdigit():
        return int(c)
    return 0


def _isdigit(c: str) -> bool:
    return c.isdigit()


def _get_value_from_table(k: int, u: str, t: int, e: int) -> str:
    """Look up the value in the hunter table."""
    if k < t:
        return u[k]
    return ''


async def unpack_packed(packed_js: str) -> str:
    """
    Unpack standard JS Packer code: eval(function(p,a,c,k,e,d){...})
    """
    # Extract the arguments from eval(function(p,a,c,k,e,d){...}(...))
    match = re.search(r"eval\(function\(p,a,c,k,e,d\)\{(.*?)\}\((.*?)\)\)", packed_js, re.DOTALL)
    if not match:
        return packed_js

    try:
        args = match.group(2).split(',')
        p = args[0].strip("'\"")
        a = int(args[1])
        c = int(args[2])
        k = args[3].strip("'\"").split('|')
        e = int(args[4])
        d = int(args[5])

        # Decode
        result = []
        while c > 1:
            c -= 1
            if e > 1:
                idx = _base36(c, e) if c >= e else str(c)
            else:
                idx = str(c)
            if idx in d:
                result.append(d[idx])
            else:
                result.append(k[c] if c < len(k) else idx)
        return ''.join(result)
    except Exception:
        return packed_js


def _base36(n: int, base: int) -> str:
    """Convert number to base-36 string."""
    if n == 0:
        return '0'
    digits = []
    while n > 0:
        digits.append(str(n % base))
        n //= base
    return ''.join(reversed(digits))
