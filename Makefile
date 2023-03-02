
build:
	docker build -t local/labelbox-python:test .


test-local: build

	@# if PATH_TO_TEST we asuume you know what you are doing
	@if [ -z ${PATH_TO_TEST} ]; then \
		./scripts/ensure_local_setup.sh; \
	fi

	docker run -it -v ${PWD}:/usr/src -w /usr/src \
		-e LABELBOX_TEST_ENVIRON="local" \
		-e DA_GCP_LABELBOX_API_KEY=${DA_GCP_LABELBOX_API_KEY} \
		-e LABELBOX_TEST_API_KEY_LOCAL=${LABELBOX_TEST_API_KEY_LOCAL} \
		local/labelbox-python:test pytest $(PATH_TO_TEST)

test-staging: build
	docker run -it -v ${PWD}:/usr/src -w /usr/src \
		-e LABELBOX_TEST_ENVIRON="staging" \
		-e DA_GCP_LABELBOX_API_KEY=${DA_GCP_LABELBOX_API_KEY} \
		-e LABELBOX_TEST_API_KEY_STAGING=${LABELBOX_TEST_API_KEY_STAGING} \
		local/labelbox-python:test pytest -n 10 $(PATH_TO_TEST)

test-prod: build
	docker run -it -v ${PWD}:/usr/src -w /usr/src \
		-e LABELBOX_TEST_ENVIRON="prod" \
		-e DA_GCP_LABELBOX_API_KEY=${DA_GCP_LABELBOX_API_KEY} \
		-e LABELBOX_TEST_API_KEY_PROD=${LABELBOX_TEST_API_KEY_PROD} \
		local/labelbox-python:test pytest $(PATH_TO_TEST)

test-onprem: build
	docker run -it -v ${PWD}:/usr/src -w /usr/src \
		-e LABELBOX_TEST_ENVIRON="onprem" \
		-e DA_GCP_LABELBOX_API_KEY=${DA_GCP_LABELBOX_API_KEY} \
		-e LABELBOX_TEST_API_KEY_ONPREM=${LABELBOX_TEST_API_KEY_ONPREM} \
		-e LABELBOX_TEST_ONPREM_HOSTNAME=${LABELBOX_TEST_ONPREM_HOSTNAME} \
		local/labelbox-python:test pytest $(PATH_TO_TEST)

test-custom: build
	docker run -it -v ${PWD}:/usr/src -w /usr/src \
		-e LABELBOX_TEST_ENVIRON="custom" \
		-e DA_GCP_LABELBOX_API_KEY=${DA_GCP_LABELBOX_API_KEY} \
		-e LABELBOX_TEST_API_KEY_CUSTOM=${LABELBOX_TEST_API_KEY_CUSTOM} \
		-e LABELBOX_TEST_GRAPHQL_API_ENDPOINT=${LABELBOX_TEST_GRAPHQL_API_ENDPOINT} \
		-e LABELBOX_TEST_REST_API_ENDPOINT=${LABELBOX_TEST_REST_API_ENDPOINT} \
		local/labelbox-python:test pytest $(PATH_TO_TEST)
