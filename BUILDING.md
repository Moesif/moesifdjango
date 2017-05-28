
## Building distributable package.

 ```bash
 python setup.py sdist

 ```
 (run from inside the root folder).
 This creates a directory called dist and builds your new package.

## Installing from local package

if needed set up virtual env first.

https://virtualenv.pypa.io/en/stable/

```bash
virtualenv ENV
```

```bash
source bin/activate
```

```
pip install --user path/to/moesifdjango.tar.gz

```

to uninstall

```
pip uninstall moesifdjango
```
