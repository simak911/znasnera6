function getTeamName(){
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('tname');
}

