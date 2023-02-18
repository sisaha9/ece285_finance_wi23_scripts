build-docker:
	docker build -f Dockerfile -t ece285_finance_wi23 .

run-container:
	@CONT_NAME="${CONT_NAME}"
	rocker --network host --git --ssh --x11 --privileged --name ${CONT_NAME} --user --volume ${shell pwd} -- ece285_finance_wi23

join-session:
	@CONT_NAME="${CONT_NAME}"
	docker exec -it ${CONT_NAME} /bin/bash

reformat:
	autoflake --in-place --remove-unused-variables --remove-all-unused-imports --ignore-init-module-imports -r ${PATHS}
	black -l 99 ${PATHS}

clean:
	@rm -rf results/ results.zip