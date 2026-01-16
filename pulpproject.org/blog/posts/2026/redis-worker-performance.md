---
date: 2026-01-13T00:00:00Z
title: RedisWorker Delivers 2.3x Performance Improvement
authors:
  - dkliban
tags:
  - performance
  - tasking
  - redis
---
# RedisWorker Delivers 2.3x Performance Improvement

This performance breakthrough came from an innovative collaboration with AI. We explained the PostgreSQL load challenges we were facing to an AI assistant, which designed an algorithm that offloads resource locking to Redis while maintaining task ordering guarantees. The AI then helped write the implementation code and test suite, dramatically accelerating our development process. This approach allowed us to rapidly prototype and validate the solution, demonstrating how AI can be a powerful tool for tackling complex architectural challenges.

We're excited to share results from our recent performance benchmarking that demonstrate significant throughput improvements in Pulp's tasking system. By offloading resource locking from PostgreSQL to Redis and eliminating the task unblocking mechanism, we've achieved more than double the task processing throughput.

<!-- more -->

## Benchmark Results

Our testing compared the traditional `PulpcoreWorker` implementation against the new `RedisWorker` implementation under identical conditions:

**PulpcoreWorker Performance:**

- Processed: 20,296 completed tasks
- Time window: 671.25 seconds
- **Average throughput: 30.24 tasks/sec**

**RedisWorker Performance:**

- Processed: 21,419 completed tasks
- Time window: 306.91 seconds
- **Average throughput: 69.79 tasks/sec**

The RedisWorker achieved **2.3x higher throughput** (69.79 vs 30.24 tasks/sec) while processing a similar number of tasks in less than half the time.

## How We Achieved This

The performance improvement comes from two key innovations: offloading resource lock coordination to Redis and eliminating the task unblocking mechanism. Here's what changed:

**Traditional PulpcoreWorker Approach:**

- Uses PostgreSQL advisory locks for task resource coordination
- At any given time, one worker constantly queries the database to find and unblock waiting tasks
- This unblocking process runs continuously, creating steady database load
- Lock operations create additional load on the PostgreSQL database
- Suitable for most deployments, especially when Redis isn't available

**New RedisWorker Approach:**

- Uses Redis distributed locks for resource coordination
- No unblocking mechanism needed - workers simply attempt to acquire locks for waiting tasks
- If locks can't be acquired, the task remains in the queue for the next worker to try
- Eliminates the continuous database queries for task unblocking
- Significantly reduces both database load and unnecessary CPU work
- Scales better under high task volumes by doing less work overall

## Architecture Benefits

By separating resource locking from the main database:

1. **Reduced PostgreSQL Load**: Database queries are limited to task CRUD operations, not constant lock checking
2. **Faster Lock Operations**: Redis's in-memory operations are significantly faster than database queries
3. **Better Scalability**: Workers can check and acquire locks with minimal overhead
4. **Improved Throughput**: The system can process more than twice as many tasks per second

## Configuration

The worker type is configurable via the `WORKER_TYPE` setting:

```python
# Use PostgreSQL advisory locks (default, stable)
WORKER_TYPE = "pulpcore"

# Use Redis distributed locks (higher performance)
WORKER_TYPE = "redis"
```

## Important Considerations

While RedisWorker delivers superior performance, there are some trade-offs to consider:

- **Redis Dependency**: Requires a Redis instance to be available
- **Stability**: PulpcoreWorker remains the default and is the more mature implementation

## When to Use RedisWorker

RedisWorker is ideal for:

- High-volume task processing environments
- Deployments where Redis is already part of the infrastructure
- Scenarios where task throughput is critical

## Looking Forward

These performance improvements represent a significant step forward for Pulp's scalability. We're continuing to enhance the RedisWorker implementation and explore additional optimizations.

The RedisWorker implementation will be available soon in upcoming Pulp releases. We encourage users with high-throughput requirements to evaluate it in their environments once released.
