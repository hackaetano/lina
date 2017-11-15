import json
import requests
import urllib3
import random

API_ENDPOINT = 'https://niemeyer.hackaetano.com'

FOLLOWUP_EVENTS = [
  "GET_PROPERTY_INFO",
  "GET_FAMILY_INFO"
]

def post_user(user):
  encoded_body = json.dumps(user)

  http = urllib3.PoolManager()

  res = http.request('POST', '{}/users'.format(API_ENDPOINT),
                      headers={'Content-Type': 'application/json'},
                      body=encoded_body)

  data = res.data

  return json.loads(data)

def put_user(user_id, user):
  encoded_body = json.dumps(user)

  http = urllib3.PoolManager()

  res = http.request('PUT', '{}/users/{}'.format(API_ENDPOINT, user_id),
                      headers={'Content-Type': 'application/json'},
                      body=encoded_body)

  data = res.data

  return json.loads(data)

def get_user_by_id(user_id):
  res = requests.get('{}/users/{}'.format(API_ENDPOINT, user_id))
  return res.json()

def handle_welcome(data):
  email = data['resolvedQuery']

  user = get_api_user(email)

  if user is None:
    return {
      'source': "Hackaetano",
      'followupEvent': {
        'name': "NEW_REGISTERED_USER"
      }
    }
  else:
    return {
      'source': "Hackaetano",
      'followupEvent': {
        'name': random.choice(FOLLOWUP_EVENTS)
      },
      'contextOut': [
        {
          'name': 'loggedUser',
          'lifespan': 10,
          'parameters': {
            'email': email,
            'id': user['_id']
          }
        }
      ]
    }

def handle_property_value(data):
  update = data['parameters']
  contexts = data['contexts']

  user_id = None

  for context in contexts:
    if context['name'] == 'loggeduser':
      if 'id' in context['parameters']:
        user_id = context['parameters']['id']
      else:
        user_id = context['parameters']['id.original']

  if user_id is None:
    return {
      'source': 'Hackaetano',
      'followupEvent': {
        'name': 'UNKNOWN_USER'
      }
    }

  user = get_user_by_id(user_id)

  changes = {
    'preferences': {
      'property': {
        'settings': {
          'propertyType': update['type'],
          'size': int(update['size']),
          'pricing': int(update['value']),
          'rooms': int(update['rooms'])
        }
      }
    }
  }

  user.update(changes)

  put_user(user_id, user)

  recommendations = get_recommendations({'id': user_id})

  return {
    'source': 'Hackaetano',
    'followupEvent': {
      'name': 'RSR',
      'data': recommendations
    }
  }

def handle_familiar_value(data):
  context = data['contexts'][0]['parameters']

  if 'email.original' in context:
    email = context['email.original']
  else:
    email = context['email']

  user_id = context['id']

  user = get_user_by_id(user_id)

  nb_filhos = int(context['nb_filhos'])

  changes = {
    "familiar": {
      "children": {
        "has": nb_filhos > 0,
        "howMany": nb_filhos
      }
    }
  }

  user.update(changes)

  res = put_user(user_id, user)

  recommendations = get_recommendations({'id': user_id})

  return {
    'source': 'Hackaetano',
    'followupEvent': {
      'name': 'RSR',
      'data': recommendations
    },
    'contextOut': [
      {
        'name': 'loggeduser',
        'lifespan': 10,
        'parameters': {
          'email': email,
          'id': user_id
        }
      }
    ]
  }

def handle_register_user(data):
  register = data['parameters']
  original = data['contexts'][0]['parameters']

  if 'email.original' in original:
    email = original['email.original']
  else:
    email = original['email']

  user = {
    'personal': {
      'name': register['name'],
      'email': email,
      'income': int(register['income'])
    },
    'preferences': {
      'neighborhood': {
        'settings': {
          'district': [register['address']]
        }
      }
    }
  }

  res = post_user(user)

  recommendations = get_recommendations({'id': res['_id']})

  return {
    'source': 'Hackaetano',
    'followupEvent': {
      'name': 'RSR',
      'data': recommendations
    },
    'contextOut': [
      {
        'name': 'loggeduser',
        'lifespan': 10,
        'parameters': {
          'email': email,
          'id': res['_id']
        }
      }
    ]
  }

def webhook(event, context):
  print(event)

  originalRequest = event['body']['originalRequest']
  result = event['body']['result']

  if result['action'] == 'input.welcome':
    return handle_welcome(result)
  
  if result['action'] == 'hackaetano.register_user':
    return handle_register_user(result)

  if result['action'] == 'hackaetano.property_value':
    return handle_property_value(result)
  
  if result['action'] == 'hackaetano.update_familiar':
    return handle_familiar_value(result)

def get_api_user(email):
  params = {'personal.email': email}
  res = requests.get('{}/users'.format(API_ENDPOINT), params=params)
  data = res.json()

  if data['length'] == 0:
    return None

  return data['results'][0]  

def get_user_recommended_properties(user):
  if '_id' in user:
    user_id = user['_id']
  if 'id' in user:
    user_id = user['id']

  res = requests.get('{}/users/{}/matches'.format(API_ENDPOINT, user_id))
  return res.json()['results']

def get_recommendations(user):
  properties = get_user_recommended_properties(user)
  random.shuffle(properties)

  obj = {}

  for idx, _property in enumerate(properties[:9]):
    aux, i = {}, str(idx+1)    
    
    aux['title'+i] = _property['characteristics']['title']
    aux['text'+i] = _property['characteristics']['propertyType']
    
    images = _property['characteristics']['images']
    random.shuffle(images)

    aux['img'+i] = images[0]
    aux['url'+i] = 'https://vivareal.com.br' + _property['source']['url']

    obj.update(aux)

  return obj
