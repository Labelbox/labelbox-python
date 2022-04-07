
build:
	docker build -t local/labelbox-python:test .


test-local: build
	docker run -it -v ${PWD}:/usr/src -w /usr/src \
		-e LABELBOX_TEST_ENVIRON="local" \
		-e LABELBOX_TEST_API_KEY_LOCAL=${LABELBOX_TEST_API_KEY_LOCAL} \
		local/labelbox-python:test pytest $(PATH_TO_TEST) 

test-staging: build
	docker run -it -v ${PWD}:/usr/src -w /usr/src \
		-e LABELBOX_TEST_ENVIRON="staging" \
		-e LABELBOX_TEST_API_KEY_STAGING=${LABELBOX_TEST_API_KEY_STAGING} \
		local/labelbox-python:test pytest $(PATH_TO_TEST) 

test-prod: build
	docker run -it -v ${PWD}:/usr/src -w /usr/src \
		-e LABELBOX_TEST_ENVIRON="prod" \
		-e LABELBOX_TEST_API_KEY_PROD=${LABELBOX_TEST_API_KEY_PROD} \
		local/labelbox-python:test pytest $(PATH_TO_TEST)

test-onprem: build
	docker run -it -v ${PWD}:/usr/src -w /usr/src \
		-e LABELBOX_TEST_ENVIRON="onprem" \
		-e LABELBOX_TEST_API_KEY_ONPREM=${LABELBOX_TEST_API_KEY_ONPREM} \
		-e LABELBOX_TEST_ONPREM_INSTANCE=${LABELBOX_TEST_ONPREM_INSTANCE} \
		local/labelbox-python:test pytest $(PATH_TO_TEST) 
