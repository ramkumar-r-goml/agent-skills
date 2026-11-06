"""Settings read from the environment at start."""
import os


def database_url():
    return os.environ.get("DATABASE_URL", "orders.db")


def port():
    return int(os.environ.get("PORT", "8081"))


def max_retries():
    return int(os.environ.get("WORKER_MAX_RETRIES", "3"))


def backlog_alert():
    return int(os.environ.get("QUEUE_BACKLOG_ALERT", "500"))


def payments_api_key():
    return os.environ["PAYMENTS_API_KEY"]
