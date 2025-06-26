# Dupe-Linker

> Find duplicate files & symlink duplicates to the first found version.

## Features
- Identifies duplicate files recursively in a specified directory.
- Generates SHA-256 hashes (in parallel) for files matching user-defined extensions.
- Stores hash values in an SQLite database for future comparison.
- Creates symbolic links (symlinks) pointing to the first version of each unique file found.

## Warning

- This program **WILL DELETE FILES**, so make sure you have a backup or have **run --dry_run AND CHECK WHAT YOU ARE DOING**.
- Generally it is NOT a great idea to blindly symlink a bunch of files just because they are duplicates.. there could be many reasons for having a duplicate copy of a file.
- This exists for the specific problem of ComfyUI custom nodes and other AI software that has no standard place to store model files, 
  and often downloads them to different locations with different names, even when using StabilityMatrix.

## Requirements
- Python 3.x
- sqlite3 module (included with Python 3)

## Usage
Run the program from the command line using the following arguments:
```
python3 dupe-linker.py -d <directory> -e <extension1>,<extension2>,...
```

Example:
```
./dupe-linker.py -d /path/to/directory -e .safetensors,.bin,.path,.pt
```

Arguments:
- `-D`, `--dry_run`: Dry run mode. Saves hash values to the DB and reports which files could be symlinked but does not remove or create any symlinks.
- `-d`, `--dir`: Directory path to scan for files.
- `-e`, `--extensions`: List of extensions that should be considered for symlinking (default = .bin, .safetensors, .pth, .pt).
- `-t`, `--threads`: Number of threads to use for parallel processing. Default is 4. (Only the hashing is performed in parallel)
- `-b`, `--db_path`: Path to the database file (default ./model-data.sqlite3).

## Author
Matt Zrinsky <matt.zrinsky@gmail.com>

## License
MIT License
