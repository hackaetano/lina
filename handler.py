import json
from fbmq import Page

FB_ACCESS_TOKEN = 'EAANGelcYPyUBAOojxXZC70lrH9Sq8FFZBDQR3ZArYx2kR7yG4wn097S8x51c751bxHGV5WlBIx2m4YJZBDBta3l78KRkafUZC60K0RN9VLQo6UhPnQYgZChw4ZAtZCZAMH7y0cHWs9ApZCKWgIm1tRsA7QHngOI1nHbkCbmP6aEgLzSAZDZD'

def response(body, code=200):
  return {
    'statusCode': code,
    'body': json.dumps(body)
  }

def hello(event, context):
  body = {
    "message": "Go Serverless v1.0! Your function executed successfully!",
    "input": event
  }

  return response(body)
