import redis
import os

r = redis.from_url("redis://default:yEzs5PcNSpiYOV7qBmyp4xAfatL8mvZ8@redis-17174.c89.us-east-1-3.ec2.cloud.redislabs.com:17174")

print(r.ping())