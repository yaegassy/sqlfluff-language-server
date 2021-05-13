# [Expelmental] sqlfluff-language-server

[Expelmental] A sql language server exclusively for [sqlfluff](https://pypi.org/project/sqlfluff/) and [coc.nvim](https://github.com/neoclide/coc.nvim) extension.

<img width="780" alt="sqlfluff-language-server-demo" src="https://user-images.githubusercontent.com/188642/118091006-40354080-b405-11eb-9e53-6cc1e768167a.gif">

## Overview

- "Server" by `sqlfluff-language-server` command (Language server)
- "Client" by `coc-sqlfluff-ls` (For operation test)

## Features

- Lint
- Format

## Note

sqlfluff-language-server is a language server that uses the sqlfluff [API](https://docs.sqlfluff.com/en/stable/api.html).

## Server (sqlfluff-language-server)

**setup**:

```sh
poetry install
poetry shell
sqlfluff-language-server --help
```

**help**:

```sh
usage: sqlfluff-language-server [-h] [--version] [--tcp] [--host HOST]
                                [--port PORT] [--log-file LOG_FILE] [-v]

sqlfluff-language-server

optional arguments:
  -h, --help           show this help message and exit
  --version            display version information and exit
  --tcp                Use TCP server instead of stdio
  --host HOST          Bind to this address
  --port PORT          Bind to this port
  --log-file LOG_FILE  redirect logs to the given file instead of writing to
                       stderr
  -v, --verbose        increase verbosity of log output
```

> default: `stdio`

### Client (coc-sqlfluff-ls)

```sh
yarn install
# or yarn build
```

Now `set runtimepath^=/path/to/sqlfluff-language-server` in "vimrc/init.vim"

## Related coc.nvim extension

- [yaegassy/coc-sqlfluff](https://github.com/yaegassy/coc-sqlfluff)
  - Using the sqlfluff [CLI](https://docs.sqlfluff.com/en/stable/cli.html)

## Thanks

- [sqlfluff/sqlfluff](https://github.com/sqlfluff/sqlfluff)
- [openlawlibrary/pygls](https://github.com/openlawlibrary/pygls)

## License

MIT
