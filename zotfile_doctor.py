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

import argparse
import os
import sqlite3
import unicodedata
from collections.abc import Iterable
from pathlib import Path

try:
    from rich import print
except ImportError:
    pass


def iter_db(db: str | Path, directory: str | Path) -> Iterable[str]:
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


def iter_dir(directory: str | Path) -> Iterable[str]:
    for path in Path(directory).rglob('*.pdf'):
        yield unicodedata.normalize('NFD', path.relative_to(directory).as_posix())


def remove_empty_dirs(directory):
    d: str
    for root, dirs, _file in os.walk(directory, topdown=False):
        for d in dirs:
            try:
                (Path(root) / d).rmdir()
            except OSError:
                continue


def main(db: str | Path, directory: str | Path, *, clean=False):
    directory = Path(directory)

    _db = {Path(x).as_posix() for x in iter_db(db, directory)}
    _dir = set(iter_dir(directory))

    db_not_dir = sorted(_db - _dir)
    dir_not_db = sorted(_dir - _db)

    print(
        f'There were {len(db_not_dir)}/{len(_db)} '
        'files in DB but not in zotfile directory:'
    )
    for file in db_not_dir:
        print(f'  - "{file}"')

    print(
        f'\nThere were {len(dir_not_db)}/{len(_dir)} '
        'files in zotfile directory but not in DB:'
    )
    for file in dir_not_db:
        print(f'  - "{file}"')

    if not (clean and len(dir_not_db) > 0):
        return

    print()
    for file in dir_not_db:
        p = directory / file
        try:
            p.unlink()
        except OSError:
            print(f'Failed to unlink "{file}"')
        else:
            print(f'Unlinked "{file}"')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='zotfile directory consistency checker'
    )
    parser.add_argument('zotero_sqlite', help='path-to-zotero/zotero.sqlite')
    parser.add_argument('zotfile_directory', help='zotfile directory')
    parser.add_argument(
        '-c',
        '--clean',
        action='store_true',
        help='remove files in zotfile directory but not in DB',
    )
    args = parser.parse_args()

    main(
        db=args.zotero_sqlite,
        directory=args.zotfile_directory,
        clean=args.clean,
    )
