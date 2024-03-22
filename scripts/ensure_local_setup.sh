#!/usr/bin/env bash

print_invalid_setup() {
  echo "Local setup: INVALID"
  echo -e 'Learn how to: https://labelbox.atlassian.net/wiki/spaces/AIENG/pages/1946910734/How+To+Test+Local+Changes+using+Python+SDK#Running-SDK-test-automation-locally'
}

# intelligence API
curl -I http://localhost:8080 1>/dev/null 2>&1

if [ $? -ne 0 ]; then
  print_invalid_setup

  echo -e '\x1b[41;37mYou need to run intelligence api first\x1b[K\x1b[0m';
  exit 1
fi

# prediction import
prediction_import_service=$(lsof -i :50051 | grep LISTEN | wc -l)

if [ $prediction_import_service -eq 0 ]; then
  print_invalid_setup

  echo -e '\x1b[41;37mYou need to run prediction import service first\x1b[K\x1b[0m';
  exit 1
fi

# label consumer service
label_consumer_service=$(lsof -i :8100 | grep LISTEN | wc -l)

if [ $label_consumer_service -eq 0 ]; then
  print_invalid_setup

  echo -e '\x1b[41;37mYou need to run label consumer service first: \x1b[K\x1b[0m';
  echo -e '# from intelligence root'
  echo -e 'docker-compose -f docker-compose.lcs.yml up -d lcs-sync label-consumer-service'
  exit 1
fi

echo "Local setup: VALID"
