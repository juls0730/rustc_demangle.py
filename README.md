# rustc_demangle.py
A single-file python port of the Rust symbol demangling library, [rustc-demangle](https://github.com/rust-lang/rustc-demangle).

## Usage
You can use rustc_demangle.py as a command-line utility, like so:

```BASH
python rustc_demangle.py _ZN3foo3barE
```

rustc_demangle.py can also take multiple strings to demangle. Instead, if you would like to use rustc_demangle.py as a library, you can use it like so:

```PYTHON
import rustc_demangle

print(rustc_demangle.demangle("_ZN4testE").get_fn_name(False))
```

## Port Status

This port is quick and dirty, intended to be usable as a CLI script for my [OS project](https://github.com/juls0730/CappuccinOS). Nevertheless, I do actually intend on maintaining this port, here is the current status:

- Ported legacy (pre-RFC2603) demangling
- v0 demangling is non-existant ;~;

## License
This project is licensed under the Creative Commons Zero v1.0 Universal, also known as CC0.

### Contribution
Any contributions intentionally submitted for inclusion in rustc_demangle.py by you shall be licensed as above, in accordance with the Creative Commons Zero v1.0 Universal (CC0), without any additional terms or conditions.
