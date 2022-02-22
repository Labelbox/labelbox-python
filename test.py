import labelbox
from labelbox.data.annotation_types import (Label, VideoData,
                                            VideoObjectAnnotation, Rectangle,
                                            Point, Radio,
                                            VideoClassificationAnnotation,
                                            ClassificationAnswer, Checklist)
from labelbox import (LabelingFrontend, Client, OntologyBuilder, Tool,
                      Classification, Option)
from labelbox.data.serialization import NDJsonConverter

# Add your api key
# API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiJja25xM2JpbmQweHRlMDg1NHhreTFmaXJwIiwib3JnYW5pemF0aW9uSWQiOiJja25xM2JpbXc2aW5wMDc4NHRhbjlwamUzIiwiYXBpS2V5SWQiOiJja3plM3FtaG1hcTJsMHo1eWZndzc4bDNtIiwic2VjcmV0IjoiNTk5ZDk2MWFiZjUyNjg2ZDU5ODY4ODY1OWM5MTRhN2MiLCJpYXQiOjE2NDQzMjM0NzEsImV4cCI6MjI3NTQ3NTQ3MX0.XvuEMbLA3Hr_QFG_g8OIunJdsv_5MGAvo0WKyzvUdxg"
import os

os.system('clear')

API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiJja2NjOWZtbXc0aGNkMDczOHFpeWM2YW54Iiwib3JnYW5pemF0aW9uSWQiOiJja2N6NmJ1YnVkeWZpMDg1NW8xZHQxZzlzIiwiYXBpS2V5SWQiOiJja2V2cDF2enAwdDg0MDc1N3I2ZWZldGgzIiwiaWF0IjoxNTk5Njc0NzY0LCJleHAiOjIyMzA4MjY3NjR9.iyqPpEWNpfcjcTid5WVkXLi51g22e_l3FrK-DlFJ2mM"
client = Client(api_key=API_KEY)

project = client.get_project("ckz38nsfd0lzq109bhq73est1")

#these come out in Labelbox common format
video_labels = project.video_label_generator()

#convert back from Labelbox common format to ndjson format
back_to_regular_labels = NDJsonConverter.serialize(video_labels)

print(len(list(back_to_regular_labels)))