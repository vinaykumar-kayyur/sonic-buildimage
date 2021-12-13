param(
    [Parameter(Mandatory=$false)]
    [string] $PersonalAccessToken=""
)
# Rest api to create auto-completed PR in AzDevOps repo
$ProjectId="b32aa71e-8ed2-41b2-9d77-5bc261222004"
$RepositoryId="8721f84d-7905-4f85-b5f1-0e19e8eac66b"

# please allow script to get oauth token when use build token
$systemBasedToken="Bearer $($env:SYSTEM_ACCESSTOKEN)"
$Headers = @{
    Authorization = $systemBasedToken
}

# set personal token when you run it in local env
if(![string]::IsNullOrWhiteSpace($PersonalAccessToken)){
    $pat =[string]::Format("{0}:{1}", "", $PersonalAccessToken)
    $EncodedPat = [System.Convert]::ToBase64String([System.Text.Encoding]::ASCII.GetBytes($pat))
    $basicAuthValue = "Basic $EncodedPat"
    $Headers = @{
        Authorization = $basicAuthValue
    }
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

Function Find-PullRequestID-ByBranch(){
    param(
        [string] $targrtBranch="internal"
    )
    $url="https://dev.azure.com/msazure/${ProjectId}/_apis/git/repositories/${RepositoryId}/pullrequests?api-version=5.1"
    $resp=Invoke-WebRequest -Uri $url -Headers $Headers -Method Get -ContentType "application/json"
    $respJson= $resp.Content | ConvertFrom-Json
    For ($i=0; $i -lt $respJson.value.Length; $i++) {
        if($respJson.value[$i].title -ne "Code sync from github" -or $respJson.value[$i].targetRefName -ne "refs/heads/${targrtBranch}" -or $respJson.value[$i].createdBy.id -ne "36efc182-8b61-450f-86ee-748b553252a9"){
            continue
        }
        return $respJson.value[$i].pullRequestId
    }
    return -1
}

Function Get-PullRequest(){
    param(
        [string] $pullRequestId
    )

    $url="https://msazure.visualstudio.com/${ProjectId}/_apis/git/pullrequests/${pullRequestId}?api-version=5.1"
    $resp=Invoke-WebRequest -Uri $url -Headers $Headers -Method Get -ContentType "application/json"
    if($resp -like '*Azure DevOps Services | Sign In*') {
        throw "Authorization failed. Please check PersonalAccessToken or SYSTEM_ACCESSTOKEN"
    }
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
    $prID=Find-PullRequestID-ByBranch $targrtBranch
    if ($prID -eq -1){
        # create PR
        $resp=Create-PullRequest $sourceBranch $targrtBranch $title
        $resp | Write-Host
        Write-Host "PR :  $($resp.url) "
        
        $pullRequestId=$resp.pullRequestId
        Sleep 5
        $prResp=Get-PullRequest $pullRequestId
        $createdById=$prResp.createdBy.id
        Set-PullRequestAutoComplete $pullRequestId $createdById
        return $pullRequestId
    } else{
        Write-Host PR already exist: https://msazure.visualstudio.com/One/_git/Networking-acs-buildimage/pullrequest/$prID
        return $prID
    }
}
