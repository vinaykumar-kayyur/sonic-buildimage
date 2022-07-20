#!/bin/bash -e
# github restapi tools

add_label(){
  if [ $# -ne 3 ];then
    >&2 echo "example: add_label github_token https://api.github.com/repos/<org>/<repo>/issues/<pr_id> label_1"
    exit 1
  fi
  TOKEN_LOCAL=$1
  ISSUES_URL=$(echo $2| sed 's#/$##')
  LABEL=$(echo $3 | sed 's#"#\\"#g')

  result=$(curl -X POST -H "Accept: application/vnd.github+json" \
             -H "Authorization: token ${TOKEN_LOCAL}" \
             ${ISSUES_URL}/labels \
             -d "{
                   \"labels\": [\"${LABEL}\"]
                }")
  if [[ $(expr length "$result") -eq "0" ]];then
    >&2 echo add_label Error:
    >&2 echo $(echo $result | jq )
    exit 2
  fi
}

add_comment(){
  if [ $# -ne 3 ];then
    >&2 echo "example: add_comment github_token https://api.github.com/repos/<org>/<repo>/issues/<pr_id> comment"
    exit 1
  fi
  TOKEN_LOCAL=$1
  ISSUES_URL=$(echo $2| sed 's#/$##')
  BODY=$(echo $3 | sed 's#"#\\"#g')

  result=$(curl -X POST -H "Accept: application/vnd.github+json" \
             -H "Authorization: token ${TOKEN_LOCAL}" \
             ${ISSUES_URL}/comments \
             -d "{\"body\":\"${BODY}\"}")
  if [[ "$(echo $result | jq '.errors')" != "null" ]];then
    >&2 echo add_comment Error:
    >&2 echo $result | jq '.errors'
    exit 2
  fi
}

create_pr(){
  if [ $# -ne 5 ];then
    >&2 echo "example: create_pr github_token https://api.github.com/repos/<org>/<repo> tile mssonicbld:feature-branch master"
    exit 1
  fi
  TOKEN_LOCAL=$1
  BASE_URL=$(echo $2| sed 's#/$##')
  TITLE=$(echo $3 | sed 's#"#\\"#g')
  HEAD=$(echo $4| sed 's#"#\\"#g')
  BASE=$(echo $5| sed 's#"#\\"#g')

  result=$(curl -X POST -H "Accept: application/vnd.github+json" \
             -H "Authorization: token ${TOKEN_LOCAL}" \
             ${BASE_URL}/pulls \
             -d "{
                   \"title\":\"${TITLE}\",
                   \"body\":\"\",
                   \"head\":\"${HEAD}\",
                   \"base\":\"${BASE}\"
                }")
  if [[ "$(echo $result | jq '.errors')" != "null" ]];then
    >&2 echo create_pr Error:
    >&2 echo $result | jq '.errors'
    exit 2
  fi
  echo $result
}

list_comments(){
  TOKEN_LOCAL=$1
  ISSUES_URL=$(echo $2| sed 's#/$##')
  result=$(curl -H "Accept: application/vnd.github+json" -H "Authorization: token ${TOKEN_LOCAL}"  ${ISSUES_URL}/comments)
  if [[ "$(echo $result | jq '.errors')" != "null" ]];then
    >&2 echo list_comments Error:
    >&2 echo $result | jq '.errors'
    exit 2
  fi
  echo $result
}