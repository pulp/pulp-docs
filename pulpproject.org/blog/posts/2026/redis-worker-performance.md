---
date: 2026-01-13T00:00:00Z
title: New Worker Type and AI Driven Development
authors:
  - dkliban
tags:
  - performance
  - tasking
  - redis
---
# New Worker Type and AI Driven Development

A performance breakthrough came from an innovative collaboration with AI. We explained the PostgreSQL load challenges we were facing to an AI assistant, which designed an algorithm that offloads resource locking to Redis while maintaining task ordering guarantees. The AI then helped write the implementation code and test suite, dramatically accelerating our development process. This approach allowed us to rapidly prototype and validate the solution, demonstrating how AI can be a powerful tool for tackling complex architectural challenges.

We're excited to share that RedisWorker delivers 2.3x performance improvement! Our recent performance benchmarking demonstrates significant throughput improvements in Pulp's tasking system. By offloading resource locking from PostgreSQL to Redis and eliminating the task unblocking mechanism, we've achieved more than double the task processing throughput.

<!-- more -->

## Architecture Benefits

By separating resource locking from the main database and eliminating the unblocking subsystem:

1. **Reduced PostgreSQL Load**: Database queries are limited to task CRUD operations, not constant lock checking or unblocking.
2. **Faster Lock Operations**: Redis's in-memory operations are generally faster than PostgreSQL advisory locks.
3. **Better Scalability**: Users can start more workers with less load on the database.
4. **Improved Throughput**: The system can process more than twice as many tasks per second.

## Benchmark Results

Our testing compared the existing `PulpcoreWorker` implementation against the new `RedisWorker` implementation under similar conditions with 80 workers and a db.m7g.large RDS instance on AWS (2 vCPUs, 8GB RAM, AWS Graviton3 physical CPU):

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

**Existing PulpcoreWorker Approach:**

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

## What Work Is Eliminated

RedisWorker achieves its performance gains by completely eliminating several resource-intensive operations:

1. **No PostgreSQL LISTEN/NOTIFY Infrastructure**: PulpcoreWorker subscribes to multiple PostgreSQL notification channels (`pulp_worker_cancel`, `pulp_worker_metrics_heartbeat`, `pulp_worker_wakeup`) and broadcasts notifications via `pg_notify()`. RedisWorker uses Redis-based cancellation signals instead, eliminating this database overhead.

2. **No Continuous Task Unblocking**: PulpcoreWorker's unblocking mechanism queries ALL incomplete tasks from the database on every cycle, iterating through potentially thousands of tasks to calculate resource conflicts. RedisWorker eliminates this entirely - it queries the first 20 waiting tasks and attempts to acquire locks.

3. **No Database Writes for Unblocking**: PulpcoreWorker must update an `unblocked_at` timestamp for each task that becomes eligible to run. RedisWorker has no unblocking concept, so these database writes are eliminated.

4. **Simpler Task Queries**: PulpcoreWorker requires `unblocked_at IS NOT NULL` in its fetch query, creating a dependency chain (dispatch → unblock → fetch → execute). RedisWorker queries tasks directly (dispatch → fetch+lock → execute).

The result: RedisWorker doesn't just move work to Redis - it eliminates an entire subsystem that was creating continuous database load.

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
- Environments that struggle with database CPU load

## Looking Forward

These performance improvements represent a significant step forward for Pulp's scalability. Before RedisWorker becomes available to users, we need to:

1. Merge the implementation into the main codebase
2. Validate the feature through our CI testing pipeline
3. Include it in an upcoming Pulp release

We encourage users with high-throughput requirements to evaluate RedisWorker in their environments once it's released.

## Upgrading

Switching between worker types requires downtime. More detailed upgrade instructions and best practices will be available in the documentation once the new worker type is released.
