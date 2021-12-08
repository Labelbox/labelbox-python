from labelbox import Client

api_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiJja21jY3gwaDYwMDRnMDk2NThieXh5NHZ0Iiwib3JnYW5pemF0aW9uSWQiOiJja21jY3gwZnQwMDRhMDk2NW5tYWx0azZhIiwicmVhZE9ubHkiOmZhbHNlLCJpYXQiOjE2Mzg4Mjc4MzQsImV4cCI6MTYzOTQzMjYzNH0.HQxOHjsa4B8leftQVXtMAlrs3xVTb3SgGMX5xjneUtI'
client = Client(api_key=api_key, endpoint='http://localhost:8080/_gql')

def handle_event(event):
  if event.get('type') == 'project.created':
    print(f"A project named {event['resource']['name']} was just creatd by {event['actor']['email']}")

client.subscribe(handle_event)