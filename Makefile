
build-image:
	docker build --quiet -t local/labelbox-python:test .

test-local: build-image

	@# if PATH_TO_TEST we assume you know what you are doing
	@if [ -z ${PATH_TO_TEST} ]; then \
		./scripts/ensure_local_setup.sh; \
	fi

	docker run -it --rm -v ${PWD}:/usr/src -w /usr/src \
		-e LABELBOX_TEST_ENVIRON="local" \
		-e DA_GCP_LABELBOX_API_KEY=${DA_GCP_LABELBOX_API_KEY} \
		-e LABELBOX_TEST_API_KEY_LOCAL=${LABELBOX_TEST_API_KEY_LOCAL} \
		-e FIXTURE_PROFILE=true \
		local/labelbox-python:test pytest $(PATH_TO_TEST)

test-staging: build-image
	docker run -it --rm -v ${PWD}:/usr/src -w /usr/src \
		-e LABELBOX_TEST_ENVIRON="staging" \
		-e DA_GCP_LABELBOX_API_KEY=${DA_GCP_LABELBOX_API_KEY} \
		-e LABELBOX_TEST_API_KEY_STAGING=${LABELBOX_TEST_API_KEY_STAGING} \
		local/labelbox-python:test pytest $(PATH_TO_TEST)

test-staging-eu: build-image
	docker run -it --rm -v ${PWD}:/usr/src -w /usr/src \
		-e LABELBOX_TEST_ENVIRON="staging-eu" \
		-e DA_GCP_LABELBOX_API_KEY=${DA_GCP_LABELBOX_API_KEY} \
		-e LABELBOX_TEST_API_KEY_STAGING_EU=${LABELBOX_TEST_API_KEY_STAGING_EU} \
		local/labelbox-python:test pytest $(PATH_TO_TEST)

test-prod: build-image
	docker run -it --rm -v ${PWD}:/usr/src -w /usr/src \
		-e LABELBOX_TEST_ENVIRON="prod" \
		-e DA_GCP_LABELBOX_API_KEY=${DA_GCP_LABELBOX_API_KEY} \
		-e LABELBOX_TEST_API_KEY_PROD=${LABELBOX_TEST_API_KEY_PROD} \
		local/labelbox-python:test pytest $(PATH_TO_TEST)

test-onprem: build-image
	docker run -it --rm -v ${PWD}:/usr/src -w /usr/src \
		-e LABELBOX_TEST_ENVIRON="onprem" \
		-e DA_GCP_LABELBOX_API_KEY=${DA_GCP_LABELBOX_API_KEY} \
		-e LABELBOX_TEST_API_KEY_ONPREM=${LABELBOX_TEST_API_KEY_ONPREM} \
		-e LABELBOX_TEST_ONPREM_HOSTNAME=${LABELBOX_TEST_ONPREM_HOSTNAME} \
		local/labelbox-python:test pytest $(PATH_TO_TEST)

test-dev0: build-image
	docker run -it --rm -v ${PWD}:/usr/src -w /usr/src \
		-e LABELBOX_TEST_ENVIRON="custom" \
		-e DA_GCP_LABELBOX_API_KEY=${DA_GCP_LABELBOX_API_KEY} \
		-e LABELBOX_TEST_API_KEY_CUSTOM=${LABELBOX_TEST_API_KEY_CUSTOM} \
		-e LABELBOX_TEST_GRAPHQL_API_ENDPOINT="https://api.dev0.na-us.lb-dev.xyz/graphql" \
		-e LABELBOX_TEST_REST_API_ENDPOINT="https://api.dev0.na-us.lb-dev.xyz/api/v1" \
		local/labelbox-python:test pytest $(PATH_TO_TEST)

test-custom: build-image
	docker run -it --rm -v ${PWD}:/usr/src -w /usr/src \
		-e LABELBOX_TEST_ENVIRON="custom" \
		-e DA_GCP_LABELBOX_API_KEY=${DA_GCP_LABELBOX_API_KEY} \
		-e LABELBOX_TEST_API_KEY_CUSTOM=${LABELBOX_TEST_API_KEY_CUSTOM} \
		-e LABELBOX_TEST_GRAPHQL_API_ENDPOINT=${LABELBOX_TEST_GRAPHQL_API_ENDPOINT} \
		-e LABELBOX_TEST_REST_API_ENDPOINT=${LABELBOX_TEST_REST_API_ENDPOINT} \
		local/labelbox-python:test pytest $(PATH_TO_TEST)

test-ephemeral: build-image

	@# if PATH_TO_TEST we assume you know what you are doing
	@if [ -z ${PATH_TO_TEST} ]; then \
		./scripts/ensure_local_setup.sh; \
	fi

	docker run -it --rm -v ${PWD}:/usr/src -w /usr/src \
		-e LABELBOX_TEST_ENVIRON="ephemeral" \
		-e DA_GCP_LABELBOX_API_KEY=${DA_GCP_LABELBOX_API_KEY} \
		-e SERVICE_API_KEY=${SERVICE_API_KEY} \
		-e LABELBOX_TEST_BASE_URL="http://host.docker.internal:8080" \
		local/labelbox-python:test pytest $(PATH_TO_TEST)
