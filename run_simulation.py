import os
import sys
import subprocess

# Change to the protocol directory
os.chdir('../protocol')

# Run the channel_driver.py with output redirected to stdout
process = subprocess.Popen(['python', 'channel_driver.py'], 
                          stdout=subprocess.PIPE, 
                          stderr=subprocess.STDOUT,
                          text=True,
                          bufsize=1)

# Print output in real-time
for line in process.stdout:
    print(line, end='')
    sys.stdout.flush()

process.wait()
