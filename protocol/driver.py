import multiprocessing

# Move worker function to top level
def worker(q):
    print("Worker: Putting test message in queue")
    q.put("TEST MESSAGE")
    print("Worker: Message sent")

def test_queue_sharing():
    print("Testing queue sharing between processes...")
    manager = multiprocessing.Manager()
    test_queue = manager.Queue()
    
    # Use the top-level worker function
    p = multiprocessing.Process(target=worker, args=(test_queue,))
    p.start()
    p.join()
    
    try:
        print("Main: Attempting to get message from queue")
        msg = test_queue.get(timeout=1)
        print(f"Main: Successfully got message: {msg}")
        return True
    except Exception as e:
        print(f"Main: Failed to get message: {e}")
        return False

# Run the test
if __name__ == "__main__":
    if test_queue_sharing():
        print("✅ Queue sharing works correctly!")
    else:
        print("❌ Queue sharing is broken!")