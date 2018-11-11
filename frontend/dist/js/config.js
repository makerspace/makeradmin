// NOTE: This file is only used in devel mode, docker_entrypoint.sh overwrites it.

var config = {
    apiBasePath: "http://" + window.location.hostname + ":8010",
	apiVersion: "1.0",
	pagination: {
		pageSize: 25,
	},
}
