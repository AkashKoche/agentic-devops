#!/bin/bash

docker run -it --rm \
	-p 4040:4040 \
	--add-host=host.docker.internal:host-gateway \
	--env-file .env \
	ngrok/ngrok:latest http host.docker.internal:8000
