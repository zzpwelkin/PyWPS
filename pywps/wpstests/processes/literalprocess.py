#!/usr/bin/env python
from contextlib import closing
def execute(in_int, in_string, out_int, out_string):
    with closing(open(out_int,'w')) as f:
        f.write(in_int)
        
    with closing(open(out_string,'w')) as f:
        f.write(in_string)

if __name__ == "__main__":
    import sys
    execute(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])