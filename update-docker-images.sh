#!/usr/bin/env bash

function get_latest_digest() {
    image_name="$1"
    tag="$2"
    docker pull "$image_name:$tag" | awk '/^Digest: / {print $2}'
}

function update_digest_in_file() {
    image="$1"
    digest="$2"
    file="$3"

    if [[ "$(basename "$file")" =~ ^'docker-compose'*'.yml' ]]; then
        sed -i 's/^\( *\)image: '"$image"'@.*$/\1image: '"$image@$digest"'/g' "$file"
    elif [[ "$(basename "$file")" == "Dockerfile" ]]; then
        sed -i 's/^FROM '"$image"'@.*$/FROM '"$image@$digest"'/g' "$file"
    else
        echo "Wrong file ending for '$file'"
        exit 1
    fi
}

function update_digest_in_files() {
    image="$1"
    tag="$2"
    shift 2

    digest=$(get_latest_digest "$image" "$tag")
    echo "Update digest for $image:$tag to $image@$digest"

    files="$*"
    for file in $files; do
        update_digest_in_file "$image" "$digest" "$file"
    done
}

function update_all_refs_to_latest_digest() {
    image="$1"
    tag="$2"
    update_digest_in_files "$image" "$tag" \
        admin/Dockerfile api/Dockerfile public/Dockerfile docker-compose.yml
}

update_all_refs_to_latest_digest python 3.11-alpine
update_all_refs_to_latest_digest nginx alpine
update_all_refs_to_latest_digest node 19-alpine
update_all_refs_to_latest_digest mysql 8.0.33
