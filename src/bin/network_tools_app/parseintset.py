import sys
import os

# return a set of selected values when a string in the form:
# 1-4,6
# would return:
# 1,2,3,4,6
# as expected...

def parseIntSet(nputstr, throw_exception_on_invalid=False):
  selection = set()
  invalid = set()

  # Tokens are comma seperated values; split them up
  tokens = [x.strip() for x in nputstr.split(',')]

  # Process each token
  for i in tokens:
     try:
        # Typically tokens are plain integers
        selection.add(int(i))
     except:
        # If not, then it might be a range
        try:
           token = [int(k.strip()) for k in i.split('-')]
           if len(token) > 1:
              token.sort()
              # We have items seperated by a dash
              # Try to build a valid range
              first = token[0]
              last = token[len(token) - 1]
              for x in range(first, last + 1):
                 selection.add(x)
        except:
           # Not an int and not a range; then it is invalid
           invalid.add(i)

   # Throw an exception if some of the entries are invalid
  if len(invalid) > 0 and throw_exception_on_invalid:
     raise ValueError("Invalid input provided: %s", ",".join(invalid))

  return selection
