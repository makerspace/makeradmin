# Download the source code and build a docker container
git clone https://github.com/MakersOfSweden/MakerAdmin-Frontend
cd ./MakerAdmin-Frontend/
./docker/docker_build

# Run the Docker container
./docker/docker_run

# TODO: Download node_modules

# Start webpack in watch mode
./webpack_watch

# You should now have a web server up and running on the IP address allocated by Docker
