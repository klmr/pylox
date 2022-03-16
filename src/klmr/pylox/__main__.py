import sys
from . import main


try:
    main()
except Exception as e:
    sys.stderr.write(f'Error: {e}\n')
    sys.exit(1)
