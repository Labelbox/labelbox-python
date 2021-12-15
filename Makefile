
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
		-e LABELBOX_TEST_API_KEY_STAGING=${LABELBOX_TEST_API_KEY_STAGING} \
		local/labelbox-python:test pytest $(PATH_TO_TEST) -svvx

test-prod: build
	docker run -it -v ${PWD}:/usr/src -w /usr/src \
		-e LABELBOX_TEST_ENVIRON="prod" \
		-e LABELBOX_TEST_API_KEY_PROD=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiJja2NjOWZtbXc0aGNkMDczOHFpeWM2YW54Iiwib3JnYW5pemF0aW9uSWQiOiJja2N6NmJ1YnVkeWZpMDg1NW8xZHQxZzlzIiwiYXBpS2V5SWQiOiJja3g3dnJ0dWtiZG5iMHo5djlsb2lheHdyIiwic2VjcmV0IjoiNzM5NjJmMmExZDNiMGZjOTNjYjQ2ZDc0YTYyOTQwNzYiLCJpYXQiOjE2Mzk1OTM3MjgsImV4cCI6MjI3MDc0NTcyOH0.ccJXRNVIh0cmtr8hq9Lh36LlTJ2kN1rVFyJuqh2Mn70 \
		local/labelbox-python:test pytest $(PATH_TO_TEST) -svvx
