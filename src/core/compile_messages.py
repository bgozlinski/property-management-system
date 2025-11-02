import os
import struct
import time
import ast
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Minimal pure-Python .po -> .mo compiler (subset of msgfmt)
# Based on Python's Tools/i18n/msgfmt.py algorithm

def _read_po(path: Path):
    messages = {}
    msgctxt = None
    msgid = None
    msgstr = None
    fuzzy = False

    def _add(msgctxt, msgid, msgstr):
        if fuzzy or msgid is None:
            return
        key = msgid if msgctxt is None else f"{msgctxt}\x04{msgid}"
        messages[key] = msgstr

    with path.open('r', encoding='utf-8') as fp:
        lines = fp.readlines()

    # State machine for simple/unpluralized entries
    def _normalize(s):
        s = s.strip()
        try:
            if s.startswith('"'):
                # Safely parse quoted PO string with escapes preserved correctly
                return ast.literal_eval(s)
            return s
        except Exception:
            # Fallback: best-effort strip quotes only
            if s.startswith('"') and s.endswith('"'):
                return s[1:-1]
            return s

    in_msgid_plural = False
    collecting = None
    buf = []

    for l in lines:
        l = l.rstrip('\n')
        if l.startswith('#,'):
            fuzzy = 'fuzzy' in l
            continue
        if l.startswith('#'):
            continue
        if l.startswith('msgctxt'):
            if msgid is not None and msgstr is not None:
                _add(msgctxt, msgid, msgstr)
                msgid = msgstr = None
            msgctxt = _normalize(l.split(' ', 1)[1])
            collecting = 'ctxt'
            continue
        if l.startswith('msgid_plural'):
            # We only support singular translations in this tiny compiler.
            in_msgid_plural = True
            collecting = None
            continue
        if l.startswith('msgid'):
            if msgid is not None and msgstr is not None:
                _add(msgctxt, msgid, msgstr)
                msgctxt = None
                msgstr = None
            msgid = _normalize(l.split(' ', 1)[1])
            fuzzy = False
            collecting = 'id'
            continue
        if l.startswith('msgstr'):
            # support only msgstr (singular)
            if l.startswith('msgstr['):
                # plural form - ignore in this minimal compiler
                collecting = None
                continue
            msgstr = _normalize(l.split(' ', 1)[1])
            collecting = 'str'
            continue
        if l.startswith('"'):
            if collecting == 'id' and msgid is not None:
                msgid += _normalize(l)
            elif collecting == 'str' and msgstr is not None:
                msgstr += _normalize(l)
            elif collecting == 'ctxt' and msgctxt is not None:
                msgctxt += _normalize(l)
            continue
        if l.strip() == '':
            # end of an entry
            if msgid is not None and msgstr is not None:
                _add(msgctxt, msgid, msgstr)
            msgctxt = None
            msgid = None
            msgstr = None
            fuzzy = False
            collecting = None
            in_msgid_plural = False
            continue

    # flush last
    if msgid is not None and msgstr is not None:
        _add(msgctxt, msgid, msgstr)

    return messages


def _write_mo(messages: dict, out_path: Path):
    # Build the binary mo file content
    ids = sorted(messages.keys())
    strs = [messages[id_] for id_ in ids]

    keystart = 7 * 4 + 16 * len(ids)
    valuestart = keystart + sum(len(i.encode('utf-8')) + 1 for i in ids)

    koffsets = []
    voffsets = []
    off = 0
    for id_ in ids:
        data = id_.encode('utf-8') + b'\0'
        koffsets.append((len(data) - 1, keystart + off))
        off += len(data)
    off = 0
    for s in strs:
        data = s.encode('utf-8') + b'\0'
        voffsets.append((len(data) - 1, valuestart + off))
        off += len(data)

    output = []
    # magic number
    output.append(struct.pack("I", 0x950412de))
    # version
    output.append(struct.pack("I", 0))
    # number of messages
    output.append(struct.pack("I", len(ids)))
    # offsets of msgid table
    output.append(struct.pack("I", 7 * 4))
    # offsets of msgstr table
    output.append(struct.pack("I", 7 * 4 + 8 * len(ids)))
    # size and offset of hash table (unused)
    output.append(struct.pack("I", 0))
    output.append(struct.pack("I", 0))

    for length, offset in koffsets:
        output.append(struct.pack("II", length, offset))
    for length, offset in voffsets:
        output.append(struct.pack("II", length, offset))

    for id_ in ids:
        output.append(id_.encode('utf-8') + b"\0")
    for s in strs:
        output.append(s.encode('utf-8') + b"\0")

    with out_path.open('wb') as fp:
        fp.write(b"".join(output))


def compile_mo_if_needed(locale_dirs):
    for loc_dir in locale_dirs:
        base = Path(loc_dir)
        if not base.exists():
            continue
        # recurse for all languages
        for lang_dir in base.iterdir():
            po = lang_dir / 'LC_MESSAGES' / 'django.po'
            mo = lang_dir / 'LC_MESSAGES' / 'django.mo'
            if not po.exists():
                continue
            try:
                # Always (re)compile to avoid stale/garbled .mo from previous runs
                messages = _read_po(po)
                if messages:
                    mo.parent.mkdir(parents=True, exist_ok=True)
                    _write_mo(messages, mo)
            except Exception as exc:
                # Log and continue; we don't want i18n compilation to break app startup
                logger.warning("Failed to compile translations from %s: %s", po, exc, exc_info=True)


def compile_default_project_locales():
    # Default LOCALE_PATHS for this project
    here = Path(__file__).resolve().parents[1]
    locale_dir = here / 'locale'
    compile_mo_if_needed([str(locale_dir)])
