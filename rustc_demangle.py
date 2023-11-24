import unicodedata

class DemangleStyle:
    def __init__(self, type: str, inner: str, elements: int):
        self.type = type
        self.inner = inner
        self.elements = elements

class Demangle:
    def __init__(self, style: DemangleStyle, original: str, suffix: str):
        self.style = style
        self.original = original
        self.suffix = suffix

    def get_fn_name(self, with_hash: bool) -> str:
        fn_name = ""

        if self.style == None:
            return self.original
        elif self.style.type == "legacy":
            inner = self.style.inner
            for element in range(self.style.elements):
                rest = inner
                while rest and rest[0].isdigit():
                    rest = rest[1:]

                i = int(inner[:(len(inner) - len(rest))])
                inner = rest[i:]
                rest = rest[:i]

                if not with_hash and element + 1 == self.style.elements and is_rust_hash(rest):
                    break

                if element != 0:
                    fn_name += "::"

                if rest.startswith("_$"):
                    rest = rest[1:]

                while True:
                    if rest.startswith("."):
                        if rest[1] == ".":
                            fn_name += "::"
                            rest = rest[2:]
                        else:
                            fn_name += "."
                            rest = rest[1:]
                    elif rest.startswith("$"):
                        end = rest[1:].find('$')
                        if end != -1:
                            escape, after_escape = rest[1:end + 1], rest[end + 2:]
                        else:
                            break

                        unescaped = None

                        if escape == "SP":
                            unescaped = "@"
                        elif escape == "BP":
                            unescaped = "*"
                        elif escape == "RF":
                            unescaped = "&"
                        elif escape == "LT":
                            unescaped = "<"
                        elif escape == "GT":
                            unescaped = ">"
                        elif escape == "LP":
                            unescaped = "("
                        elif escape == "RP":
                            unescaped = ")"
                        elif escape == "C":
                            unescaped = ","
                        else:
                            if escape.startswith('u'):
                                digits = escape[1:]

                                all_lower_hex = all(c.isdigit() or c.isalpha() and c.islower() for c in digits)
                                try:
                                    c = chr(int(digits, 16))
                                    if all_lower_hex and not is_control(c):
                                        fn_name += str(c)
                                        rest = after_escape
                                        continue
                                except ValueError:
                                    pass
                            break


                        fn_name += unescaped
                        rest = after_escape
                    elif i := next((index for index, c in enumerate(rest) if c == "$" or c == "."), None) is not None:
                        fn_name += rest[:i]
                        rest = rest[i:]
                    else:
                        break
                fn_name += rest

            return fn_name
        elif self.style.type == "v0":
            pass

def is_rust_hash(s: str) -> bool:
    return s.startswith("h") and s[1:].isalnum() and all(c.isdigit() or c.isalpha() and c.islower() for c in s[1:])

def is_control(char):
    category = unicodedata.category(char)
    return category.startswith('C')

# my hack to tupples, is there another way? Maybe, but if it works it works:tm:
class DemanglerType:
    def __init__(self, style: DemangleStyle, suffix: str):
        self.style = style
        self.suffix = suffix


def legacy_demangle(symbol: str) -> DemanglerType:
    inner = ""

    if symbol.startswith("_ZN"):
        inner = symbol[3:]
    elif symbol.startswith("ZN"):
        inner = symbol[2:]
    elif symbol.startswith("__ZN"):
        inner = symbol[4:]
    else:
        raise Exception

    if any(c & 0x80 != 0 for c in inner.encode()):
        raise Exception

    elements = 0
    chars = iter(list(inner))
    c = next(chars, None)
    while c != "E":
        # Decode an identifier element's length.
        if not c.isdigit():
            raise Exception
        len = 0
        while c.isdigit():
            len = len * 10 + int(c)
            c = next(chars, None)

        # `c` already contains the first character of this identifier, skip it and
        # all the other characters of this identifier, to reach the next element.
        for _ in range(len):
            c = next(chars, None)

        elements += 1

    return DemanglerType(style=DemangleStyle(type="legacy", inner=inner, elements=elements), suffix="".join(chars))

def v0_demangle(symbol: str) -> DemanglerType:
    raise Exception

def is_symbol_like(symbol: str) -> bool:
    return all(c.isalnum() or c in string.punctuation for c in s)

def demangle(symbol: str) -> Demangle:
    llvm = ".llvm."
    i = symbol.find(llvm)

    # if `.llvm.` is in the string, and the part after `.llvm.` is all hex plus an @ sign,
    # cut it off. Example:
    # `_ZN3fooE.llvm.9D1C9369` becomes `_ZN3fooE`
    if i != -1:
        candidate = symbol[i + len(llvm):]
        all_hex = all(c in "ABCDEF0123456789@" for c in candidate)

        if all_hex:
            symbol = symbol[:i]

    suffix = ""
    style = None
    try:
        # legacy demangle
        demangled = legacy_demangle(symbol)
        style = demangled.style
        suffix = demangled.suffix
    except Exception:
        try:
            # v0 demangle
            demangled = v0_demangle(symbol)
            style = demangled.style
            suffix = demangled.suffix
        except Exception:
            # Either ParseError or RecursedTooDeep
            style = None

    if suffix != "":
        if suffix.startswith(".") and is_symbol_like(suffix):
            # Keep the suffix (hack to get around the python interpreter)
            pass
        else:
            suffix = ""
            style = None

    return Demangle(style=style, original=symbol, suffix=suffix)

# if not imported
if __name__ == "__main__":
    import sys

    symbols = sys.argv
    symbols.pop(0)

    if len(symbols) == 0:
       print("Not enough arguments.\nUsage:\n  python rustc_demangle.py _ZN3foo3barE\n  python rustc_demangle.py _ZN3foo3barE _ZN4testE")
       exit(-1)

    for symbol in symbols:
        function_signature = demangle(symbol)
        
        print(function_signature.get_fn_name(False))
        # print(legacy_demangle(symbol))
