#!/bin/bash

# Run pytest and capture the exit code
pytest --disable-warnings --maxfail=1 -q
EXIT_CODE=$?

# Check the exit code and print a big success message if tests pass
if [ $EXIT_CODE -eq 0 ]; then
  echo -e "\n\n"
  echo "########################################"
  echo "#                                      #"
  echo "#          ALL TESTS PASSED!           #"
  echo "#                                      #"
  echo "########################################"
  echo -e "\n\n"
fi

# Exit with the same code as pytest
exit $EXIT_CODE