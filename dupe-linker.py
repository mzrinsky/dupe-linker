#!/usr/bin/env python3

"""
Dupe-Linker: A program to find duplicate files and symlink duplicates to the first found version.

This program helps you identify and manage duplicate files in a specified directory.
It generates SHA-256 hashes for all the files matching the extensions you specify and stores them in an SQLite database.
When it encounters duplicate files, it creates symbolic links (symlinks) pointing to the first version of each unique file found.

This program WILL DELETE FILES, so make sure you have a backup or have run --dry_run AND ARE SURE OF WHAT YOU ARE DOING.

Usage:
Run the program from the command line with the following arguments:

python3 dupe-linker.py -d <directory> -e <extension1>,<extension2>,...

Example:
./dupe-linker.py -d /path/to/directory -e .safetensors,.bin,.path,.pt

Arguments:
- -D, --dry_run: Dry run mode. Saves hash values to the DB and reports which files could be symlinked but does not remove or create any symlinks.
- -d, --dir: Directory path to scan for files.
- -e, --extensions: List of extensions that should be considered for symlinking (default = .bin, .safetensors, .pth, .pt).
- -t, --threads: Number of threads to use for parallel processing. Default is 4. (Only the hashing is performed in parallel)
- -b, --db_path: Path to the database file (default ./model-data.sqlite3).

Requirements:
- Python 3.x
- sqlite3 module (included with Python 3)

Author: Matt Zrinsky <matt.zrinsky@gmail.com>
License: MIT License
"""

import argparse
import os
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
import sqlite3

con = None
cur = None
dry_run = False

def db_connect(filename):
    global con, cur
    con = sqlite3.connect(filename)
    cur = con.cursor()
    # Create table if it doesn't exist
    cur.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            path TEXT NOT NULL,
            sha256 TEXT NOT NULL UNIQUE
        )
    """)

def db_close():
    global con, cur
    if con is not None:
      con.close()
      con = None
      cur = None


def lookup_hash(hash):
    global con, cur
    cur.execute("SELECT id, path, sha256 FROM files WHERE sha256=?", (hash,))
    result = cur.fetchone()
    return result

def save_hash(file_path, hash):
    file = os.path.basename(file_path)
    cur.execute("INSERT INTO files (filename, path, sha256) VALUES (?, ?, ?)",
            (file, file_path, hash))
    con.commit()

def calculate_file_hash(file_path):
    """
    Calculate the SHA-256 hash of a file.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return file_path, sha256_hash.hexdigest()

def traverse_directory(directory, extensions):
    """
    Traverse a directory recursively and yield file paths matching requested extensions.
    """
    for root, dirs, files in os.walk(directory):
        for file in files:
            # get the file extension
            ext = os.path.splitext(file)[1]
            # check if the extension is in the list of requested extensions
            if ext in extensions:
              file_path = os.path.join(root, file)
              # ensure the file is NOT a symlink and NOT empty
              if os.path.islink(file_path) == False and os.path.getsize(file_path) != 0:
                  # yield the file path for processing
                  yield file_path

def process_files(directory, extensions, database_file):
    """
    Process files in directory, calculating hashes for each, and removing / symlinking as necessary.
    """
    global dry_run, use_max_threads
    file_paths = list(traverse_directory(directory, extensions))
    with ThreadPoolExecutor(max_workers=use_max_threads) as executor:
        db_connect(database_file)
        total_savings = 0
        futures = [executor.submit(calculate_file_hash, file_path) for file_path in file_paths]
        for future in as_completed(futures):
            file_path, hash_value = future.result()
            # print(f"File: {file_path} - Hash: {hash_value}")
            result = lookup_hash(hash_value)
            if result and result[1] != file_path:
                # File already exists with a different path
                new_savings = os.path.getsize(file_path)
                total_savings += new_savings
                if dry_run == False:
                    print(f"Symlinking {file_path} => {result[1]} saving {new_savings} more bytes.")
                    # Perform symlink creation or other actions here
                    os.remove(file_path)
                    os.symlink(result[1], file_path)
                else:
                    print(f"File {file_path} can be symlinked to: {result[1]} saving {new_savings} more bytes.")
            elif result and result[1] == file_path:
                # file exists with the same path
                # print(f"File {file_path} already exists in DB: {result[1]} : {result[2]}")
                pass
            else:
                # Insert new file information into the database
                save_hash(file_path, hash_value)
                print(f"Added new file: {file_path} with sha256: {hash_value}")

        if dry_run:
          print(f"Total possible savings: {total_savings} bytes")
        else:
          print(f"Saved: {total_savings} bytes.")

        db_close()

def main():
    global dry_run, use_max_threads

    parser = argparse.ArgumentParser()
    parser.add_argument("-D", "--dry_run", action="store_true", help="Dry run mode, will save hashes to the DB, and tell you which files could be symlinked, but not remove or symlink any files.")
    parser.add_argument("-d", "--dir", help="Directory path to scan for files")
    parser.add_argument("-e", "--extensions", nargs='+', default=[".bin", ".safetensors", ".pth", ".pt"], help="List of extensions that should be considered for symlinking (default = .bin, .safetensors, .pth, .pt)")
    parser.add_argument("-t", "--threads", default=4, help="Directory path to scan for files")
    parser.add_argument("-b", "--db_path", default="./model-data.sqlite3", help="Path to the database file (default ./model-data.sqlite3)")

    args = parser.parse_args()

    dry_run = args.dry_run
    use_max_threads = args.threads

    if args.dir and args.extensions:
      process_files(args.dir, args.extensions, args.db_path)
    else:
      parser.print_help()

if __name__ == "__main__":
    main()
    