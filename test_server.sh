#!/bin/bash

# Start the server in the background
python backend/main.py &
SERVER_PID=$!

# Wait a moment for server to start
echo "Starting server..."
sleep 5

# Run the tests
echo "Running API tests..."
python backend/tests/test_api.py
TEST_EXIT_CODE=$?

# Kill the server process
kill $SERVER_PID

# Exit with the test exit code
exit $TEST_EXIT_CODE