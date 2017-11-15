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
    if context['name'] == 'loggedUser':
      if 'id' in context['parameters']:
        user_id = context['parameters']['id']
      else:
        user_id = context['parameters']['id.original']

  if user_id is None:
    return {
      'source': 'Hackaetano',
      'followupEvent': {
        'name': 'UNKNOWN'
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

  recommendations = recommendations_by_property(data)

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

  recommendations = recommendations_by_familiar(user)

  return {
    'source': 'Hackaetano',
    'followupEvent': {
      'name': 'RSR',
      'data': recommendations
    },
    'contextOut': [
      {
        'name': 'loggedUser',
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

  print('aqui4')

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

  print('aqui5')
  print(register)

  recommendations = recommendations_by_addrs(register['address'])

  return {
    'source': 'Hackaetano',
    'followupEvent': {
      'name': 'RSR',
      'data': recommendations
    },
    'contextOut': [
      {
        'name': 'loggedUser',
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

def recommendations_by_addrs(address):
  return {
    'title1': 'Liber 1000, 32-547 m².',
    'text1': 'Descrição a definir',
    'img1': 'https://resizedimgs.vivareal.com/4TnF4eH3iJXGRyq21rfk6FOPZQM=/fit-in/685x457/vr.images.sp/7cc05eda75ee252c188b581d09878033.jpg',

    'title2': 'Liber 1000, 32-547 m².',
    'text2': 'Descrição a definir',
    'img2': 'https://resizedimgs.vivareal.com/4TnF4eH3iJXGRyq21rfk6FOPZQM=/fit-in/685x457/vr.images.sp/7cc05eda75ee252c188b581d09878033.jpg',

    'title3': 'Liber 1000, 32-547 m².',
    'text3': 'Descrição a definir',
    'img3': 'https://resizedimgs.vivareal.com/4TnF4eH3iJXGRyq21rfk6FOPZQM=/fit-in/685x457/vr.images.sp/7cc05eda75ee252c188b581d09878033.jpg',    

    'title4': 'Liber 1000, 32-547 m².',
    'text4': 'Descrição a definir',
    'img4': 'https://resizedimgs.vivareal.com/4TnF4eH3iJXGRyq21rfk6FOPZQM=/fit-in/685x457/vr.images.sp/7cc05eda75ee252c188b581d09878033.jpg'
  }

def recommendations_by_property(property):
  return {
    'title1': 'Liber 1000, 32-547 m².',
    'text1': 'Descrição a definir',
    'img1': 'https://resizedimgs.vivareal.com/4TnF4eH3iJXGRyq21rfk6FOPZQM=/fit-in/685x457/vr.images.sp/7cc05eda75ee252c188b581d09878033.jpg',

    'title2': 'Liber 1000, 32-547 m².',
    'text2': 'Descrição a definir',
    'img2': 'https://resizedimgs.vivareal.com/4TnF4eH3iJXGRyq21rfk6FOPZQM=/fit-in/685x457/vr.images.sp/7cc05eda75ee252c188b581d09878033.jpg',

    'title3': 'Liber 1000, 32-547 m².',
    'text3': 'Descrição a definir',
    'img3': 'https://resizedimgs.vivareal.com/4TnF4eH3iJXGRyq21rfk6FOPZQM=/fit-in/685x457/vr.images.sp/7cc05eda75ee252c188b581d09878033.jpg',    

    'title4': 'Liber 1000, 32-547 m².',
    'text4': 'Descrição a definir',
    'img4': 'https://resizedimgs.vivareal.com/4TnF4eH3iJXGRyq21rfk6FOPZQM=/fit-in/685x457/vr.images.sp/7cc05eda75ee252c188b581d09878033.jpg'
  }

def recommendations_by_familiar(user):
  return {
    'title1': 'Liber 1000, 32-547 m².',
    'text1': 'Descrição a definir',
    'img1': 'https://resizedimgs.vivareal.com/4TnF4eH3iJXGRyq21rfk6FOPZQM=/fit-in/685x457/vr.images.sp/7cc05eda75ee252c188b581d09878033.jpg',

    'title2': 'Liber 1000, 32-547 m².',
    'text2': 'Descrição a definir',
    'img2': 'https://resizedimgs.vivareal.com/4TnF4eH3iJXGRyq21rfk6FOPZQM=/fit-in/685x457/vr.images.sp/7cc05eda75ee252c188b581d09878033.jpg',

    'title3': 'Liber 1000, 32-547 m².',
    'text3': 'Descrição a definir',
    'img3': 'https://resizedimgs.vivareal.com/4TnF4eH3iJXGRyq21rfk6FOPZQM=/fit-in/685x457/vr.images.sp/7cc05eda75ee252c188b581d09878033.jpg',    

    'title4': 'Liber 1000, 32-547 m².',
    'text4': 'Descrição a definir',
    'img4': 'https://resizedimgs.vivareal.com/4TnF4eH3iJXGRyq21rfk6FOPZQM=/fit-in/685x457/vr.images.sp/7cc05eda75ee252c188b581d09878033.jpg'
  }
