import json, pika
from redis import Redis
from .config import settings

def handle_event(event):
    """Record idempotent receipt; event-specific projections can safely retry."""
    event_id=event.get("actionId") or event.get("documentId") or event.get("correlationId")
    if not event_id:
        raise ValueError("event is missing an idempotency key")
    redis=Redis.from_url(settings.redis_url,decode_responses=True)
    return redis.set(f"factoryops:consumer:{event_id}",json.dumps(event,sort_keys=True),nx=True)

def consume(handler=handle_event):
    connection=pika.BlockingConnection(pika.URLParameters(settings.rabbitmq_url)); channel=connection.channel()
    channel.queue_declare("factoryops.agent.events",durable=True)
    def callback(ch,method,properties,body):
        try: handler(json.loads(body)); ch.basic_ack(method.delivery_tag)
        except Exception: ch.basic_nack(method.delivery_tag,requeue=True)
    channel.basic_qos(prefetch_count=10); channel.basic_consume("factoryops.agent.events",callback); channel.start_consuming()

if __name__ == "__main__":
    consume()
