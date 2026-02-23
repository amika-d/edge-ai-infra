import time
import asyncio
import aiohttp
import statistics
import json

# CONFIGURATION
MODEL_NAME = "/models/AMead10/Llama-3.2-3B-Instruct-AWQ" # Must match your curl response
API_URL = "http://localhost:8000/v1/chat/completions"
MAX_TOKENS = 200 # Standard "paragraph" length
CONCURRENT_USERS = [1, 5, 10, 20, 30,35 ,40, 50 , 60] # We will test these batch sizes

async def simulate_user(session, user_id):
    """Simulates one user asking a question."""
    payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": "Explain the benefits of Edge Computing in 3 sentences."}],
        "max_tokens": MAX_TOKENS,
        "temperature": 0.7
    }
    
    start_time = time.time()
    try:
        async with session.post(API_URL, json=payload) as response:
            if response.status != 200:
                return None
            data = await response.json()
            end_time = time.time()
            
            # Calculate Metrics
            latency = end_time - start_time
            tokens = data['usage']['completion_tokens']
            tps = tokens / latency
            return {"tps": tps, "latency": latency}
    except Exception as e:
        return None

async def run_batch(num_users):
    """Runs a batch of concurrent users."""
    print(f"\n🔥 Testing with {num_users} concurrent users...")
    async with aiohttp.ClientSession() as session:
        tasks = [simulate_user(session, i) for i in range(num_users)]
        results = await asyncio.gather(*tasks)
        
    # Filter failures
    valid_results = [r for r in results if r is not None]
    failed_count = num_users - len(valid_results)
    
    if not valid_results:
        print(f"❌ All {num_users} requests failed!")
        return

    # Stats
    avg_tps = statistics.mean([r['tps'] for r in valid_results])
    p95_latency = statistics.quantiles([r['latency'] for r in valid_results], n=20)[18] # 95th percentile
    
    print(f"✅ Success: {len(valid_results)}/{num_users}")
    print(f"⚡ Avg Throughput: {avg_tps:.2f} tokens/sec")
    print(f"⏱️ P95 Latency: {p95_latency:.2f}s")
    
    if failed_count > 0:
        print(f"⚠️ Failures: {failed_count}")

async def main():
    print("🚀 Starting Production Load Test...")
    print(f"Target: {API_URL}")
    print("-" * 40)
    
    for user_count in CONCURRENT_USERS:
        await run_batch(user_count)
        time.sleep(2) # Cool down GPU

if __name__ == "__main__":
    # Install requirement if missing: pip install aiohttp
    asyncio.run(main())