# X'BPGH Save File Parser + Simulator

A simple tool/library for parsing/validating solutions to X'BPGH: The Forbidden
Path, a subgame of [Last Call BBS](https://zachtronics.com/last-call-bbs/).

## Usage

To validate and compute metrics for your own save file, use
```
python -m main validate_all <save_file_path>
```
Save files are usually located at:
```
Windows: %USERPROFILE%\Documents\My Games\Last Call BBS\<user-id>\save.dat
Linux: $HOME/.local/share/Last Call BBS/<user-id>/save.dat
```
Alternatively, use `-` as the path to read from stdin.

To simulate/visualize a particular level, use
```
python -m main simulate <level_name> <slot_number> <save_file_path>
```
Run `python -m main` to see detailed format.

Sample output:
```
$ python -m main simulate 1-1 3 ~/.local/share/Last\ Call\ BBS/7...5/save.dat
1-1 (Slot 3)
Metrics:
is_correct = True
num_rules = 5
num_rules_conditional = 0
num_frames = 7
is_stable = True
num_waste = 0
Simulation:
┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐
│_ _ █ █│ │_ _ █ █│ │_ _ █ █│ │_ _ █ █│ │* _ █ █│ │*-* █ █│
│       │ │       │ │       │ │       │ │|      │ │|      │
│_ █ █ █│ │_ █ █ █│ │_ █ █ █│ │* █ █ █│ │* █ █ █│ │s █ █ █│
│       │ │       │ │       │ │|      │ │|      │ │|      │
│_ * _ █│ │_ *-* █│ │*-*-* █│ │*-s-s █│ │s-s-s █│ │s-s-s █│
│       │ │       │ │    |  │ │    |  │ │    |  │ │    |  │
│█ █ _ _│ │█ █ _ _│ │█ █ * _│ │█ █ *-*│ │█ █ *-s│ │█ █ s-s│
│       │ │       │ │       │ │       │ │    |  │ │    |  │
│█ _ _ █│ │█ _ _ █│ │█ _ _ █│ │█ _ _ █│ │█ _ * █│ │█ *-* █│
└───────┘ └───────┘ └───────┘ └───────┘ └───────┘ └───────┘
┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐
│s-s █ █│ │s-s █ █│ │s-s █ █│ │s-s █ █│ │s-s █ █│ │s-s █ █│
│|      │ │|      │ │|      │ │|      │ │|      │ │|      │
│s █ █ █│ │s █ █ █│ │s █ █ █│ │s █ █ █│ │s █ █ █│ │s █ █ █│
│|      │ │|      │ │|      │ │|      │ │|      │ │|      │
│s-s-s █│ │s-s-s █│ │s-s-s █│ │s-s-s █│ │s-s-s █│ │s-s-s █│
│    |  │ │    |  │ │    |  │ │    |  │ │    |  │ │    |  │
│█ █ s-s│ │█ █ s-s│ │█ █ s-s│ │█ █ s-s│ │█ █ s-s│ │█ █ s-s│
│    |  │ │    |  │ │    |  │ │    |  │ │    |  │ │    |  │
│█ s-s █│ │█ s-s █│ │█ s-s █│ │█ s-s █│ │█ s-s █│ │█ s-s █│
└───────┘ └───────┘ └───────┘ └───────┘ └───────┘ └───────┘
Rules:
DIVIDE
┌─────┐ ┌─────┐
│     │ │     │
│     │ │     │
│  *  │>│  *-*│
│     │ │     │
│     │ │     │
└─────┘ └─────┘
DIVIDE
┌─────┐ ┌─────┐
│     │ │     │
│     │ │     │
│  *  │>│*-*  │
│     │ │     │
│     │ │     │
└─────┘ └─────┘
DIVIDE
┌─────┐ ┌─────┐
│     │ │  *  │
│     │ │  |  │
│  *  │>│  *  │
│     │ │     │
│     │ │     │
└─────┘ └─────┘
DIVIDE
┌─────┐ ┌─────┐
│     │ │     │
│     │ │     │
│  *  │>│  *  │
│     │ │  |  │
│     │ │  *  │
└─────┘ └─────┘
SPECIALIZE
┌─────┐ ┌─────┐
│     │ │     │
│     │ │     │
│  *  │>│  s  │
│     │ │     │
│     │ │     │
└─────┘ └─────┘
```

## Technical Notes

### Cell types

We use these symbols/names for the various types of cells, in the order of the game UI:
```
" ": CellType.IGNORE,
"*": CellType.SEED,
"f": CellType.FLESH,
"M": CellType.FLESH_MUSCLE,
"H": CellType.FLESH_HEART,
"F": CellType.FLESH_FAT,
"b": CellType.BONE,
"B": CellType.BONE_SPINE,
"s": CellType.SKIN,
"W": CellType.SKIN_HAIR,
"O": CellType.SKIN_EYE,
"█": CellType.METAL,
"X": CellType.METAL,  # Alternative
"?": CellType.ANY,
"_": CellType.NONE,
```

### Save file format

The relevant lines of `save.dat` are of the form
```
Toronto.Solution.<LevelID>.<SaveSlot> = <SolutionString>
```
LevelID is the numeric ID of the level (see [this post](https://old.reddit.com/r/lastcallbbs/comments/wkgg96/comment/ijn4oo9/)).
SaveSlot is 0, 1, 2, or 3 (top-left, top-right, bottom-left, bottom-right).
SolutionString is is the binary solution file, zlib compressed and base64 encoded.

Decompressed solutions are variable-length encoded, using mostly little-endian (LE) 32-bit integers, and have the following high level structure
```
header: 4-byte LE int, always 1003 (0xEB 0x03 0x00 0x00)

num_rules: 4-byte LE int, always 16 (0x10 0x00 0x00 0x00)
rules: <num_rules = 16> rules in priority order, using a variable-length encoding, see below

start_coords: pair of 4-byte LE ints (x, y)

num_metal_coords: 4-byte LE int, always 0 except for level editor
metal_coords: <num_metal_coords> pairs of 4-byte LE ints (x, y)
```
All coordinates are 0-indexed and in `(x, y)` form, with `x` from left to right and `y` from bottom to top (so `0 <= x < 4` and `0 <= y < 5`, origin at the bottom left). `start_coords` gives the coordinates of the starting seed cell, and `metal_coords` is a list of coordinates containing metal (only nonempty in the level editor, LevelID 16).

#### Rules

Rules are variable-length encoded, and each has length 13, 17, or 21 bytes. The rule format is:
```
  target_cell_type: 4-byte LE int, see cell types
neighbor_cell_type: 4-byte LE int, see cell types
neighbor_direction: 4-byte LE int, 1 = RIGHT, 2 = UP, 4 = LEFT, 8 = DOWN
     reaction_type: *1*-byte int, 0 = IGNORE, 1 = DIVIDE, 2 = SPECIALIZE, 3 = FUSE, 4 = DIE
     divide_coords: (for DIVIDE reactions only) pair of 4-byte LE ints (dx, dy) from -1 to +1, direction to divide
    fuse_direction: (for FUSE reactions only) 4-byte LE int, 1=R, 2=U, 4=L, 8=D, direction to fuse
   specialize_type: (for SPECIALIZE reactions only) 4-byte LE int, see cell types
```

The cell types are:
```
 0: IGNORE
 1: SEED
 2: FLESH
 3: FLESH_HEART
 4: FLESH_MUSCLE
 5: FLESH_FAT
 6: BONE
 7: BONE_SPINE
 8: SKIN
 9: SKIN_HAIR
10: SKIN_EYE
11: METAL
12: ANY
13: NONE
```
Note that `FLESH_HEART` and `FLESH_MUSCLE` are transposed compared to the game UI.

For example (written in left-to-right byte order):
```
0x01000000 0x0c000000 0x02000000 0x01 0xffffffff 0x00000000   SEED with ANY ABOVE should DIVIDE towards (-1, 0) (LEFT)
0x08000000 0x00000000 0x01000000 0x03 0x08000000              SKIN (IGNORE neighbor) should FUSE DOWN
0x06000000 0x05000000 0x01000000 0x02 0x07000000              BONE with FLESH_FAT to the RIGHT should SPECIALIZE into BONE_SPINE
0x0a000000 0x00000000 0x01000000 0x04                         SKIN_EYE (IGNORE neighbor) should DIE
0x04000000 0x00000000 0x01000000 0x00                         FLESH_MUSCLE (IGNORE neighbor) should IGNORE (rule is treated as empty)
0x00000000 0x00000000 0x01000000 0x00                         empty rule (has no effect)
```
