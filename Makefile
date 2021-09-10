
build:
	docker build -t local/labelbox-python:test .


test-local: build
	docker run -it -v ${PWD}:/usr/src -w /usr/src \
		-e LABELBOX_TEST_ENVIRON="local" \
		-e LABELBOX_TEST_API_KEY_LOCAL=${LABELBOX_TEST_API_KEY_LOCAL} \
		local/labelbox-python:test pytest $(PATH_TO_TEST) -svvx

test-staging: build
	docker run -it -v ${PWD}:/usr/src -w /usr/src \
		-e LABELBOX_TEST_ENVIRON="staging" \
		-e LABELBOX_TEST_API_KEY_STAGING=${LLT} \
		local/labelbox-python:test pytest $(PATH_TO_TEST) -svvx

test-prod: build
	docker run -it -v ${PWD}:/usr/src -w /usr/src \
		-e LABELBOX_TEST_ENVIRON="prod" \
		-e LABELBOX_TEST_API_KEY_PROD=${LABELBOX_TEST_API_KEY_PROD} \
		local/labelbox-python:test pytest $(PATH_TO_TEST) -svvx
