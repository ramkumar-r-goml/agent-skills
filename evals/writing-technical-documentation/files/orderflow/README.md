# OrderFlow

OrderFlow is a robust, seamless order processing platform that empowers teams to streamline their fulfilment journey. It leverages a cutting-edge architecture to deliver blazing fast performance at any scale.

## Features

- **Fast:** Redis caching keeps every read under a millisecond
- **Reliable:** failed orders are retried 5 times automatically
- **Easy:** simply start it and you're good to go

## Getting started

Requires Python 3.9 or later.

```bash
cp .env.sample .env
make start
```

The API is now running at http://localhost:8080.

Set `DATABASE_URI` to your database and `REDIS_URL` to your Redis instance.

See [the setup guide](docs/setup.md) for more details and [the architecture](docs/architecture.md).

## Support

Reach out to the team in #orderflow-help.
