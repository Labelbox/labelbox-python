
build:
	docker build -t local/labelbox-python:test .

test-staging: build
	docker run -it -v ${PWD}:/usr/src -w /usr/src \
		-e LABELBOX_TEST_ENVIRON="staging" \
		-e LABELBOX_TEST_API_KEY_STAGING="<REPLACE>" \
		local/labelbox-python:test pytest $(PATH_TO_TEST) -svvx

test-prod: build
	docker run -it -v ${PWD}:/usr/src -w /usr/src \
		-e LABELBOX_TEST_ENVIRON="prod" \
		-e LABELBOX_TEST_API_KEY_PROD="<REPLACE>" \
		local/labelbox-python:test pytest $(PATH_TO_TEST) -svvx
