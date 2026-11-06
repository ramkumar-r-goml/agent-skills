# Architecture Overview

## Introduction

In today's fast-paced world, OrderFlow plays a crucial role in order fulfilment. This document provides a comprehensive overview of its components.

## Components

- **API:** handles order-related operations
- **Worker:** processes orders
- **Redis Cache:** caches order reads for `get_order`, invalidated by `invalidate_order_cache`
- **Notifications Service:** emails customers through `send_order_email`
- **Postgres:** stores data

## Failure Handling

Errors are handled gracefully to ensure a smooth experience. See `src/orderflow/retry.py` for the retry policy.

For operating the system, see the [runbook](runbook.md).
