#!/usr/bin/env python3

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""Checks the consistency between the zotfile-managed directory and the database."""

import sqlite3
import unicodedata
from collections.abc import Iterable
from pathlib import Path

import cyclopts
import rich


def _iter_db(db: str | Path, directory: str | Path) -> Iterable[str]:
    conn = sqlite3.connect(db)
    db_c = conn.execute(
        'select path from itemAttachments where '
        'linkMode = 2 or linkMode = 3 and contentType = "application/pdf"'
    )
    db_d = db_c.fetchall()

    for i, _ in enumerate(db_d):
        try:
            # Ignore all kind of errors wholesale, i.e. duck typing
            item = db_d[i][0]
            if not item.lower().endswith('.pdf'):
                continue
            if item.count('attachments:') > 0:  # relative path
                item = item.replace('attachments:', '')
            else:  # absolute path
                item = Path(item).relative_to(directory).as_posix()
        except (OSError, ValueError, TypeError):
            # file is not in zotfile directory
            continue

        yield unicodedata.normalize('NFD', item)


def _iter_dir(directory: Path) -> Iterable[str]:
    for path in directory.rglob('*.pdf'):
        yield unicodedata.normalize('NFD', path.relative_to(directory).as_posix())


app = cyclopts.App(config=cyclopts.config.Toml('config.toml'))


@app.default
def main(db: Path, directory: Path, *, clean: bool = False) -> None:
    """
    Zotfile directory consistency checker.

    Parameters
    ----------
    db : Path
        zotero.sqlite path
    directory : Path
        Zotfile directory
    clean : bool, optional
        Remove files in zotfile directory but not in DB.
    """
    directory = Path(directory)
    console = rich.get_console()

    db_files = {Path(x).as_posix() for x in _iter_db(db, directory)}
    dir_files = set(_iter_dir(directory))

    db_not_dir = sorted(db_files - dir_files)
    dir_not_db = sorted(dir_files - db_files)

    console.print(
        f'There were {len(db_not_dir)}/{len(db_files)} '
        'files in DB but not in zotfile directory:'
    )
    console.print(db_not_dir)

    console.print(
        f'\nThere were {len(dir_not_db)}/{len(dir_files)} '
        'files in zotfile directory but not in DB:'
    )
    console.print(dir_not_db)

    if not (clean and len(dir_not_db) > 0):
        return

    console.print()
    for file in dir_not_db:
        p = directory / file

        try:
            p.unlink()
        except OSError:
            console.print(f'Failed to unlink "{file}"')
        else:
            console.print(f'Unlinked "{file}"')


if __name__ == '__main__':
    app()
