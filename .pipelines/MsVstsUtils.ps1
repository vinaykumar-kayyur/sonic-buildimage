# Rest api to create auto-completed PR in AzDevOps repo
$ProjectId="b32aa71e-8ed2-41b2-9d77-5bc261222004"
$RepositoryId="8721f84d-7905-4f85-b5f1-0e19e8eac66b"

# please allow script to get oauth token when use build token
$systemBasedToken="Bearer $($env:SYSTEM_ACCESSTOKEN)"
$Headers = @{
    Authorization = $systemBasedToken
}

Function Create-PullRequest(){
  param(
    [string] $sourceBranch,
    [string] $targrtBranch,
    [string] $title=""
  )

  $url="https://msazure.visualstudio.com/${ProjectId}/_apis/git/repositories/${RepositoryId}/pullrequests?api-version=5.1"
  $body=@{}
  $body.sourceRefName= "refs/heads/${sourceBranch}"
  $body.targetRefName= "refs/heads/${targrtBranch}"
  $body.title= "${title}"
  $body.description= "PR for merging ${sourceBranch} to ${targrtBranch} requested by $($env:BUILD_REQUESTEDFOR), email: $($env:BUILD_REQUESTEDFOREMAIL)"
  $bodyjson=$body | ConvertTo-Json
  try{
     $resp=Invoke-WebRequest -Uri $url -Headers $Headers -Method Post -Body $bodyjson -ContentType "application/json"
     $respJson=$resp.Content| ConvertFrom-Json
     return $respJson
  }catch [System.Net.WebException]
  {
    if ($_.Exception.Response.StatusCode -eq 200)
    {
       return $resp.StatusCode
    }
    throw  $_
  }
}

Function Get-PullRequest(){
  param(
    [string] $pullRequestId
  )

 $url="https://msazure.visualstudio.com/${ProjectId}/_apis/git/pullrequests/${pullRequestId}?api-version=5.1"
 $resp=Invoke-WebRequest -Uri $url -Headers $Headers -Method Get -ContentType "application/json"
 $respJson=$resp.Content| ConvertFrom-Json
 return $respJson
}

Function Set-PullRequestAutoComplete(){
  param(
    [string] $pullRequestId,
    [string] $autoCompleteSetById
  )

  Write-Host "Set PR $pullRequestId to auto complete by $autoCompleteSetById "
  $url="https://msazure.visualstudio.com/${ProjectId}/_apis/git/repositories/${RepositoryId}/pullrequests/${pullRequestId}?api-version=5.1"

  $body=@{}
  $body.autoCompleteSetBy=@{}
  $body.completionOptions=@{}
  $body.autoCompleteSetBy.id="$autoCompleteSetById"
  $body.completionOptions.mergeCommitMessage="Merge PR $pullRequestId"
  $body.completionOptions.bypassReason=""
  $body.completionOptions.bypassPolicy=$false
  $body.completionOptions.deleteSourceBranch=$true
  $body.completionOptions.squashMerge=$false
  $body.completionOptions.mergeStrategy=1
  $body.completionOptions.transitionWorkItems=$true
  $bodyjson=$body | ConvertTo-Json
  $respJson=$null
  try{
    $resp=Invoke-WebRequest -Uri $url -Headers $Headers -Method Patch -Body $bodyjson -ContentType "application/json"
    $respJson=$resp.Content| ConvertFrom-Json
    Write-Host "auto completed: $respJson"
  }catch [System.Net.WebException] {
    Write-Host "auto completed failed: $_"
    return $null
  }
  return $respJson
}

Function Create-MergePullRequest(){
  param(
    [string] $sourceBranch,
    [string] $targrtBranch,
    [string] $title=""
  )
  # create PR
  $resp=Create-PullRequest $sourceBranch $targrtBranch $title
  $resp | Write-Host
  Write-Host "PR :  $($resp.url) "
  
  $pullRequstId=$resp.pullRequestId
  Sleep 5
  $prResp=Get-PullRequest $pullRequstId
  $createdById=$prResp.createdBy.id
  Set-PullRequestAutoComplete $pullRequstId $createdById
}
