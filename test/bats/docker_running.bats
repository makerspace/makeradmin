@test "Docker containers are running" {
  # Print out status of containers
  docker_container_ids=`docker ps -q`
  number_of_running_containers=`echo -n $docker_container_ids | sed 's/ /\n/g' | wc -l`
  [ $number_of_running_containers -ne 0 ]
  echo $docker_container_ids |
  while read docker_id; do
    status=`docker inspect -f {{.State.Status}} $docker_id`;
  done
}

@test "Web sites are contactable" {
  # Check that services can be contacted
  for port in 8009; do
    http_code=$(curl --head -w %{http_code} localhost:$port -o /dev/null)
    [ "$http_code" -eq "200" ]
  done
}
