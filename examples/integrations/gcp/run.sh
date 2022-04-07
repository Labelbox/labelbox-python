set -e

docker-compose build
docker-compose push
docker-compose up deployment_config
docker-compose up -d coordinator
docker-compose logs --follow coordinator
